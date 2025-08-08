import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain.agents import Tool, initialize_agent
from langchain_neo4j import Neo4jGraph
from neo4j import GraphDatabase

load_dotenv()



try:
    driver = GraphDatabase.driver(
        os.environ.get("NEO4J_URI"),
        auth=(os.environ.get("NEO4J_USERNAME"), os.environ.get("NEO4J_PASSWORD"))
    )

    driver.verify_connectivity()
    print("Neo4j connection successful")
    
    graph = Neo4jGraph(
        url=os.environ.get("NEO4J_URI"),
        username=os.environ.get("NEO4J_USERNAME"),
        password=os.environ.get("NEO4J_PASSWORD"),
        timeout=30  
    )
    

    llm = ChatAnthropic(
        model="claude-3-5-haiku-latest",
        temperature=0.3,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_tokens=4000
    )
    
    print("LLM initialized successfully")

except Exception as e:
    print(f"Setup failed: {e}")
    raise

def create_road_network_tools():

    def find_connected_links(link_id: str, levels: int = 2) -> str:
        with driver.session() as session:
            query = f"""
            MATCH (start:Link {{link_id: $link_id}})-[:CONNECTED_TO*1..{levels}]-(neighbor:Link)
            RETURN start.link_id as start_link, neighbor.link_id as connected_link, 
                   neighbor.meters as distance
            LIMIT 50
            """
            result = session.run(query, link_id=link_id)
            return str([dict(record) for record in result])

    def find_nearby_vms(link_id: str) -> str:
        with driver.session() as session:
            query = """
            MATCH path = (l:Link {link_id: $link_id})-[:CONNECTED_TO*0..2]-(connected:Link)<-[:LOCATED_AT]-(v:VMS)
            WITH v, connected, l, path, length(path) as hops,
                CASE 
                WHEN length(path) = 0 THEN 0
                ELSE reduce(total = 0, node IN nodes(path)[0..-1] | 
                            total + coalesce(node.meters, 0))
                END as cumulative_distance
            
            // Determine direction based on path relationships  
            WITH v, connected, l, cumulative_distance, hops,
                CASE 
                WHEN hops = 0 THEN 'same_link'
                WHEN hops = 1 THEN 'adjacent'
                WHEN hops = 2 THEN 'nearby'
                ELSE 'distant'
                END as proximity,
                relationships(path) as rels
            
            // Simple upstream/downstream logic
            WITH v, connected, l, cumulative_distance, hops, proximity,
                CASE 
                WHEN hops = 0 THEN 'same_link'
                WHEN hops > 0 AND size(rels) > 0 THEN
                    CASE 
                    WHEN startNode(rels[0]) = l THEN 'downstream'
                    WHEN endNode(rels[0]) = l THEN 'upstream'
                    ELSE 'cross_connection'
                    END
                ELSE 'unknown'
                END as direction
            
            RETURN v.EQT_NO as vms_id, 
                v.ROAD_NAME as road, 
                connected.link_id as vms_link,
                cumulative_distance as distance_meters,
                hops as links_away,
                direction,
                proximity
            ORDER BY cumulative_distance, hops
            LIMIT 20
            """
            result = session.run(query, link_id=link_id)
            return str([dict(record) for record in result])
        
    def find_nearby_events(link_id: str) -> str:
        with driver.session() as session:
            query = """
            MATCH (l:Link {link_id: $link_id})-[:CONNECTED_TO*0..2]-(connected:Link)
            MATCH (connected)<-[:START_AT|END_AT]-(e:event_record)
            RETURN e.id as event_id, e.ROAD_NAME as road, connected.link_id as link
            LIMIT 20
            """
            result = session.run(query, link_id=link_id)
            return str([dict(record) for record in result])
        
    def find_connected_plan(event_id: str) -> str:
        with driver.session() as session:
            query = """
            MATCH (e:event_record {id: $event_id})-[:HAS_PLAN]->(ep:event_plan)
            RETURN e.id as event_id,
                e.road_name as event_road,
                ep.id as plan_id,
                ep.plan_status as plan_status,
                ep.created_date as plan_created_date,
                ep.start_time as plan_start_time,
                ep.end_time as plan_end_time
            ORDER BY ep.created_date DESC
            LIMIT 20
            """
            result = session.run(query, event_id=int(event_id))
            return str([dict(record) for record in result])
    
    def find_connected_plan_command(plan_id: str) -> str:
        with driver.session() as session:
            query = """
            MATCH (ep:event_plan {id: $plan_id})-[:HAS_COMMAND]->(epc:event_plan_command)
            RETURN ep.id as plan_id,
                ep.plan_status as plan_status,
                epc.id as command_id,
                epc.msgDesc1 as command_description_1,
                epc.msgDesc2 as command_description_2,
                epc.cmd_status as command_status,
                epc.created_date as command_created_date,
                epc.eqt_site_id as equipment_id
            ORDER BY epc.created_date DESC
            LIMIT 50
            """
            result = session.run(query, plan_id=int(plan_id))
            return str([dict(record) for record in result])


    def run_cypher_query(query: str) -> str:
        try:
            with driver.session() as session:
                result = session.run(query)
                records = [dict(record) for record in result]
                return str(records[:50])
        except Exception as e:
            return f"Query error: {str(e)}"

    def generate_smart_response_plan(context: str) -> str:
        
        prompt = f"""
        Based on the following traffic incident information, generate a comprehensive response plan:
        
        Context: {context}
        
        RESPONSE PLAN FORMAT:
        Please generate a response plan in the following JSON format:

        {{
            "plan_type": "Traffic Management Plan",
            "priority": "High/Medium/Low",
            "estimated_duration": "X minutes/hours",
            "traffic_management_actions": [
                            {{
                    "eqt_no": "VMS_EQUIPMENT_ID",
                    "message_line_1": "Primary message text",
                    "message_line_2": "Secondary message text (if needed)",
                    "display_duration": "X minutes",
                    "justification": "Why this VMS and message"
                }},

                {{
                    "action": "Specific action to take",
                    "location": "Where to implement",
                    "resources_needed": "What resources are required",
                    "timing": "When to implement"
                }}
            ],
            
            "justification": "Detailed explanation of why this plan is appropriate"
        }}

        Generate a practical, actionable response plan considering the event severity, available VMS systems, and traffic management best practices.
        """
        
        try:
            response = llm.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Error generating smart response plan: {str(e)}"

    def find_affected_area_comprehensive(link_ids_input):
        """
        Find affected links using multiple pathfinding strategies.
        Input: link_ids_input (string or list) - Can be "[17840003591931, 17840001783588]" or actual list
        Returns: List of affected link IDs using fallback methods if direct path not found.
        """
        
        # Handle different input formats
        if isinstance(link_ids_input, str):
            # Try to parse string representation of list
            import ast
            import json
            try:
                # Try literal_eval first
                link_ids = ast.literal_eval(link_ids_input)
            except:
                try:
                    # Try JSON parsing
                    link_ids = json.loads(link_ids_input)
                except:
                    try:
                        # Try comma-separated values
                        link_ids = [x.strip() for x in link_ids_input.split(',')]
                    except:
                        return "Error: Could not parse link_ids input format"
        else:
            link_ids = link_ids_input
        
        # Validate we have exactly 2 link IDs
        if not isinstance(link_ids, list) or len(link_ids) < 2:
            return "Error: Need exactly 2 link IDs - upstream and downstream"
        
        up_link_id = str(link_ids[0])
        dn_link_id = str(link_ids[1])
        
        with driver.session() as session:
            query = """
            MATCH (start_link:Link {link_id: $up_link_id})
            MATCH (end_link:Link {link_id: $dn_link_id})
            
            // Method 1: Direct shortest path
            OPTIONAL MATCH path1 = shortestPath((start_link)-[:CONNECTED_TO*]-(end_link))
            WITH start_link, end_link, 
                CASE WHEN path1 IS NOT NULL 
                    THEN [node IN nodes(path1) | node.link_id] 
                    ELSE [] END as direct_path
            
            // Method 2: If no direct path, find links within reasonable distance of both start and end
            OPTIONAL MATCH (start_link)-[:CONNECTED_TO*1..3]-(intermediate:Link)-[:CONNECTED_TO*1..3]-(end_link)
            WITH start_link, end_link, direct_path,
                CASE WHEN size(direct_path) > 0 
                    THEN direct_path 
                    ELSE collect(DISTINCT intermediate.link_id)[0..10] END as affected_links
            
            // Method 3: If still no path, use links near start and end
            WITH start_link, end_link, 
                CASE WHEN size(affected_links) > 0 
                    THEN affected_links 
                    ELSE [start_link.link_id, end_link.link_id] END as final_affected_links
            
            RETURN $up_link_id as up_link_id,
                $dn_link_id as dn_link_id,
                final_affected_links as affected_links
            """
            
            result = session.run(query, up_link_id=up_link_id, dn_link_id=dn_link_id)
            return str([dict(record) for record in result])

    return [
        Tool(
            name="FindConnectedLinks",
            func=find_connected_links,
            description="Use this to find road links connected to a given link within specified levels"
        ),
        Tool(
            name="FindNearbyVMS", 
            func=find_nearby_vms,
            description="""Find VMS (Variable Message Signs) near a specific road link.
            Input: link_id (string) - The road link identifier to search around.
            Returns: List of nearby VMS with equipment IDs, distances, and directions."""
        ),
        Tool(
            name="CypherQuery",
            func=run_cypher_query,
            description="Execute Cypher queries on the Neo4j graph database. Use this for general graph queries."
        ),
        Tool(
            name="FindEventRecord",
            func=find_nearby_events,
            description="""Find Event Records near a specific road link.
            Input: link_id (string) - The road link identifier to search around.
            Returns: List of events with event IDs, roads, and associated links."""
        ),
        Tool(
            name="FindEventPlan",
            func=find_connected_plan,
            description="""Find the Event Plans connected to the event record
            Input: event_id (string) - The id of the event_record.
            Returns: list of Event plans with their details that were used for the event, 
            """
        ),
        Tool(
            name="FindPlanCommands",
            func=find_connected_plan_command,
            description="""Find the Event Plan Commands used by a specific event plan
            Input: plan_id (string) the id of the event plan.
            Returns: The information of the Event plan command"""
        ),
        Tool(
            name="GenerateSmartResponsePlan",
            func=generate_smart_response_plan,
            description="""Generate intelligent response plan using incident context.
            Input: context (string) - Comprehensive context including incident details, VMS data importantly the id, event with their respective plan and plan command history to provide context.
            Returns: the explicit JSON formatted response plan with actions and VMS commands not the summary."""
        ),
        Tool(
            name="FindAffectedAreaComprehensive",
            func=find_affected_area_comprehensive,
            description="""Find affected links using multiple pathfinding strategies.
            Input: link_ids (string) - Two link IDs as "[upstream_link_id, downstream_link_id]" or "upstream_link_id, downstream_link_id"
            Returns: List of affected link IDs using fallback methods if direct path not found."""
        ),
    ]


class RoadNetworkChatBot:
    def __init__(self):
        self.chat_history = []
        self.road_tools = create_road_network_tools()

        system_prompt = """
        You are a traffic incident management expert.
        Main objective is to reduce the congestion in the area quickly
        Use the available tools to help with traffic management.
        """

        self.agent = initialize_agent(
            tools=self.road_tools,
            llm=llm,
            agent="chat-conversational-react-description",
            verbose=True,
            max_iterations=6,
            return_intermediate_steps=True,
            agent_kwargs={
                "system_message": system_prompt
            }

        )
    
    def query(self, question: str):
        try:
            response = self.agent.invoke({
                "input": question,
                "chat_history": self.chat_history
            })
            
            self.chat_history.extend([
                ("human", question),
                ("ai", response.get("output", ""))
            ])
            
            return response.get("output", str(response))
        except Exception as e:
            return f"Error: {e}"
    
    def clear_history(self):
        self.chat_history = []
    
    def get_history(self):
        return self.chat_history

chatbot = RoadNetworkChatBot()

class SessionAwareChatBot(RoadNetworkChatBot):
    def __init__(self):
        super().__init__()
        self.current_link = None
        self.current_road = None
    
    def set_link(self, link_id: str):
        self.current_link = link_id
        return f"✅ Working with link: {link_id}"
    
    def query(self, question: str):
        if self.current_link and ("this link" in question.lower() or "that link" in question.lower()):
            question = question.replace("this link", self.current_link)
            question = question.replace("that link", self.current_link)
        
        return super().query(question)

session_chatbot = SessionAwareChatBot()


# # Step 2: Generate response plan
# response2 = enhanced_session_chatbot.query("Generate an intelligent response plan for this situation")
# print("Response Plan:", response2)
# response = session_chatbot.query("affected links : 	17840001587376 to 17840001763559, event_severity: high, queue_length: 2000 meters,lane_blockage: 2 of 3 lanes, event_type: accident,time_of_day: 0800,weather_conditions: clear,expected_duration: 45,road_type: highway,traffic_volume: high,incident_description: Multi-vehicle accident blocking 2 lanes during morning rush hour generate a smart response plan from this information based on context gathered from exploring similar events and around the area of the event")
# print("Response Plan:", response)


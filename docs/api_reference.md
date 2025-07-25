# API Reference

## Core Classes

### RoadNetworkChatBot

The main interface for interacting with the traffic management system.

```python
from src.agents.traffic_agent import RoadNetworkChatBot

chatbot = RoadNetworkChatBot(verbose=True)
result = chatbot.query("Traffic incident on link 17840006094278...")
```

#### Methods

##### `query(question: str, run_name: str = None) -> str`

Process a traffic management query with human-in-the-loop approval.

**Parameters:**
- `question`: Traffic incident description
- `run_name`: Optional name for tracking the run

**Returns:** String response with generated plan or processing status

##### `stream_query(question: str, run_name: str = None) -> Iterator`

Stream the workflow execution for real-time monitoring.

**Parameters:**
- `question`: Traffic incident description  
- `run_name`: Optional name for tracking the run

**Returns:** Iterator yielding workflow chunks

## Tools

### Neo4j Tools

#### `run_cypher_query(query: str) -> str`

Execute Cypher queries against the road network database.

#### `get_schema() -> str`

Retrieve the database schema information.

### Event Tools

#### `extract_event_data(event_description: str) -> str`

Extract structured data from natural language incident descriptions.

#### `analyze_event_changes(event_data: str, previous_data: str = None) -> str`

Analyze changes to determine if response plan updates are needed.

### Plan Tools

#### `generate_response_plan(context: str) -> str`

Generate psychology-based VMS response plans.

### Storage Tools

#### `store_event_details(event_data: str, graph_schema: str) -> str`

Store event information in the Neo4j database.

#### `store_event_plan(response_plan: str, event_id: str, graph_schema: str) -> str`

Store response plans and link them to events.

## Configuration

### Settings

Configure the system through environment variables:

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# Anthropic API
ANTHROPIC_API_KEY=your_api_key

# LangSmith (Optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
```

### Database Connection

```python
from config.database import get_neo4j_driver, get_neo4j_graph

# Get driver for direct queries
driver = get_neo4j_driver()

# Get LangChain graph for tools
graph = get_neo4j_graph()
```

### LLM Configuration

```python
from config.llm import get_llm

llm = get_llm()
response = llm.invoke("Your prompt here")
```

## Monitoring

### Performance Tracking

```python
from monitoring.performance_metrics import performance_monitor

# Start timing an operation
timer_id = performance_monitor.start_timer("query_processing")

# ... do work ...

# End timing and record metric
duration = performance_monitor.end_timer(timer_id)

# Get performance summary
summary = performance_monitor.get_metrics_summary("query_processing")
```

### LangSmith Integration

```python
from monitoring.langsmith_tracker import langsmith_tracker

# Track a query
langsmith_tracker.track_query(
    query="Traffic incident...",
    result="Response plan generated",
    metadata={"severity": "high", "duration": 12.5}
)
```

## Error Handling

### Custom Error Handler

```python
from src.utils.error_handlers import custom_parsing_error_handler

try:
    # LLM operation that might fail
    result = llm.invoke(prompt)
except Exception as e:
    formatted_error = custom_parsing_error_handler(e)
    print(formatted_error)
```

### Validation

```python
from src.utils.validators import validate_event_data, validate_response_plan

# Validate event data
try:
    validated_data = validate_event_data(event_json_string)
except ValueError as e:
    print(f"Validation failed: {e}")
```

## Data Models

### TrafficEvent

```python
from src.core.schemas import TrafficEvent

event = TrafficEvent(
    event_id="12345",
    link_id="17840006094278",
    incident_type="accident",
    severity="high",
    blocked_lanes=["left", "center"],
    queue_length=1500
)
```

### ResponsePlan

```python
from src.core.schemas import ResponsePlan, VMSAction

action = VMSAction(
    eqt_no="VMS001",
    message_line_1="ACCIDENT AHEAD",
    message_line_2="SLOW DOWN",
    display_duration="30 minutes",
    distance="500 meters",
    psychological_rationale="Creates urgency without panic",
    behavioral_goal="Reduce speed",
    urgency_level="High",
    reasoning="Close proximity requires immediate action"
)
```

## Examples

### Basic Usage

```python
from src.agents.traffic_agent import RoadNetworkChatBot

# Initialize
chatbot = RoadNetworkChatBot()

# Process incident
incident = """
Multi-vehicle accident on link 17840006094278 at 08:45.
Two lanes blocked, queue 750m. High severity.
"""

result = chatbot.query(incident)
print(result)
```

### Streaming Workflow

```python
for chunk in chatbot.stream_query(incident):
    for node, output in chunk.items():
        print(f"Node: {node}")
        if "messages" in output:
            for msg in output["messages"]:
                if hasattr(msg, 'content'):
                    print(f"Output: {msg.content}")
```

### Direct Tool Usage

```python
from src.tools.neo4j_tools import run_cypher_query
from src.tools.event_tools import extract_event_data

# Extract event data
event_data = extract_event_data.func("Accident on Highway 101...")

# Query database
vms_data = run_cypher_query.func("""
MATCH (v:VMS)-[:LOCATED_AT]->(l:Link {link_id: '17840006094278'})
RETURN v.EQT_NO, v.ROAD_NAME
""")
```

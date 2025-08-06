"""Setup script to initialize connections like in the notebook."""

import os
from dotenv import load_dotenv

def setup_connections():
    """Setup Neo4j and Anthropic connections like in the notebook."""
    
    print("🔧 SETTING UP CONNECTIONS")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    print("✅ Environment variables loaded")
    
    try:
        # Test Neo4j connection
        from neo4j import GraphDatabase
        
        print("\n🗄️ Testing Neo4j connection...")
        driver = GraphDatabase.driver(
            os.environ.get("NEO4J_URI"),
            auth=(os.environ.get("NEO4J_USERNAME"), os.environ.get("NEO4J_PASSWORD"))
        )
        
        driver.verify_connectivity()
        print("✅ Neo4j connection successful")
        
        # Test Neo4j Graph
        from langchain_neo4j import Neo4jGraph
        
        graph = Neo4jGraph(
            url=os.environ.get("NEO4J_URI"),
            username=os.environ.get("NEO4J_USERNAME"),
            password=os.environ.get("NEO4J_PASSWORD"),
            timeout=30  
        )
        
        try:
            schema = graph.get_schema
            print("✅ Schema cached successfully")
            print(f"📊 Schema preview: {str(schema)[:200]}...")
        except Exception as schema_error:
            print(f"⚠️ Could not cache schema: {schema_error}")
            
        driver.close()
        
        # Test LLM connection
        print("\n🤖 Testing Anthropic LLM...")
        from langchain_anthropic import ChatAnthropic
        
        llm = ChatAnthropic(
            model="claude-3-5-haiku-latest",
            temperature=0.3,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=4000
        )
        
        # Test with a simple query
        response = llm.invoke("Hello, can you confirm you're working?")
        print("✅ LLM initialized successfully")
        print(f"💬 LLM test response: {response.content[:100]}...")
        
        # Test LangSmith (optional)
        print("\n📊 Testing LangSmith...")
        try:
            from langsmith import Client
            langsmith_client = Client()
            print("✅ LangSmith client initialized successfully")
        except Exception as ls_error:
            print(f"⚠️ LangSmith warning: {ls_error}")
            print("💡 LangSmith is optional - system can run without it")
        
        print("\n🎉 All connections setup successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        print("\n💡 Check your .env file contains:")
        print("  - NEO4J_URI")
        print("  - NEO4J_USERNAME") 
        print("  - NEO4J_PASSWORD")
        print("  - ANTHROPIC_API_KEY")
        print("  - LANGCHAIN_API_KEY (optional)")
        return False

def check_environment():
    """Check if all required environment variables are set."""
    
    print("🔍 CHECKING ENVIRONMENT")
    print("=" * 50)
    
    required_vars = [
        "NEO4J_URI",
        "NEO4J_USERNAME", 
        "NEO4J_PASSWORD",
        "ANTHROPIC_API_KEY"
    ]
    
    optional_vars = [
        "LANGCHAIN_API_KEY",
        "LANGCHAIN_PROJECT",
        "LANGCHAIN_TRACING_V2"
    ]
    
    missing_required = []
    missing_optional = []
    
    # Check required variables
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * min(len(value), 10)}...")
        else:
            print(f"❌ {var}: Not set")
            missing_required.append(var)
    
    # Check optional variables
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"🔵 {var}: {'*' * min(len(value), 10)}... (optional)")
        else:
            print(f"⚪ {var}: Not set (optional)")
            missing_optional.append(var)
    
    if missing_required:
        print(f"\n❌ Missing required variables: {missing_required}")
        return False
    else:
        print(f"\n✅ All required environment variables are set!")
        if missing_optional:
            print(f"💡 Optional variables not set: {missing_optional}")
        return True

def setup_database():
    """Setup database like in the notebook."""
    
    print("\n🗄️ SETTING UP DATABASE")
    print("=" * 50)
    
    try:
        # Initialize the workflow tools setup
        from src.tools.workflow_tools import setup_connections
        setup_connections()
        
        print("✅ Database setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 TRAFFIC MANAGEMENT SYSTEM SETUP")
    print("=" * 80)
    
    # Check environment first
    env_ok = check_environment()
    
    if not env_ok:
        print("\n❌ Environment check failed!")
        print("💡 Please set up your .env file with the required variables")
        exit(1)
    
    # Setup connections
    connections_ok = setup_connections()
    
    if not connections_ok:
        print("\n❌ Connection setup failed!")
        exit(1)
    
    # Setup database
    db_ok = setup_database()
    
    if db_ok:
        print("\n🎉 SETUP COMPLETE!")
        print("✅ Your system is ready to use")
        print("🚀 Run 'python main.py' to start the traffic management system")
    else:
        print("\n❌ Setup incomplete - check errors above")

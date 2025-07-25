"""Setup script for initializing the Neo4j database schema."""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import get_neo4j_driver
from config.settings import settings

def create_schema():
    """Create the necessary schema in Neo4j database."""
    
    schema_queries = [
        # Create constraints
        "CREATE CONSTRAINT link_id_unique IF NOT EXISTS FOR (l:Link) REQUIRE l.link_id IS UNIQUE",
        "CREATE CONSTRAINT vms_eqt_no_unique IF NOT EXISTS FOR (v:VMS) REQUIRE v.EQT_NO IS UNIQUE", 
        "CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (e:Event) REQUIRE e.event_id IS UNIQUE",
        
        # Create indexes
        "CREATE INDEX link_from_junction IF NOT EXISTS FOR (l:Link) ON (l.from_junction)",
        "CREATE INDEX link_to_junction IF NOT EXISTS FOR (l:Link) ON (l.to_junction)",
        "CREATE INDEX vms_link_id IF NOT EXISTS FOR (v:VMS) ON (v.LINK_ID)",
        "CREATE INDEX event_link_id IF NOT EXISTS FOR (e:Event) ON (e.link_id)",
        
        # Create sample data if needed
        """
        MERGE (l1:Link {link_id: '17840006094278', from_junction: 'J001', to_junction: 'J002', meters: '500'})
        MERGE (l2:Link {link_id: '17840006094277', from_junction: 'J002', to_junction: 'J003', meters: '800'})
        MERGE (l1)-[:CONNECTED_TO]->(l2)
        MERGE (l2)-[:CONNECTED_TO]->(l1)
        """,
        
        """
        MERGE (v1:VMS {
            EQT_NO: 'VMS001', 
            EQT_EXT_ID: 'VMS001_EXT',
            ROAD_NAME: 'Main Highway',
            LATITUDE: 25.123456,
            LONGITUDE: 55.987654,
            LINK_ID: 17840006094278
        })
        """
    ]
    
    driver = get_neo4j_driver()
    
    try:
        with driver.session() as session:
            for query in schema_queries:
                if query.strip():  # Skip empty queries
                    try:
                        session.run(query)
                        print(f"✅ Executed: {query[:50]}...")
                    except Exception as e:
                        print(f"⚠️ Warning for query {query[:50]}...: {e}")
        
        print("✅ Database schema setup completed successfully!")
        
    except Exception as e:
        print(f"❌ Schema setup failed: {e}")
        return False
    
    finally:
        driver.close()
    
    return True

def test_connection():
    """Test database connectivity."""
    try:
        driver = get_neo4j_driver()
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            if record and record["test"] == 1:
                print("✅ Database connection successful!")
                return True
            else:
                print("❌ Database connection test failed!")
                return False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    finally:
        driver.close()

if __name__ == "__main__":
    print("🚀 Setting up Neo4j database...")
    print(f"Connecting to: {settings.NEO4J_URI}")
    
    # Validate settings
    try:
        settings.validate()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Test connection first
    if not test_connection():
        sys.exit(1)
    
    # Create schema
    if create_schema():
        print("🎉 Database setup completed successfully!")
    else:
        print("❌ Database setup failed!")
        sys.exit(1)

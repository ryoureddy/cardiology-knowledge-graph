"""
Initialize Neo4j database with a cardiology-specific schema.
"""
import logging
from pathlib import Path
import sys

# Add the project root to the path to import modules correctly
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.database.database_connector import connector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_cardiology_schema():
    """
    Initialize Neo4j database with cardiology-specific schema.
    
    Returns:
        bool: True if schema initialization was successful, False otherwise
    """
    try:
        # Connect to Neo4j
        graph = connector.get_connection()
        
        # Clear existing data (uncomment with caution)
        logger.info("Clearing existing data...")
        graph.run("MATCH (n) DETACH DELETE n")
        
        # Create constraints for unique nodes
        logger.info("Creating constraints...")
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Condition) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Treatment) REQUIRE t.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Mechanism) REQUIRE m.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (f:Finding) REQUIRE f.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Diagnostic) REQUIRE d.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Procedure) REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Anatomy) REQUIRE a.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Source) REQUIRE s.id IS UNIQUE"
        ]
        
        # Create indexes for better performance
        logger.info("Creating indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS FOR (c:Condition) ON (c.name)",
            "CREATE INDEX IF NOT EXISTS FOR (t:Treatment) ON (t.name)",
            "CREATE INDEX IF NOT EXISTS FOR (m:Mechanism) ON (m.name)",
            "CREATE INDEX IF NOT EXISTS FOR (f:Finding) ON (f.name)",
            "CREATE INDEX IF NOT EXISTS FOR (d:Diagnostic) ON (d.name)",
            "CREATE INDEX IF NOT EXISTS FOR (p:Procedure) ON (p.name)",
            "CREATE INDEX IF NOT EXISTS FOR (a:Anatomy) ON (a.name)",
            "CREATE INDEX IF NOT EXISTS FOR (s:Source) ON (s.id)",
            "CREATE INDEX IF NOT EXISTS FOR (s:Source) ON (s.type)"
        ]
        
        # Execute all constraints and indexes
        for constraint in constraints:
            graph.run(constraint)
        
        for index in indexes:
            graph.run(index)
        
        # Add root nodes for cardiology taxonomy
        logger.info("Creating root nodes for cardiology taxonomy...")
        graph.run("""
        CREATE (root:Root {name: 'Cardiology Knowledge Graph'})
        CREATE (conditions:Category {name: 'Cardiac Conditions'})
        CREATE (anatomy:Category {name: 'Cardiac Anatomy'})
        CREATE (procedures:Category {name: 'Cardiac Procedures'})
        CREATE (diagnostics:Category {name: 'Cardiac Diagnostics'})
        CREATE (treatments:Category {name: 'Cardiac Treatments'})
        CREATE (mechanisms:Category {name: 'Cardiac Mechanisms'})
        CREATE (findings:Category {name: 'Cardiac Findings'})
        
        CREATE (root)-[:CONTAINS]->(conditions)
        CREATE (root)-[:CONTAINS]->(anatomy)
        CREATE (root)-[:CONTAINS]->(procedures)
        CREATE (root)-[:CONTAINS]->(diagnostics)
        CREATE (root)-[:CONTAINS]->(treatments)
        CREATE (root)-[:CONTAINS]->(mechanisms)
        CREATE (root)-[:CONTAINS]->(findings)
        """)
        
        # Create some example relationships between entity types
        logger.info("Creating relationship schemas...")
        graph.run("""
        CREATE (relSchema:RelationshipSchema {name: 'Relationship Schema'})
        
        CREATE (condToAnat:RelationType {name: 'AFFECTS', description: 'A condition affects an anatomical structure'})
        CREATE (condToMech:RelationType {name: 'INVOLVES', description: 'A condition involves a mechanism'})
        CREATE (treatToCond:RelationType {name: 'TREATS', description: 'A treatment addresses a condition'})
        CREATE (diagToCond:RelationType {name: 'DIAGNOSES', description: 'A diagnostic procedure diagnoses a condition'})
        CREATE (findToCond:RelationType {name: 'INDICATES', description: 'A finding indicates a condition'})
        CREATE (procToAnat:RelationType {name: 'PERFORMED_ON', description: 'A procedure is performed on an anatomical structure'})
        CREATE (anatToAnat:RelationType {name: 'CONNECTED_TO', description: 'An anatomical structure is connected to another'})
        CREATE (mechToMech:RelationType {name: 'LEADS_TO', description: 'A mechanism leads to another mechanism'})
        
        CREATE (relSchema)-[:DEFINES]->(condToAnat)
        CREATE (relSchema)-[:DEFINES]->(condToMech)
        CREATE (relSchema)-[:DEFINES]->(treatToCond)
        CREATE (relSchema)-[:DEFINES]->(diagToCond)
        CREATE (relSchema)-[:DEFINES]->(findToCond)
        CREATE (relSchema)-[:DEFINES]->(procToAnat)
        CREATE (relSchema)-[:DEFINES]->(anatToAnat)
        CREATE (relSchema)-[:DEFINES]->(mechToMech)
        """)
        
        logger.info("Cardiology schema initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing schema: {str(e)}")
        return False

if __name__ == "__main__":
    if initialize_cardiology_schema():
        logger.info("Schema initialization complete")
    else:
        logger.error("Schema initialization failed")
        sys.exit(1) 
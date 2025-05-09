"""
Database connector module for Neo4j connection management.
"""
from py2neo import Graph
import logging
import os
from pathlib import Path
import sys
from dotenv import load_dotenv

# Add the project root to the path to import modules correctly
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Load environment variables from .env file
load_dotenv(os.path.join(project_root, '.env'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Neo4jConnector:
    """
    Manages connections to the Neo4j database for the Cardiology Knowledge Graph.
    """
    
    def __init__(self, uri=None, user=None, password=None):
        """
        Initialize the Neo4j database connector.
        
        Args:
            uri (str): Neo4j connection URI
            user (str): Neo4j username
            password (str): Neo4j password
        """
        # Get connection details from environment variables if not provided
        self.uri = uri or os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.environ.get("NEO4J_USER", "neo4j")
        self.password = password or os.environ.get("NEO4J_PASSWORD", "password")
        self.graph = None
        
    def connect(self):
        """
        Establish connection to the Neo4j database.
        
        Returns:
            Graph: A py2neo Graph object representing the connected database
        """
        try:
            self.graph = Graph(self.uri, auth=(self.user, self.password))
            logger.info("Successfully connected to Neo4j database")
            return self.graph
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j database: {str(e)}")
            raise
            
    def get_connection(self):
        """
        Get the current database connection, or create a new one if none exists.
        
        Returns:
            Graph: A py2neo Graph object representing the connected database
        """
        if self.graph is None:
            return self.connect()
        return self.graph
        
    def close(self):
        """
        Close the database connection.
        """
        # py2neo doesn't require explicit connection closing,
        # but we'll keep this method for future extensions or cleanup
        self.graph = None
        logger.info("Database connection closed")
        
    def test_connection(self):
        """
        Test the database connection by running a simple query.
        
        Returns:
            bool: True if connection is working, False otherwise
        """
        try:
            # Try to execute a simple Cypher query
            result = self.get_connection().run("RETURN 1 AS test")
            # Consume the result
            value = result.evaluate()
            return value == 1
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False


# Singleton instance for global use
connector = Neo4jConnector() 
"""
Module for building the knowledge graph in Neo4j from extracted entities and relationships.
"""
import logging
import os
import json
from pathlib import Path
import sys
from tqdm import tqdm

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

class KnowledgeGraphBuilder:
    """Class to build the cardiology knowledge graph in Neo4j."""
    
    def __init__(self):
        """
        Initialize the knowledge graph builder.
        """
        self.graph = connector.get_connection()
        self.entity_count = 0
        self.relationship_count = 0
        self.source_count = 0
    
    def create_source_node(self, article_data):
        """
        Create a source node in the graph for an article.
        
        Args:
            article_data (dict): Article metadata
            
        Returns:
            str: Source node ID
        """
        # Generate a source ID based on the article data
        source_id = article_data.get('id', article_data.get('pmid', str(hash(json.dumps(article_data)))))
        
        # Prepare source properties
        source_type = article_data.get('source_type', 'unknown')
        
        properties = {
            'id': source_id,
            'type': source_type,
            'title': article_data.get('title', 'Untitled'),
            'url': article_data.get('url', '')
        }
        
        # Add source-specific properties
        if source_type == 'pubmed':
            properties.update({
                'journal': article_data.get('journal', ''),
                'publication_date': article_data.get('publication_date', ''),
                'pmid': article_data.get('pmid', '')
            })
        
        # Create the source node if it doesn't exist
        query = """
        MERGE (s:Source {id: $id})
        ON CREATE SET s.type = $type, 
                      s.title = $title, 
                      s.url = $url
        """
        
        # Add additional properties for PubMed sources
        if source_type == 'pubmed':
            query += ", s.journal = $journal, s.publication_date = $publication_date, s.pmid = $pmid"
        
        self.graph.run(query, **properties)
        
        return source_id
    
    def create_entity_node(self, entity, source_id):
        """
        Create an entity node in the graph.
        
        Args:
            entity (dict): Entity data
            source_id (str): ID of the source node
            
        Returns:
            tuple: (entity_text, entity_type)
        """
        entity_text = entity['text']
        entity_type = entity['type']
        
        # Create the entity node if it doesn't exist
        query = f"""
        MERGE (e:{entity_type} {{name: $name}})
        ON CREATE SET e.frequency = 1
        ON MATCH SET e.frequency = e.frequency + 1
        
        WITH e
        
        MATCH (s:Source {{id: $source_id}})
        MERGE (e)-[r:MENTIONED_IN]->(s)
        ON CREATE SET r.count = 1
        ON MATCH SET r.count = r.count + 1
        
        RETURN e.name, e.frequency
        """
        
        result = self.graph.run(query, name=entity_text, source_id=source_id).data()
        
        # Connect to appropriate category node
        category_query = f"""
        MATCH (e:{entity_type} {{name: $name}})
        MATCH (c:Category {{name: 'Cardiac {entity_type}s'}})
        MERGE (c)-[:CONTAINS]->(e)
        """
        
        self.graph.run(category_query, name=entity_text)
        
        return (entity_text, entity_type)
    
    def create_relationship_edge(self, relationship, source_id):
        """
        Create a relationship edge between entities in the graph.
        
        Args:
            relationship (dict): Relationship data
            source_id (str): ID of the source node
            
        Returns:
            bool: True if successful, False otherwise
        """
        subject = relationship['subject']
        subject_type = relationship['subject_type']
        object_entity = relationship['object']
        object_type = relationship['object_type']
        rel_type = relationship['relationship']
        confidence = relationship.get('confidence', 0.5)
        
        # Create the relationship with evidence
        query = f"""
        MATCH (subj:{subject_type} {{name: $subject}})
        MATCH (obj:{object_type} {{name: $object}})
        MATCH (s:Source {{id: $source_id}})
        
        MERGE (subj)-[r:{rel_type}]->(obj)
        ON CREATE SET r.count = 1, 
                      r.confidence = $confidence,
                      r.evidence_count = 1
        ON MATCH SET r.count = r.count + 1,
                     r.confidence = (r.confidence * r.evidence_count + $confidence) / (r.evidence_count + 1),
                     r.evidence_count = r.evidence_count + 1
        
        MERGE (r)-[e:EVIDENCE]->(s)
        ON CREATE SET e.context = $context
        
        RETURN subj.name, type(r), obj.name
        """
        
        try:
            result = self.graph.run(
                query,
                subject=subject,
                object=object_entity,
                source_id=source_id,
                confidence=confidence,
                context=relationship.get('context', '')
            ).data()
            
            return len(result) > 0
            
        except Exception as e:
            logger.error(f"Error creating relationship: {str(e)}")
            return False
    
    def build_graph_from_results(self, relationship_results_path):
        """
        Build the knowledge graph from relationship extraction results.
        
        Args:
            relationship_results_path (str): Path to the relationship extraction results
            
        Returns:
            tuple: (entity_count, relationship_count, source_count)
        """
        relationship_results_path = os.path.join(project_root, relationship_results_path)
        
        if not os.path.exists(relationship_results_path):
            logger.error(f"Results file not found: {relationship_results_path}")
            return 0, 0, 0
        
        try:
            # Load relationship extraction results
            with open(relationship_results_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            if not results:
                logger.warning("Results file is empty")
                return 0, 0, 0
            
            # Track metrics
            self.entity_count = 0
            self.relationship_count = 0
            self.source_count = 0
            
            # Process each article's data
            for article_id, data in tqdm(results.items(), desc="Building knowledge graph"):
                # Create source node
                source_id = self.create_source_node(data['article_data'])
                self.source_count += 1
                
                # Create entity nodes
                entities = {}
                for entity in data['entities']:
                    entity_key = self.create_entity_node(entity, source_id)
                    entities[entity_key] = True
                
                self.entity_count += len(entities)
                
                # Create relationship edges
                for relationship in data['relationships']:
                    success = self.create_relationship_edge(relationship, source_id)
                    if success:
                        self.relationship_count += 1
            
            logger.info(f"Knowledge graph built successfully with {self.entity_count} entities, "
                        f"{self.relationship_count} relationships, and {self.source_count} sources")
            
            return self.entity_count, self.relationship_count, self.source_count
            
        except Exception as e:
            logger.error(f"Error building knowledge graph: {str(e)}")
            return 0, 0, 0
    
    def add_dual_process_properties(self):
        """
        Add properties to relationships for dual process theory views.
        
        Returns:
            int: Number of relationships updated
        """
        # System 1 properties are based on high frequency/confidence
        system1_query = """
        MATCH ()-[r]->()
        WHERE type(r) <> 'CONTAINS' AND type(r) <> 'EVIDENCE' AND type(r) <> 'MENTIONED_IN'
        SET r.system1_strength = CASE
            WHEN r.count > 5 AND r.confidence > 0.7 THEN 'high'
            WHEN r.count > 2 AND r.confidence > 0.5 THEN 'medium'
            ELSE 'low'
        END
        RETURN count(r) as updated
        """
        
        # System 2 properties are set initially based on evidence count
        system2_query = """
        MATCH ()-[r]->()
        WHERE type(r) <> 'CONTAINS' AND type(r) <> 'EVIDENCE' AND type(r) <> 'MENTIONED_IN'
        SET r.system2_relevance = CASE
            WHEN r.evidence_count > 3 THEN 'high'
            WHEN r.evidence_count > 1 THEN 'medium'
            ELSE 'low'
        END
        RETURN count(r) as updated
        """
        
        # Run the queries
        result1 = self.graph.run(system1_query).data()
        result2 = self.graph.run(system2_query).data()
        
        # Get the counts
        count1 = result1[0]['updated'] if result1 else 0
        count2 = result2[0]['updated'] if result2 else 0
        
        logger.info(f"Added dual process properties to {count1} relationships (System 1)")
        logger.info(f"Added dual process properties to {count2} relationships (System 2)")
        
        return max(count1, count2)

# Example usage
if __name__ == "__main__":
    builder = KnowledgeGraphBuilder()
    builder.build_graph_from_results("data/processed/extracted_relationships.json")
    builder.add_dual_process_properties() 
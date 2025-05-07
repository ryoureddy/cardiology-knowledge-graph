"""
Module for generating dual process theory views of the cardiology knowledge graph.
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

class DualProcessViews:
    """Class to generate dual process theory views of the knowledge graph."""
    
    def __init__(self):
        """Initialize the dual process views generator."""
        self.graph = connector.get_connection()
    
    def generate_system1_view(self, entity_name, entity_type=None, limit=50):
        """
        Generate System 1 (intuitive) view centered on a specific entity.
        
        System 1 view focuses on high-frequency, high-confidence relationships
        that represent common associations medical students should learn.
        
        Args:
            entity_name (str): Name of the central entity
            entity_type (str, optional): Type of the entity (if known)
            limit (int): Maximum number of relationships to include
            
        Returns:
            dict: System 1 view data
        """
        # Construct the type constraint if provided
        type_constraint = ""
        if entity_type:
            type_constraint = f"AND n:{entity_type}"
        
        # Query to get System 1 relationships
        query = f"""
        MATCH (n {{name: $entity_name}}){type_constraint}
        OPTIONAL MATCH (n)-[r]->(target) 
        WHERE type(r) <> 'MENTIONED_IN' AND type(r) <> 'EVIDENCE'
        AND (r.system1_strength = 'high' OR r.system1_strength = 'medium')
        
        WITH n, r, target
        ORDER BY r.count DESC, r.confidence DESC
        LIMIT {limit}
        
        RETURN n.name as source_name, 
               labels(n)[0] as source_type,
               type(r) as relationship,
               r.count as relationship_count,
               r.confidence as relationship_confidence,
               r.system1_strength as relationship_strength,
               target.name as target_name,
               labels(target)[0] as target_type
        
        UNION
        
        MATCH (n {{name: $entity_name}}){type_constraint}
        OPTIONAL MATCH (source)-[r]->(n)
        WHERE type(r) <> 'MENTIONED_IN' AND type(r) <> 'EVIDENCE'
        AND (r.system1_strength = 'high' OR r.system1_strength = 'medium')
        
        WITH n, r, source
        ORDER BY r.count DESC, r.confidence DESC
        LIMIT {limit}
        
        RETURN source.name as source_name,
               labels(source)[0] as source_type,
               type(r) as relationship,
               r.count as relationship_count,
               r.confidence as relationship_confidence,
               r.system1_strength as relationship_strength,
               n.name as target_name,
               labels(n)[0] as target_type
        """
        
        results = self.graph.run(query, entity_name=entity_name).data()
        
        # Format the results
        nodes = {}
        links = []
        
        for row in results:
            if not row['relationship']:
                continue
                
            # Add source node if not already in nodes
            if row['source_name'] not in nodes:
                nodes[row['source_name']] = {
                    'id': row['source_name'],
                    'label': row['source_name'],
                    'type': row['source_type'],
                    'group': row['source_type'],
                }
            
            # Add target node if not already in nodes
            if row['target_name'] not in nodes:
                nodes[row['target_name']] = {
                    'id': row['target_name'],
                    'label': row['target_name'],
                    'type': row['target_type'],
                    'group': row['target_type'],
                }
            
            # Add the link
            links.append({
                'source': row['source_name'],
                'target': row['target_name'],
                'label': row['relationship'],
                'type': row['relationship'],
                'value': row['relationship_count'] or 1,
                'strength': row['relationship_strength'] or 'low',
                'confidence': row['relationship_confidence'] or 0.5,
            })
        
        # Convert nodes dict to list
        nodes_list = list(nodes.values())
        
        # Mark the central node
        for node in nodes_list:
            if node['id'] == entity_name:
                node['central'] = True
                node['value'] = 20  # Make central node larger
            else:
                node['central'] = False
                node['value'] = 10
        
        # Create the view
        view = {
            'viewType': 'system1',
            'centralEntity': entity_name,
            'entityType': entity_type,
            'nodes': nodes_list,
            'links': links,
            'description': f"System 1 (Intuitive) view centered on {entity_name} showing {len(links)} high-confidence relationships."
        }
        
        return view
    
    def generate_system2_view(self, entity_name, entity_type=None, limit=50):
        """
        Generate System 2 (analytical) view centered on a specific entity.
        
        System 2 view includes less common but still important relationships
        that represent deeper analytical understanding.
        
        Args:
            entity_name (str): Name of the central entity
            entity_type (str, optional): Type of the entity (if known)
            limit (int): Maximum number of relationships to include
            
        Returns:
            dict: System 2 view data
        """
        # Construct the type constraint if provided
        type_constraint = ""
        if entity_type:
            type_constraint = f"AND n:{entity_type}"
        
        # Query to get System 2 relationships
        query = f"""
        MATCH (n {{name: $entity_name}}){type_constraint}
        OPTIONAL MATCH (n)-[r]->(target)
        WHERE type(r) <> 'MENTIONED_IN' AND type(r) <> 'EVIDENCE'
        
        WITH n, r, target
        ORDER BY r.system2_relevance DESC, r.evidence_count DESC
        LIMIT {limit}
        
        RETURN n.name as source_name,
               labels(n)[0] as source_type,
               type(r) as relationship,
               r.count as relationship_count,
               r.evidence_count as evidence_count,
               r.system2_relevance as relationship_relevance,
               target.name as target_name,
               labels(target)[0] as target_type
        
        UNION
        
        MATCH (n {{name: $entity_name}}){type_constraint}
        OPTIONAL MATCH (source)-[r]->(n)
        WHERE type(r) <> 'MENTIONED_IN' AND type(r) <> 'EVIDENCE'
        
        WITH n, r, source
        ORDER BY r.system2_relevance DESC, r.evidence_count DESC
        LIMIT {limit}
        
        RETURN source.name as source_name,
               labels(source)[0] as source_type,
               type(r) as relationship,
               r.count as relationship_count,
               r.evidence_count as evidence_count,
               r.system2_relevance as relationship_relevance,
               n.name as target_name,
               labels(n)[0] as target_type
        """
        
        results = self.graph.run(query, entity_name=entity_name).data()
        
        # Format the results
        nodes = {}
        links = []
        
        for row in results:
            if not row['relationship']:
                continue
                
            # Add source node if not already in nodes
            if row['source_name'] not in nodes:
                nodes[row['source_name']] = {
                    'id': row['source_name'],
                    'label': row['source_name'],
                    'type': row['source_type'],
                    'group': row['source_type'],
                }
            
            # Add target node if not already in nodes
            if row['target_name'] not in nodes:
                nodes[row['target_name']] = {
                    'id': row['target_name'],
                    'label': row['target_name'],
                    'type': row['target_type'],
                    'group': row['target_type'],
                }
            
            # Add the link
            links.append({
                'source': row['source_name'],
                'target': row['target_name'],
                'label': row['relationship'],
                'type': row['relationship'],
                'value': row['relationship_count'] or 1,
                'relevance': row['relationship_relevance'] or 'low',
                'evidence_count': row['evidence_count'] or 1,
            })
        
        # Convert nodes dict to list
        nodes_list = list(nodes.values())
        
        # Mark the central node
        for node in nodes_list:
            if node['id'] == entity_name:
                node['central'] = True
                node['value'] = 20  # Make central node larger
            else:
                node['central'] = False
                node['value'] = 10
        
        # Create the view
        view = {
            'viewType': 'system2',
            'centralEntity': entity_name,
            'entityType': entity_type,
            'nodes': nodes_list,
            'links': links,
            'description': f"System 2 (Analytical) view centered on {entity_name} showing {len(links)} relationships."
        }
        
        return view
    
    def generate_complete_view(self, entity_name, entity_type=None, limit=100):
        """
        Generate complete view centered on a specific entity.
        
        Complete view includes all relationships but uses visual cues to distinguish
        System 1 from System 2 relationships.
        
        Args:
            entity_name (str): Name of the central entity
            entity_type (str, optional): Type of the entity (if known)
            limit (int): Maximum number of relationships to include
            
        Returns:
            dict: Complete view data
        """
        # Construct the type constraint if provided
        type_constraint = ""
        if entity_type:
            type_constraint = f"AND n:{entity_type}"
        
        # Query to get all relevant relationships
        query = f"""
        MATCH (n {{name: $entity_name}}){type_constraint}
        OPTIONAL MATCH (n)-[r]->(target)
        WHERE type(r) <> 'MENTIONED_IN' AND type(r) <> 'EVIDENCE'
        
        WITH n, r, target
        ORDER BY r.count DESC
        LIMIT {limit}
        
        RETURN n.name as source_name,
               labels(n)[0] as source_type,
               type(r) as relationship,
               r.count as relationship_count,
               r.confidence as relationship_confidence,
               r.system1_strength as system1_strength,
               r.system2_relevance as system2_relevance,
               target.name as target_name,
               labels(target)[0] as target_type
        
        UNION
        
        MATCH (n {{name: $entity_name}}){type_constraint}
        OPTIONAL MATCH (source)-[r]->(n)
        WHERE type(r) <> 'MENTIONED_IN' AND type(r) <> 'EVIDENCE'
        
        WITH n, r, source
        ORDER BY r.count DESC
        LIMIT {limit}
        
        RETURN source.name as source_name,
               labels(source)[0] as source_type,
               type(r) as relationship,
               r.count as relationship_count,
               r.confidence as relationship_confidence,
               r.system1_strength as system1_strength,
               r.system2_relevance as system2_relevance,
               n.name as target_name,
               labels(n)[0] as target_type
        """
        
        results = self.graph.run(query, entity_name=entity_name).data()
        
        # Format the results
        nodes = {}
        links = []
        
        for row in results:
            if not row['relationship']:
                continue
                
            # Add source node if not already in nodes
            if row['source_name'] not in nodes:
                nodes[row['source_name']] = {
                    'id': row['source_name'],
                    'label': row['source_name'],
                    'type': row['source_type'],
                    'group': row['source_type'],
                }
            
            # Add target node if not already in nodes
            if row['target_name'] not in nodes:
                nodes[row['target_name']] = {
                    'id': row['target_name'],
                    'label': row['target_name'],
                    'type': row['target_type'],
                    'group': row['target_type'],
                }
            
            # Determine view attributes
            is_system1 = row['system1_strength'] in ['high', 'medium']
            is_system2 = row['system2_relevance'] in ['high', 'medium']
            
            # Add the link
            links.append({
                'source': row['source_name'],
                'target': row['target_name'],
                'label': row['relationship'],
                'type': row['relationship'],
                'value': row['relationship_count'] or 1,
                'system1': is_system1,
                'system2': is_system2,
                'system1_strength': row['system1_strength'] or 'low',
                'system2_relevance': row['system2_relevance'] or 'low',
                'confidence': row['relationship_confidence'] or 0.5,
            })
        
        # Convert nodes dict to list
        nodes_list = list(nodes.values())
        
        # Mark the central node
        for node in nodes_list:
            if node['id'] == entity_name:
                node['central'] = True
                node['value'] = 20  # Make central node larger
            else:
                node['central'] = False
                node['value'] = 10
        
        # Create the view
        view = {
            'viewType': 'complete',
            'centralEntity': entity_name,
            'entityType': entity_type,
            'nodes': nodes_list,
            'links': links,
            'description': f"Complete view centered on {entity_name} showing {len(links)} relationships."
        }
        
        return view
    
    def get_entity_info(self, entity_name, entity_type=None):
        """
        Get detailed information about an entity.
        
        Args:
            entity_name (str): Name of the entity
            entity_type (str, optional): Type of the entity (if known)
            
        Returns:
            dict: Entity information
        """
        # Construct the type constraint if provided
        type_constraint = ""
        params = {"entity_name": entity_name}
        
        if entity_type:
            type_constraint = f"AND n:{entity_type}"
        
        # Query to get entity information
        query = f"""
        MATCH (n {{name: $entity_name}}){type_constraint}
        OPTIONAL MATCH (n)-[r:MENTIONED_IN]->(s:Source)
        
        WITH n, collect({{
            source_id: s.id,
            source_title: s.title,
            source_type: s.type,
            mention_count: r.count
        }}) as sources
        
        RETURN n.name as name,
               labels(n)[0] as type,
               n.frequency as total_frequency,
               sources
        """
        
        result = self.graph.run(query, **params).data()
        
        if not result:
            return {
                'found': False,
                'message': f"Entity {entity_name} not found"
            }
        
        entity_info = result[0]
        
        # Get related entities
        related_query = f"""
        MATCH (n {{name: $entity_name}}){type_constraint}
        OPTIONAL MATCH (n)-[r]->(target)
        WHERE type(r) <> 'MENTIONED_IN' AND type(r) <> 'EVIDENCE'
        
        RETURN target.name as entity_name,
               labels(target)[0] as entity_type,
               type(r) as relationship,
               r.count as frequency
               
        UNION
        
        MATCH (n {{name: $entity_name}}){type_constraint}
        OPTIONAL MATCH (source)-[r]->(n)
        WHERE type(r) <> 'MENTIONED_IN' AND type(r) <> 'EVIDENCE'
        
        RETURN source.name as entity_name,
               labels(source)[0] as entity_type,
               type(r) as relationship,
               r.count as frequency
        
        ORDER BY frequency DESC
        LIMIT 10
        """
        
        related_entities = self.graph.run(related_query, **params).data()
        
        # Format the response
        info = {
            'found': True,
            'name': entity_info['name'],
            'type': entity_info['type'],
            'frequency': entity_info['total_frequency'],
            'sources': entity_info['sources'],
            'related_entities': related_entities
        }
        
        return info
    
    def search_entities(self, search_term, limit=10):
        """
        Search for entities in the knowledge graph.
        
        Args:
            search_term (str): Search term
            limit (int): Maximum number of results
            
        Returns:
            list: Matching entities
        """
        # Query to search for entities by name
        query = f"""
        MATCH (n)
        WHERE n.name CONTAINS $search_term
        AND NOT n:Category AND NOT n:Source AND NOT n:Root AND NOT n:RelationshipSchema
        
        RETURN n.name as name,
               labels(n)[0] as type,
               n.frequency as frequency
        
        ORDER BY n.frequency DESC
        LIMIT {limit}
        """
        
        results = self.graph.run(query, search_term=search_term).data()
        
        return results

# Example usage
if __name__ == "__main__":
    views = DualProcessViews()
    
    # Example for "heart failure"
    entity_name = "heart failure"
    
    # Get complete view
    complete_view = views.generate_complete_view(entity_name)
    print(f"Complete view: {len(complete_view['nodes'])} nodes, {len(complete_view['links'])} links")
    
    # Get System 1 view
    system1_view = views.generate_system1_view(entity_name)
    print(f"System 1 view: {len(system1_view['nodes'])} nodes, {len(system1_view['links'])} links")
    
    # Get System 2 view
    system2_view = views.generate_system2_view(entity_name)
    print(f"System 2 view: {len(system2_view['nodes'])} nodes, {len(system2_view['links'])} links") 
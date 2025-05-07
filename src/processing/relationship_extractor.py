"""
Module for extracting relationships between cardiology entities.
"""
import spacy
import logging
import os
import json
import re
from pathlib import Path
import sys
from collections import defaultdict, Counter
import pandas as pd
from tqdm import tqdm
import nltk
from nltk.tokenize import sent_tokenize
import itertools

# Add the project root to the path to import modules correctly
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RelationshipExtractor:
    """Class to extract relationships between cardiology entities."""
    
    def __init__(self, model_name="en_core_web_sm"):
        """
        Initialize the relationship extractor with a spaCy model.
        
        Args:
            model_name (str): Name of the spaCy model to use
        """
        # Load spaCy model
        try:
            self.nlp = spacy.load(model_name)
            logger.info(f"Loaded spaCy model: {model_name}")
        except Exception as e:
            logger.error(f"Error loading spaCy model: {str(e)}")
            raise
        
        # Try to load NLTK punkt if not already downloaded
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            logger.info("Downloading NLTK punkt tokenizer")
            nltk.download('punkt')
        
        # Define relationship patterns based on entity types
        self.relationship_patterns = [
            # Condition-Anatomy relationships
            {
                'subject_type': 'Condition',
                'object_type': 'Anatomy', 
                'pattern': r'(?i)(affects|involves|in|of|associated with|related to)',
                'rel_type': 'AFFECTS'
            },
            
            # Condition-Mechanism relationships
            {
                'subject_type': 'Condition',
                'object_type': 'Mechanism',
                'pattern': r'(?i)(involves|causes|leads to|results in|associated with|characterized by)',
                'rel_type': 'INVOLVES'
            },
            
            # Treatment-Condition relationships
            {
                'subject_type': 'Treatment',
                'object_type': 'Condition',
                'pattern': r'(?i)(treats|used for|effective for|indicated for|manages|therapy for)',
                'rel_type': 'TREATS'
            },
            
            # Diagnostic-Condition relationships
            {
                'subject_type': 'Diagnostic',
                'object_type': 'Condition',
                'pattern': r'(?i)(diagnoses|detects|identifies|confirms|rules out|evaluates|assesses|screens for)',
                'rel_type': 'DIAGNOSES'
            },
            
            # Finding-Condition relationships
            {
                'subject_type': 'Finding',
                'object_type': 'Condition',
                'pattern': r'(?i)(indicates|suggests|sign of|symptom of|manifestation of|associated with|seen in)',
                'rel_type': 'INDICATES'
            },
            
            # Procedure-Anatomy relationships
            {
                'subject_type': 'Procedure',
                'object_type': 'Anatomy',
                'pattern': r'(?i)(performed on|targets|involves|repairs|replaces|treats)',
                'rel_type': 'PERFORMED_ON'
            },
            
            # Anatomy-Anatomy relationships
            {
                'subject_type': 'Anatomy',
                'object_type': 'Anatomy',
                'pattern': r'(?i)(connected to|adjacent to|part of|contains|supplies|drains|attaches to)',
                'rel_type': 'CONNECTED_TO'
            },
            
            # Mechanism-Mechanism relationships
            {
                'subject_type': 'Mechanism',
                'object_type': 'Mechanism',
                'pattern': r'(?i)(leads to|causes|triggers|activates|inhibits|promotes|precedes|follows)',
                'rel_type': 'LEADS_TO'
            }
        ]
    
    def extract_relationships_from_sentence(self, sentence, entities):
        """
        Extract relationships from a single sentence.
        
        Args:
            sentence (str): Sentence text
            entities (list): List of entities detected in the sentence
            
        Returns:
            list: Extracted relationships
        """
        relationships = []
        
        # If there are less than 2 entities, no relationships can be formed
        if len(entities) < 2:
            return relationships
        
        # Process all pairs of entities
        for entity1, entity2 in itertools.combinations(entities, 2):
            # Skip if entities are the same
            if entity1['text'] == entity2['text']:
                continue
            
            # Get entity types
            type1 = entity1['type']
            type2 = entity2['type']
            
            # Check which relationship patterns might apply
            for pattern in self.relationship_patterns:
                # Check if entity types match the pattern
                if ((type1 == pattern['subject_type'] and type2 == pattern['object_type']) or 
                    (type2 == pattern['subject_type'] and type1 == pattern['object_type'])):
                    
                    # Get the text between the entities
                    start_idx = min(entity1['end'], entity2['end'])
                    end_idx = max(entity1['start'], entity2['start'])
                    
                    # Handle case where one entity is within another
                    if start_idx > end_idx:
                        between_text = ""
                    else:
                        between_text = sentence[start_idx:end_idx]
                    
                    # Check if the connecting text matches our pattern
                    if re.search(pattern['pattern'], between_text) or re.search(pattern['pattern'], sentence):
                        # Ensure subject-object order based on pattern
                        if type1 == pattern['subject_type'] and type2 == pattern['object_type']:
                            subject = entity1
                            object_entity = entity2
                        else:
                            subject = entity2
                            object_entity = entity1
                        
                        # Create relationship
                        relationship = {
                            'subject': subject['text'],
                            'subject_type': subject['type'],
                            'object': object_entity['text'],
                            'object_type': object_entity['type'],
                            'relationship': pattern['rel_type'],
                            'context': sentence,
                            'confidence': 0.7  # Simplified confidence score
                        }
                        
                        relationships.append(relationship)
        
        return relationships
    
    def extract_relationships_from_text(self, text, entities):
        """
        Extract relationships from text containing entities.
        
        Args:
            text (str): The text to process
            entities (list): Entities extracted from the text
            
        Returns:
            list: Extracted relationships
        """
        if not text or not entities:
            return []
        
        # Segment text into sentences
        sentences = sent_tokenize(text)
        
        all_relationships = []
        
        # Process each sentence
        for sentence in sentences:
            # Find entities in this sentence
            sentence_entities = []
            for entity in entities:
                # If entity context contains this sentence, include the entity
                if entity['context'] and sentence in entity['context']:
                    sentence_entities.append(entity)
            
            # Extract relationships from this sentence
            relationships = self.extract_relationships_from_sentence(sentence, sentence_entities)
            all_relationships.extend(relationships)
        
        return all_relationships
    
    def process_entity_results(self, entity_results_path):
        """
        Process entity extraction results to find relationships.
        
        Args:
            entity_results_path (str): Path to the entity extraction results JSON
            
        Returns:
            dict: Results with relationships by article
        """
        entity_results_path = os.path.join(project_root, entity_results_path)
        
        if not os.path.exists(entity_results_path):
            logger.error(f"Entity results file does not exist: {entity_results_path}")
            return {}
        
        try:
            # Load entity extraction results
            with open(entity_results_path, 'r', encoding='utf-8') as f:
                entity_results = json.load(f)
            
            if not entity_results:
                logger.warning("Entity results file is empty")
                return {}
            
            # Process each article's entities
            relationship_results = {}
            article_count = 0
            relationship_count = 0
            
            for article_id, data in tqdm(entity_results.items(), desc="Extracting relationships"):
                article_data = data['article_data']
                entities = data['entities']
                
                # Get the full text to process
                text_parts = []
                
                # Add title
                if 'title' in article_data and article_data['title']:
                    text_parts.append(article_data['title'])
                
                # Add abstract
                if 'abstract' in article_data and article_data['abstract']:
                    text_parts.append(article_data['abstract'])
                
                # Add content or full text if available
                if 'content' in article_data and article_data['content'] and article_data['content'] != "See URL for access to this resource.":
                    text_parts.append(article_data['content'])
                elif 'full_text' in article_data and article_data['full_text']:
                    text_parts.append(article_data['full_text'])
                
                # Join all text parts
                full_text = "\n\n".join(text_parts)
                
                # Extract relationships
                relationships = self.extract_relationships_from_text(full_text, entities)
                
                # Store results
                relationship_results[article_id] = {
                    'article_data': article_data,
                    'entities': entities,
                    'relationships': relationships
                }
                
                article_count += 1
                relationship_count += len(relationships)
            
            logger.info(f"Processed {article_count} articles, extracted {relationship_count} relationships")
            return relationship_results
            
        except Exception as e:
            logger.error(f"Error processing entity results: {str(e)}")
            return {}
    
    def save_results(self, results, output_path):
        """
        Save relationship extraction results to a JSON file.
        
        Args:
            results (dict): Results from process_entity_results
            output_path (str): Path to save results
            
        Returns:
            bool: True if successful, False otherwise
        """
        output_path = os.path.join(project_root, output_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved relationship results to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving relationship results: {str(e)}")
            return False
    
    def analyze_relationship_distribution(self, results):
        """
        Analyze the distribution of extracted relationships.
        
        Args:
            results (dict): Results from process_entity_results
            
        Returns:
            dict: Analysis of relationship distribution
        """
        all_relationships = []
        
        # Flatten all relationships
        for article_id, data in results.items():
            all_relationships.extend(data['relationships'])
        
        # Count by relationship type
        rel_type_counter = Counter()
        for rel in all_relationships:
            rel_type_counter[rel['relationship']] += 1
        
        # Count entity pairs by relationship type
        entity_pairs = defaultdict(Counter)
        for rel in all_relationships:
            pair_key = f"{rel['subject']}::{rel['object']}"
            entity_pairs[rel['relationship']][pair_key] += 1
        
        # Prepare analysis
        analysis = {
            'total_relationships': len(all_relationships),
            'by_type': {
                rel_type: {
                    'count': count,
                    'unique_pairs': len(entity_pairs[rel_type]),
                    'most_common_pairs': entity_pairs[rel_type].most_common(10)
                }
                for rel_type, count in rel_type_counter.items()
            }
        }
        
        return analysis

# Example usage
if __name__ == "__main__":
    extractor = RelationshipExtractor()
    results = extractor.process_entity_results("data/processed/extracted_entities.json")
    extractor.save_results(results, "data/processed/extracted_relationships.json")
    
    # Analyze results
    analysis = extractor.analyze_relationship_distribution(results)
    
    # Print summary
    print(f"\nRelationship Extraction Summary:")
    print(f"Total relationships: {analysis['total_relationships']}")
    
    print("\nRelationships by type:")
    for rel_type, data in analysis['by_type'].items():
        print(f"  {rel_type}: {data['count']} instances ({data['unique_pairs']} unique pairs)")
        
        print("  Most common pairs:")
        for pair, count in data['most_common_pairs'][:5]:
            subject, obj = pair.split("::")
            print(f"    {subject} -> {obj}: {count}") 
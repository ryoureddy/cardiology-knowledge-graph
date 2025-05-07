"""
Module for extracting cardiology-related entities from medical texts.
"""
import spacy
import logging
import os
import json
import re
from pathlib import Path
import sys
from collections import Counter
import pandas as pd
from tqdm import tqdm

# Add the project root to the path to import modules correctly
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CardiologyEntityExtractor:
    """Class to extract cardiology-related entities from medical texts."""
    
    def __init__(self, model_name="en_core_web_sm"):
        """
        Initialize the entity extractor with a spaCy model.
        
        Args:
            model_name (str): Name of the spaCy model to use
        """
        try:
            self.nlp = spacy.load(model_name)
            logger.info(f"Loaded spaCy model: {model_name}")
        except Exception as e:
            logger.error(f"Error loading spaCy model: {str(e)}")
            raise
        
        # Cardiology-specific entity patterns (simplified example)
        self.cardio_terms = {
            'Anatomy': [
                'heart', 'atrium', 'ventricle', 'aorta', 'valve', 'mitral valve', 
                'aortic valve', 'pulmonary valve', 'tricuspid valve', 
                'coronary artery', 'myocardium', 'endocardium', 'epicardium', 
                'pericardium', 'septum', 'interventricular septum', 'interatrial septum',
                'sinus node', 'av node', 'purkinje fibers', 'bundle of his',
                'papillary muscle', 'chordae tendineae', 'vena cava'
            ],
            'Condition': [
                'myocardial infarction', 'heart attack', 'coronary artery disease', 
                'angina', 'heart failure', 'cardiomyopathy', 'atrial fibrillation', 
                'ventricular fibrillation', 'tachycardia', 'bradycardia', 'arrhythmia',
                'hypertension', 'hypotension', 'pericarditis', 'endocarditis',
                'myocarditis', 'atherosclerosis', 'aneurysm', 'valvular heart disease',
                'mitral stenosis', 'mitral regurgitation', 'aortic stenosis', 
                'aortic regurgitation', 'congenital heart defect'
            ],
            'Diagnostic': [
                'echocardiogram', 'echocardiography', 'electrocardiogram', 'ECG', 'EKG',
                'cardiac catheterization', 'coronary angiogram', 'stress test',
                'holter monitor', 'cardiac MRI', 'cardiac CT', 'blood test', 'troponin test',
                'BNP test', 'cardiac enzyme'
            ],
            'Procedure': [
                'bypass surgery', 'CABG', 'coronary bypass', 'angioplasty', 'stent placement',
                'heart transplant', 'valve replacement', 'valve repair', 'ablation', 
                'pacemaker implantation', 'cardioversion', 'ICD implantation'
            ],
            'Treatment': [
                'beta blocker', 'ace inhibitor', 'angiotensin receptor blocker', 'ARB',
                'calcium channel blocker', 'diuretic', 'anticoagulant', 'aspirin',
                'statin', 'nitrate', 'vasodilator', 'inotrope', 'antiarrhythmic',
                'thrombolytic', 'cardiac glycoside', 'digoxin'
            ],
            'Finding': [
                'chest pain', 'dyspnea', 'shortness of breath', 'palpitations', 
                'syncope', 'edema', 'cyanosis', 'murmur', 'S3 gallop', 'S4 gallop',
                'crackles', 'elevated jugular venous pressure', 'JVP', 'tachypnea',
                'cardiomegaly', 'peripheral edema', 'clubbing', 'fatigue', 'cough',
                'orthopnea', 'paroxysmal nocturnal dyspnea', 'PND', 'diaphoresis',
                'pulmonary edema'
            ],
            'Mechanism': [
                'plaque formation', 'atherosclerotic plaque', 'thrombosis', 'embolism',
                'ischemia', 'reperfusion injury', 'remodeling', 'fibrosis',
                'inflammation', 'oxidative stress', 'endothelial dysfunction',
                'platelet aggregation', 'vasoconstriction', 'vasodilation',
                'cardiac remodeling', 'hypertrophy', 'diastolic dysfunction',
                'systolic dysfunction', 'conduction abnormality'
            ]
        }
        
        # Create an entity ruler for cardiology terms
        self.ruler = self.nlp.add_pipe("entity_ruler", before="ner")
        
        # Add patterns for each entity category
        patterns = []
        for category, terms in self.cardio_terms.items():
            for term in terms:
                patterns.append({"label": category, "pattern": term.lower()})
        
        self.ruler.add_patterns(patterns)
        logger.info(f"Added {len(patterns)} cardiology-specific entity patterns")
    
    def extract_entities(self, text):
        """
        Extract cardiology-related entities from text.
        
        Args:
            text (str): Text to extract entities from
            
        Returns:
            list: List of extracted entities with details
        """
        if not text or not isinstance(text, str):
            return []
        
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            # Only include entities with our cardiology labels
            if ent.label_ in self.cardio_terms.keys():
                entities.append({
                    'text': ent.text,
                    'type': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'context': text[max(0, ent.start_char-50):min(len(text), ent.end_char+50)]
                })
        
        return entities
    
    def process_article(self, article_path):
        """
        Process a single article file to extract entities.
        
        Args:
            article_path (str): Path to the article JSON file
            
        Returns:
            tuple: (article_data, extracted_entities)
        """
        try:
            with open(article_path, 'r', encoding='utf-8') as f:
                article_data = json.load(f)
            
            # Prepare text for processing
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
            
            # Extract entities
            entities = self.extract_entities(full_text)
            
            return article_data, entities
            
        except Exception as e:
            logger.error(f"Error processing article {article_path}: {str(e)}")
            return None, []
    
    def process_directory(self, dir_path, output_path=None):
        """
        Process all article files in a directory.
        
        Args:
            dir_path (str): Path to directory containing article JSON files
            output_path (str, optional): Path to save processed results
            
        Returns:
            dict: Results with entities by article
        """
        dir_path = os.path.join(project_root, dir_path)
        
        if not os.path.exists(dir_path):
            logger.error(f"Directory does not exist: {dir_path}")
            return {}
        
        # Get all JSON files in the directory
        json_files = [f for f in os.listdir(dir_path) if f.endswith('.json')]
        
        if not json_files:
            logger.warning(f"No JSON files found in {dir_path}")
            return {}
        
        # Process each file
        results = {}
        article_count = 0
        entity_count = 0
        
        for filename in tqdm(json_files, desc="Processing articles"):
            article_path = os.path.join(dir_path, filename)
            
            article_data, entities = self.process_article(article_path)
            if article_data is None:
                continue
            
            # Store results
            article_id = article_data.get('id', article_data.get('pmid', filename))
            results[article_id] = {
                'article_data': article_data,
                'entities': entities
            }
            
            article_count += 1
            entity_count += len(entities)
        
        logger.info(f"Processed {article_count} articles, extracted {entity_count} entities")
        
        # Save results if output path provided
        if output_path:
            output_path = os.path.join(project_root, output_path)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved extraction results to {output_path}")
        
        return results
    
    def analyze_entity_distribution(self, results):
        """
        Analyze the distribution of extracted entities.
        
        Args:
            results (dict): Results from process_directory
            
        Returns:
            dict: Analysis of entity distribution
        """
        entity_counts = Counter()
        entity_by_type = {}
        
        # Initialize counter for each entity type
        for entity_type in self.cardio_terms.keys():
            entity_by_type[entity_type] = Counter()
        
        # Count entities across all articles
        for article_id, data in results.items():
            for entity in data['entities']:
                entity_text = entity['text'].lower()
                entity_type = entity['type']
                
                entity_counts[entity_text] += 1
                entity_by_type[entity_type][entity_text] += 1
        
        # Prepare analysis results
        analysis = {
            'total_entities': sum(entity_counts.values()),
            'unique_entities': len(entity_counts),
            'entity_types': {
                entity_type: {
                    'count': sum(counter.values()),
                    'unique': len(counter),
                    'most_common': counter.most_common(10)
                }
                for entity_type, counter in entity_by_type.items()
            },
            'most_common_overall': entity_counts.most_common(20)
        }
        
        return analysis

# Example usage
if __name__ == "__main__":
    extractor = CardiologyEntityExtractor()
    results = extractor.process_directory("data/raw", "data/processed/extracted_entities.json")
    analysis = extractor.analyze_entity_distribution(results)
    
    # Print summary
    print(f"\nEntity Extraction Summary:")
    print(f"Total entities: {analysis['total_entities']}")
    print(f"Unique entities: {analysis['unique_entities']}")
    
    print("\nEntity counts by type:")
    for entity_type, data in analysis['entity_types'].items():
        print(f"  {entity_type}: {data['count']} instances ({data['unique']} unique)")
    
    print("\nMost common entities overall:")
    for entity, count in analysis['most_common_overall']:
        print(f"  {entity}: {count}") 
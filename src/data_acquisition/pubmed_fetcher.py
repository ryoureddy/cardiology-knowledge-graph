"""
Module for acquiring cardiology-related articles from PubMed.
"""
import requests
import time
import os
import json
import logging
from urllib.parse import quote_plus
from Bio import Entrez, Medline
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

class PubMedFetcher:
    """Class to fetch cardiology articles from PubMed."""
    
    def __init__(self, email=None, api_key=None, save_dir="data/raw"):
        """
        Initialize the PubMed fetcher.
        
        Args:
            email (str): Your email address (required by NCBI)
            api_key (str, optional): NCBI API key for higher rate limits
            save_dir (str): Directory to save fetched articles
        """
        # Get credentials from environment variables if not provided
        self.email = email or os.environ.get('PUBMED_EMAIL')
        self.api_key = api_key or os.environ.get('PUBMED_API_KEY')
        
        if not self.email:
            logger.warning("No email provided for PubMed API. Set PUBMED_EMAIL in .env file or pass as parameter.")
        
        # Set up required properties for NCBI's E-utilities
        Entrez.email = self.email
        if self.api_key:
            Entrez.api_key = self.api_key
        
        # Set up the save directory
        self.save_dir = os.path.join(project_root, save_dir)
        os.makedirs(self.save_dir, exist_ok=True)
        
    def search_articles(self, query, max_results=50, from_date=None, to_date=None):
        """
        Search for cardiology articles in PubMed.
        
        Args:
            query (str): Search term
            max_results (int): Maximum number of results to return
            from_date (str, optional): Start date in format YYYY/MM/DD
            to_date (str, optional): End date in format YYYY/MM/DD
            
        Returns:
            list: List of PubMed IDs (PMIDs)
        """
        logger.info(f"Searching PubMed for: {query}")
        
        # Construct the search term with a cardiology focus
        search_term = f"{query}[Title/Abstract] AND cardiology[MeSH Terms] AND free full text[filter]"
        
        # Add date range if provided
        if from_date and to_date:
            search_term += f" AND {from_date}:{to_date}[pdat]"
        
        try:
            # Perform the search using Entrez API
            handle = Entrez.esearch(
                db="pubmed",
                term=search_term,
                retmax=max_results,
                sort="relevance"
            )
            record = Entrez.read(handle)
            handle.close()
            
            pmids = record["IdList"]
            logger.info(f"Found {len(pmids)} articles for '{query}'")
            return pmids
            
        except Exception as e:
            logger.error(f"Error searching PubMed: {str(e)}")
            return []
    
    def fetch_article_details(self, pmids):
        """
        Fetch details for a list of PubMed articles.
        
        Args:
            pmids (list): List of PubMed IDs
            
        Returns:
            list: List of article metadata dictionaries
        """
        if not pmids:
            return []
            
        logger.info(f"Fetching details for {len(pmids)} articles")
        
        try:
            # Join PMIDs for the API call
            ids = ','.join(pmids)
            
            # Fetch the articles
            handle = Entrez.efetch(db="pubmed", id=ids, rettype="medline", retmode="text")
            records = list(Medline.parse(handle))
            handle.close()
            
            logger.info(f"Successfully fetched details for {len(records)} articles")
            return records
            
        except Exception as e:
            logger.error(f"Error fetching article details: {str(e)}")
            return []
    
    def fetch_full_text(self, pmid):
        """
        Attempt to fetch the full text of an article from PubMed Central.
        
        Args:
            pmid (str): PubMed ID
            
        Returns:
            str: Full text content if available, None otherwise
        """
        try:
            # First, try to find a link to PubMed Central
            handle = Entrez.elink(dbfrom="pubmed", db="pmc", linkname="pubmed_pmc", id=pmid)
            record = Entrez.read(handle)
            handle.close()
            
            # Check if there's a link to PMC
            if record[0]["LinkSetDb"] and record[0]["LinkSetDb"][0]["Link"]:
                pmc_id = record[0]["LinkSetDb"][0]["Link"][0]["Id"]
                logger.info(f"Found PMC ID {pmc_id} for PMID {pmid}")
                
                # Fetch the full text from PMC
                try:
                    handle = Entrez.efetch(db="pmc", id=pmc_id, rettype="text", retmode="text")
                    full_text = handle.read()
                    handle.close()
                    return full_text
                except Exception as e:
                    logger.warning(f"Error fetching full text for PMC ID {pmc_id}: {str(e)}")
                    return None
            else:
                logger.info(f"No PMC link found for PMID {pmid}")
                return None
                
        except Exception as e:
            logger.warning(f"Error finding PMC link for PMID {pmid}: {str(e)}")
            return None
    
    def save_article(self, article, full_text=None):
        """
        Save an article's metadata and full text to a JSON file.
        
        Args:
            article (dict): Article metadata
            full_text (str, optional): Article full text
            
        Returns:
            str: Path to the saved file
        """
        if not article or 'PMID' not in article:
            logger.warning("Cannot save article: Invalid article data or missing PMID")
            return None
        
        pmid = article['PMID']
        
        # Convert the article object to a serializable format
        article_data = {
            'pmid': pmid,
            'title': article.get('TI', ''),
            'abstract': article.get('AB', ''),
            'authors': article.get('AU', []),
            'journal': article.get('JT', ''),
            'publication_date': article.get('DP', ''),
            'mesh_terms': article.get('MH', []),
            'keywords': article.get('OT', []),
            'full_text': full_text if full_text else None,
            'source_type': 'pubmed'
        }
        
        # Save to file
        file_path = os.path.join(self.save_dir, f"pubmed_{pmid}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(article_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Saved article {pmid} to {file_path}")
        return file_path
        
    def get_cardiology_articles(self, search_terms, max_per_term=10, from_date=None, to_date=None):
        """
        Fetch cardiology articles for multiple search terms.
        
        Args:
            search_terms (list): List of search terms
            max_per_term (int): Maximum articles to fetch per term
            from_date (str, optional): Start date in format YYYY/MM/DD
            to_date (str, optional): End date in format YYYY/MM/DD
            
        Returns:
            list: List of paths to saved article files
        """
        saved_files = []
        
        for term in search_terms:
            logger.info(f"Processing search term: {term}")
            
            # Search for articles
            pmids = self.search_articles(term, max_results=max_per_term, 
                                       from_date=from_date, to_date=to_date)
            
            if not pmids:
                logger.warning(f"No articles found for '{term}'")
                continue
                
            # Process articles in batches to avoid timeouts
            batch_size = 10
            for i in range(0, len(pmids), batch_size):
                batch_pmids = pmids[i:i+batch_size]
                
                # Fetch article details
                articles = self.fetch_article_details(batch_pmids)
                
                # Process each article
                for article in articles:
                    # Try to fetch full text
                    full_text = self.fetch_full_text(article['PMID'])
                    
                    # Save the article
                    file_path = self.save_article(article, full_text)
                    if file_path:
                        saved_files.append(file_path)
                
                # Be nice to NCBI servers
                time.sleep(0.5)
            
            # Pause between search terms
            time.sleep(2)
            
        logger.info(f"Fetched and saved {len(saved_files)} articles in total")
        return saved_files

# Example usage
if __name__ == "__main__":
    # Set up the fetcher using environment variables
    fetcher = PubMedFetcher()
    
    # Define cardiology-specific search terms
    cardiology_terms = [
        "myocardial infarction",
        "atrial fibrillation",
        "heart failure",
        "cardiomyopathy",
        "coronary artery disease"
    ]
    
    # Fetch articles
    fetcher.get_cardiology_articles(cardiology_terms, max_per_term=5) 
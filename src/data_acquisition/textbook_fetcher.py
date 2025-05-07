"""
Module for fetching cardiology content from free medical textbooks.
"""
import requests
import time
import os
import json
import logging
import sys
from pathlib import Path
from bs4 import BeautifulSoup
import uuid

# Add the project root to the path to import modules correctly
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MedicalTextbookFetcher:
    """Class to fetch cardiology content from free medical textbooks."""
    
    def __init__(self, save_dir="data/raw"):
        """
        Initialize the medical textbook fetcher.
        
        Args:
            save_dir (str): Directory to save fetched content
        """
        self.save_dir = os.path.join(project_root, save_dir)
        os.makedirs(self.save_dir, exist_ok=True)
        
        # Set a user agent to behave like a browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
    
    def fetch_openstax_anatomy(self):
        """
        Fetch cardiovascular chapters from OpenStax Anatomy and Physiology.
        
        Returns:
            list: List of paths to saved content files
        """
        logger.info("Fetching cardiovascular chapters from OpenStax")
        saved_files = []
        
        # URLs for cardiovascular chapters
        cardio_chapter_urls = [
            "https://openstax.org/books/anatomy-and-physiology/pages/19-1-heart-anatomy",
            "https://openstax.org/books/anatomy-and-physiology/pages/19-2-cardiac-muscle-and-electrical-activity",
            "https://openstax.org/books/anatomy-and-physiology/pages/19-3-cardiac-cycle",
            "https://openstax.org/books/anatomy-and-physiology/pages/19-4-cardiac-physiology",
            "https://openstax.org/books/anatomy-and-physiology/pages/19-5-development-of-the-heart",
            "https://openstax.org/books/anatomy-and-physiology/pages/20-1-structure-and-function-of-blood-vessels",
            "https://openstax.org/books/anatomy-and-physiology/pages/20-2-blood-flow-blood-pressure-and-resistance"
        ]
        
        for url in cardio_chapter_urls:
            try:
                logger.info(f"Fetching content from: {url}")
                
                # Make a request to get the chapter content
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                
                # Parse the HTML content
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract the chapter title
                title_element = soup.find("h1")
                title = title_element.text.strip() if title_element else "Unknown Chapter Title"
                
                # Extract the content
                content_div = soup.find("div", class_="page-contents")
                if content_div:
                    content = content_div.get_text(separator=' ', strip=True)
                    
                    # Create a unique ID for this content
                    content_id = str(uuid.uuid4())
                    
                    # Prepare the data
                    data = {
                        'id': content_id,
                        'title': title,
                        'source': 'OpenStax Anatomy and Physiology',
                        'url': url,
                        'content': content,
                        'source_type': 'textbook'
                    }
                    
                    # Save to file
                    file_path = os.path.join(self.save_dir, f"openstax_{content_id}.json")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    saved_files.append(file_path)
                    logger.info(f"Saved OpenStax chapter: {title}")
                else:
                    logger.warning(f"Could not find content div for: {url}")
                    
                # Be polite to the server
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error fetching content from {url}: {str(e)}")
        
        logger.info(f"Fetched {len(saved_files)} OpenStax chapters")
        return saved_files
    
    def fetch_free_cardiology_books(self):
        """
        Fetch cardiology books from FreeBooks4Doctors.
        
        Returns:
            list: List of paths to saved book reference files
        """
        logger.info("Fetching cardiology books from FreeBooks4Doctors")
        saved_files = []
        
        # URL for cardiology section on FreeBooks4Doctors
        url = "http://www.freebooks4doctors.com/fb/CARD.htm"
        
        try:
            # Make a request to get the list of books
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all links that might point to books
            links = soup.find_all('a')
            
            for link in links:
                try:
                    href = link.get('href')
                    title = link.text.strip()
                    
                    # Skip empty or navigation links
                    if not href or not title or href.startswith('#') or href == 'index.htm':
                        continue
                    
                    # Make sure we have a full URL
                    if not href.startswith('http'):
                        href = f"http://www.freebooks4doctors.com/fb/{href}"
                    
                    # Create a unique ID for this book reference
                    book_id = str(uuid.uuid4())
                    
                    # Prepare the data - note that we're only storing references to these books
                    data = {
                        'id': book_id,
                        'title': title,
                        'source': 'Free Books 4 Doctors',
                        'url': href,
                        'content': "See URL for access to this resource.", # We're not downloading PDFs
                        'source_type': 'book_reference'
                    }
                    
                    # Save to file
                    file_path = os.path.join(self.save_dir, f"freebooks_{book_id}.json")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    saved_files.append(file_path)
                    logger.info(f"Saved book reference: {title}")
                    
                    # Be polite to the server
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing book link: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error fetching book list from {url}: {str(e)}")
        
        logger.info(f"Fetched {len(saved_files)} book references")
        return saved_files
        
    def fetch_all_sources(self):
        """
        Fetch content from all available sources.
        
        Returns:
            list: List of paths to all saved files
        """
        all_files = []
        
        # Fetch content from OpenStax
        openstax_files = self.fetch_openstax_anatomy()
        all_files.extend(openstax_files)
        
        # Fetch book references from FreeBooks4Doctors
        freebooks_files = self.fetch_free_cardiology_books()
        all_files.extend(freebooks_files)
        
        logger.info(f"Fetched a total of {len(all_files)} resources from all sources")
        return all_files

# Example usage
if __name__ == "__main__":
    fetcher = MedicalTextbookFetcher()
    fetcher.fetch_all_sources() 
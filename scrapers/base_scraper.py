from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging
import aiohttp
import asyncio
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class BaseScraper(ABC):
    """Base class for all scrapers"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"scraper.{name}")
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
    
    @abstractmethod
    async def scrape(self) -> Dict[str, Dict[str, Any]]:
        """Scrape the website and return the odds data
        
        Returns:
            Dict[str, Dict[str, Any]]: A dictionary with sports as keys and odds data as values
        """
        pass
    
    async def fetch_html(self, url: str) -> str:
        """Fetch HTML content from a URL
        
        Args:
            url (str): The URL to fetch
            
        Returns:
            str: The HTML content
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        self.logger.error(f"Failed to fetch {url}: {response.status}")
                        return ""
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            return ""
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content using BeautifulSoup
        
        Args:
            html (str): The HTML content to parse
            
        Returns:
            BeautifulSoup: The parsed HTML
        """
        return BeautifulSoup(html, 'lxml')
    
    def log_info(self, message: str) -> None:
        """Log an info message
        
        Args:
            message (str): The message to log
        """
        self.logger.info(message)
    
    def log_error(self, message: str) -> None:
        """Log an error message
        
        Args:
            message (str): The message to log
        """
        self.logger.error(message)
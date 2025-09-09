import asyncio
import json
import os
from datetime import datetime
import logging
from typing import Dict, Any, List

from .draftkings_scraper import DraftKingsScraper
from .fanduel_scraper import FanduelScraper
from .betmgm_scraper import BetMGMScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("scheduler")

# Path to the JSON file where odds data is stored
ODDS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "odds.json")

# Ensure the data directory exists
os.makedirs(os.path.dirname(ODDS_FILE), exist_ok=True)

async def run_scrapers() -> None:
    """Run all scrapers and update the odds data"""
    logger.info("Starting scraper scheduler")
    
    # Initialize scrapers
    scrapers = [
        DraftKingsScraper(),
        FanduelScraper(),
        BetMGMScraper()
    ]
    
    # Run all scrapers concurrently
    scraper_tasks = [scraper.scrape() for scraper in scrapers]
    results = await asyncio.gather(*scraper_tasks, return_exceptions=True)
    
    # Process results
    all_odds = {}
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Error running scraper {scrapers[i].name}: {str(result)}")
            continue
        
        # Add the scraper name to the results
        for sport, sport_data in result.items():
            if sport not in all_odds:
                all_odds[sport] = {}
            
            all_odds[sport][scrapers[i].name] = sport_data
    
    # Update the odds file
    await update_odds_file(all_odds)
    
    logger.info("Completed scraper scheduler")

async def update_odds_file(odds_data: Dict[str, Dict[str, Any]]) -> None:
    """Update the odds file with new data
    
    Args:
        odds_data: The new odds data
    """
    try:
        # Load existing data if file exists
        if os.path.exists(ODDS_FILE):
            with open(ODDS_FILE, "r") as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = {"last_updated": None, "odds": {}}
        else:
            existing_data = {"last_updated": None, "odds": {}}
        
        # Update the data
        existing_data["odds"] = odds_data
        existing_data["last_updated"] = datetime.now().isoformat()
        
        # Write the updated data back to the file
        with open(ODDS_FILE, "w") as f:
            json.dump(existing_data, f, indent=2)
        
        logger.info(f"Updated odds file with data for {len(odds_data)} sports")
    except Exception as e:
        logger.error(f"Error updating odds file: {str(e)}")

# Function to run the scrapers on a schedule
async def schedule_scrapers(interval_seconds: int = 300) -> None:
    """Run the scrapers on a schedule
    
    Args:
        interval_seconds: The interval between scraper runs in seconds (default: 5 minutes)
    """
    while True:
        try:
            await run_scrapers()
        except Exception as e:
            logger.error(f"Error in scheduler: {str(e)}")
        
        logger.info(f"Waiting {interval_seconds} seconds until next scrape")
        await asyncio.sleep(interval_seconds)
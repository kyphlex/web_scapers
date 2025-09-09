import asyncio
import uvicorn
import os
import sys
import argparse
from scrapers.scheduler import run_scrapers, schedule_scrapers

async def run_once():
    """Run the scrapers once and exit"""
    await run_scrapers()
    print("Scrapers completed successfully. Data saved to data/odds.json")

def run_api():
    """Run the FastAPI server"""
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

async def run_scheduler(interval_seconds):
    """Run the scheduler to periodically update odds data"""
    await schedule_scrapers(interval_seconds)

def main():
    parser = argparse.ArgumentParser(description="Sports Betting Odds Scraper")
    parser.add_argument("--mode", choices=["api", "scrape", "schedule"], default="api",
                        help="Run mode: api (run API server), scrape (run scrapers once), schedule (run scrapers on schedule)")
    parser.add_argument("--interval", type=int, default=300,
                        help="Interval between scraper runs in seconds (default: 300)")
    
    args = parser.parse_args()
    
    if args.mode == "api":
        run_api()
    elif args.mode == "scrape":
        asyncio.run(run_once())
    elif args.mode == "schedule":
        asyncio.run(run_scheduler(args.interval))

if __name__ == "__main__":
    main()
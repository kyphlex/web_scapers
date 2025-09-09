import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

from scrapers.scheduler import run_scrapers
from utils.odds_comparison import compare_odds

app = FastAPI(title="Sports Betting Odds API", 
              description="API for retrieving live betting odds from multiple sportsbooks",
              version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to the JSON file where odds data is stored
ODDS_FILE = os.path.join(os.path.dirname(__file__), "data", "odds.json")

# Ensure the data directory exists
os.makedirs(os.path.dirname(ODDS_FILE), exist_ok=True)

# Initialize the odds file if it doesn't exist
if not os.path.exists(ODDS_FILE):
    with open(ODDS_FILE, "w") as f:
        json.dump({"last_updated": None, "odds": {}}, f)

@app.get("/")
async def root():
    return {"message": "Welcome to the Sports Betting Odds API"}

@app.get("/odds")
async def get_odds(sport: Optional[str] = None, bookmaker: Optional[str] = None):
    """Get the latest odds for all sports or filter by sport and/or bookmaker"""
    try:
        with open(ODDS_FILE, "r") as f:
            data = json.load(f)
        
        if not data.get("odds"):
            return JSONResponse(
                status_code=404,
                content={"message": "No odds data available. Try again later."}
            )
        
        # Filter by sport if specified
        if sport:
            filtered_odds = {k: v for k, v in data["odds"].items() if k.lower() == sport.lower()}
            if not filtered_odds:
                return JSONResponse(
                    status_code=404,
                    content={"message": f"No odds data available for sport: {sport}"}
                )
            data["odds"] = filtered_odds
        
        # Filter by bookmaker if specified
        if bookmaker:
            for sport_name, sport_data in data["odds"].items():
                filtered_bookmakers = {k: v for k, v in sport_data.items() if k.lower() == bookmaker.lower()}
                if filtered_bookmakers:
                    data["odds"][sport_name] = filtered_bookmakers
                else:
                    # Remove sports that don't have the specified bookmaker
                    data["odds"][sport_name] = {}
            
            # Remove empty sports
            data["odds"] = {k: v for k, v in data["odds"].items() if v}
            
            if not data["odds"]:
                return JSONResponse(
                    status_code=404,
                    content={"message": f"No odds data available for bookmaker: {bookmaker}"}
                )
        
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/compare")
async def compare_bookmakers(sport: str, event_id: Optional[str] = None, market: Optional[str] = None):
    """Compare odds across different bookmakers for a specific sport and optionally for a specific event and market"""
    try:
        with open(ODDS_FILE, "r") as f:
            data = json.load(f)
        
        if not data.get("odds") or sport.lower() not in [s.lower() for s in data["odds"]]:
            return JSONResponse(
                status_code=404,
                content={"message": f"No odds data available for sport: {sport}"}
            )
        
        # Get the sport data (case insensitive)
        sport_key = next((s for s in data["odds"] if s.lower() == sport.lower()), None)
        sport_data = data["odds"][sport_key]
        
        # Compare odds across bookmakers
        comparison = compare_odds(sport_data, event_id, market)
        
        if not comparison:
            return JSONResponse(
                status_code=404,
                content={"message": f"No comparable odds found for the specified criteria"}
            )
        
        return {"comparison": comparison, "last_updated": data["last_updated"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bookmakers")
async def get_bookmakers():
    """Get a list of all available bookmakers"""
    try:
        with open(ODDS_FILE, "r") as f:
            data = json.load(f)
        
        if not data.get("odds"):
            return JSONResponse(
                status_code=404,
                content={"message": "No odds data available. Try again later."}
            )
        
        # Collect all unique bookmakers across all sports
        bookmakers = set()
        for sport_data in data["odds"].values():
            bookmakers.update(sport_data.keys())
        
        return {"bookmakers": sorted(list(bookmakers))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sports")
async def get_sports():
    """Get a list of all available sports"""
    try:
        with open(ODDS_FILE, "r") as f:
            data = json.load(f)
        
        if not data.get("odds"):
            return JSONResponse(
                status_code=404,
                content={"message": "No odds data available. Try again later."}
            )
        
        return {"sports": sorted(list(data["odds"].keys()))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trigger-scrape")
async def trigger_scrape():
    """Manually trigger the scraping process"""
    try:
        await run_scrapers()
        return {"message": "Scraping process triggered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
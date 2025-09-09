from typing import Dict, Any
import json
import re
from .base_scraper import BaseScraper

class BetMGMScraper(BaseScraper):
    """Scraper for BetMGM sportsbook"""
    
    def __init__(self):
        super().__init__("BetMGM")
        self.base_url = "https://sports.betmgm.com"
        self.sports_urls = {
            "NFL": f"{self.base_url}/en/sports/football/nfl",
            "NBA": f"{self.base_url}/en/sports/basketball/nba",
            "MLB": f"{self.base_url}/en/sports/baseball/mlb",
            "NHL": f"{self.base_url}/en/sports/ice-hockey/nhl",
            "Soccer": f"{self.base_url}/en/sports/soccer"
        }
    
    async def scrape(self) -> Dict[str, Dict[str, Any]]:
        """Scrape BetMGM for odds data"""
        self.log_info("Starting BetMGM scraper")
        results = {}
        
        for sport, url in self.sports_urls.items():
            self.log_info(f"Scraping {sport} from BetMGM")
            html = await self.fetch_html(url)
            
            if not html:
                self.log_error(f"Failed to fetch HTML for {sport} from BetMGM")
                continue
            
            # Parse the HTML
            soup = self.parse_html(html)
            
            # Extract the odds data
            sport_data = self._extract_odds(soup, sport)
            
            if sport_data:
                results[sport] = sport_data
            else:
                self.log_info(f"No odds data found for {sport} on BetMGM")
        
        self.log_info(f"Completed BetMGM scraper, found data for {len(results)} sports")
        return results
    
    def _extract_odds(self, soup, sport: str) -> Dict[str, Any]:
        """Extract odds data from the parsed HTML
        
        Args:
            soup: The parsed HTML
            sport: The sport being scraped
            
        Returns:
            Dict[str, Any]: The extracted odds data
        """
        events = []
        
        try:
            # Look for the script tag containing the initial state data
            script_tags = soup.find_all("script")
            data_script = None
            
            for script in script_tags:
                if script.string and "__PRELOADED_STATE__" in script.string:
                    data_script = script.string
                    break
            
            if not data_script:
                self.log_error(f"Could not find preloaded state data for {sport}")
                return {}
            
            # Extract the JSON data
            json_str = re.search(r'__PRELOADED_STATE__\s*=\s*(\{.*\});', data_script, re.DOTALL)
            if not json_str:
                self.log_error(f"Could not extract JSON data for {sport}")
                return {}
            
            try:
                data = json.loads(json_str.group(1))
                
                # Navigate through the data structure to find the events
                if 'competitions' in data:
                    for competition in data['competitions']:
                        if 'events' in competition:
                            for event in competition['events']:
                                event_data = self._parse_event(event)
                                if event_data:
                                    events.append(event_data)
            except json.JSONDecodeError as e:
                self.log_error(f"Error parsing JSON data for {sport}: {str(e)}")
                return {}
            
        except Exception as e:
            self.log_error(f"Error extracting odds for {sport}: {str(e)}")
            return {}
        
        return {
            "events": events,
            "last_updated": None  # This will be set by the scheduler
        }
    
    def _parse_event(self, event) -> Dict[str, Any]:
        """Parse an event from the JSON data
        
        Args:
            event: The event data from the JSON
            
        Returns:
            Dict[str, Any]: The parsed event data
        """
        try:
            event_id = event.get('id')
            event_name = event.get('name', '')
            start_time = event.get('startTime')
            
            # Extract teams
            teams = []
            if 'participants' in event:
                for participant in event['participants']:
                    teams.append(participant.get('name', ''))
            
            # Extract markets and odds
            markets = []
            if 'markets' in event:
                for market in event['markets']:
                    market_data = self._parse_market(market)
                    if market_data:
                        markets.append(market_data)
            
            return {
                "id": event_id,
                "name": event_name,
                "start_time": start_time,
                "teams": teams,
                "markets": markets
            }
        except Exception as e:
            self.log_error(f"Error parsing event: {str(e)}")
            return {}
    
    def _parse_market(self, market) -> Dict[str, Any]:
        """Parse a market from the JSON data
        
        Args:
            market: The market data from the JSON
            
        Returns:
            Dict[str, Any]: The parsed market data
        """
        try:
            market_id = market.get('id')
            market_name = market.get('name', '')
            
            # Extract outcomes
            outcomes = []
            if 'selections' in market:
                for selection in market['selections']:
                    outcome_data = {
                        "name": selection.get('name', ''),
                        "price": selection.get('price', {}).get('american'),
                        "points": selection.get('handicap')
                    }
                    outcomes.append(outcome_data)
            
            return {
                "id": market_id,
                "name": market_name,
                "outcomes": outcomes
            }
        except Exception as e:
            self.log_error(f"Error parsing market: {str(e)}")
            return {}
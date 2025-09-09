from typing import Dict, Any, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("odds_comparison")

def compare_odds(sport_data: Dict[str, Any], event_id: Optional[str] = None, market_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Compare odds across different bookmakers for a specific sport
    
    Args:
        sport_data: The sport data containing odds from different bookmakers
        event_id: Optional event ID to filter by
        market_type: Optional market type to filter by (e.g., "moneyline", "spread", "total")
        
    Returns:
        List[Dict[str, Any]]: A list of comparisons for each event and market
    """
    comparisons = []
    
    try:
        # Get all events from all bookmakers
        all_events = {}
        
        for bookmaker, data in sport_data.items():
            if "events" not in data:
                continue
            
            for event in data["events"]:
                event_key = event.get("id") or event.get("name")
                if not event_key:
                    continue
                
                if event_id and str(event_key) != str(event_id):
                    continue
                
                if event_key not in all_events:
                    all_events[event_key] = {
                        "id": event.get("id"),
                        "name": event.get("name"),
                        "start_time": event.get("start_time"),
                        "teams": event.get("teams", []),
                        "bookmakers": {}
                    }
                
                # Add markets for this bookmaker
                all_events[event_key]["bookmakers"][bookmaker] = {
                    "markets": event.get("markets", [])
                }
        
        # For each event, compare the odds across bookmakers
        for event_key, event_data in all_events.items():
            # Get all unique market types across all bookmakers
            all_markets = {}
            
            for bookmaker, bookmaker_data in event_data["bookmakers"].items():
                for market in bookmaker_data["markets"]:
                    market_key = market.get("id") or market.get("name")
                    if not market_key:
                        continue
                    
                    # Filter by market type if specified
                    if market_type and market_type.lower() not in market.get("name", "").lower():
                        continue
                    
                    if market_key not in all_markets:
                        all_markets[market_key] = {
                            "id": market.get("id"),
                            "name": market.get("name"),
                            "bookmakers": {}
                        }
                    
                    # Add outcomes for this bookmaker
                    all_markets[market_key]["bookmakers"][bookmaker] = {
                        "outcomes": market.get("outcomes", [])
                    }
            
            # For each market, compare the odds across bookmakers
            market_comparisons = []
            for market_key, market_data in all_markets.items():
                # Get all unique outcomes across all bookmakers
                all_outcomes = {}
                
                for bookmaker, bookmaker_data in market_data["bookmakers"].items():
                    for outcome in bookmaker_data["outcomes"]:
                        outcome_key = outcome.get("name")
                        if not outcome_key:
                            continue
                        
                        if outcome_key not in all_outcomes:
                            all_outcomes[outcome_key] = {
                                "name": outcome_key,
                                "bookmakers": {}
                            }
                        
                        # Add price for this bookmaker
                        all_outcomes[outcome_key]["bookmakers"][bookmaker] = {
                            "price": outcome.get("price"),
                            "points": outcome.get("points")
                        }
                
                # Find the best odds for each outcome
                for outcome_key, outcome_data in all_outcomes.items():
                    best_price = None
                    best_bookmaker = None
                    
                    for bookmaker, price_data in outcome_data["bookmakers"].items():
                        price = price_data.get("price")
                        if price is None:
                            continue
                        
                        # Convert to numeric if it's a string
                        if isinstance(price, str):
                            try:
                                price = float(price.replace("+", ""))
                            except ValueError:
                                continue
                        
                        # For American odds, higher positive or lower negative is better
                        if best_price is None or \
                           (price > 0 and (best_price <= 0 or price > best_price)) or \
                           (price < 0 and best_price < 0 and price > best_price):
                            best_price = price
                            best_bookmaker = bookmaker
                    
                    outcome_data["best_price"] = best_price
                    outcome_data["best_bookmaker"] = best_bookmaker
                
                # Add the market comparison
                market_comparisons.append({
                    "market": {
                        "id": market_data.get("id"),
                        "name": market_data.get("name")
                    },
                    "outcomes": list(all_outcomes.values())
                })
            
            # Add the event comparison
            comparisons.append({
                "event": {
                    "id": event_data.get("id"),
                    "name": event_data.get("name"),
                    "start_time": event_data.get("start_time"),
                    "teams": event_data.get("teams")
                },
                "markets": market_comparisons
            })
    
    except Exception as e:
        logger.error(f"Error comparing odds: {str(e)}")
    
    return comparisons

def american_to_decimal(american_odds: float) -> float:
    """Convert American odds to decimal odds
    
    Args:
        american_odds: The American odds
        
    Returns:
        float: The decimal odds
    """
    if american_odds > 0:
        return (american_odds / 100) + 1
    else:
        return (100 / abs(american_odds)) + 1

def decimal_to_american(decimal_odds: float) -> float:
    """Convert decimal odds to American odds
    
    Args:
        decimal_odds: The decimal odds
        
    Returns:
        float: The American odds
    """
    if decimal_odds >= 2:
        return (decimal_odds - 1) * 100
    else:
        return -100 / (decimal_odds - 1)

def calculate_implied_probability(american_odds: float) -> float:
    """Calculate the implied probability from American odds
    
    Args:
        american_odds: The American odds
        
    Returns:
        float: The implied probability (0-1)
    """
    decimal_odds = american_to_decimal(american_odds)
    return 1 / decimal_odds

def calculate_arbitrage_opportunity(odds: List[float]) -> Dict[str, Any]:
    """Calculate if there's an arbitrage opportunity given a list of odds
    
    Args:
        odds: A list of American odds for different outcomes of the same event
        
    Returns:
        Dict[str, Any]: Information about the arbitrage opportunity, if any
    """
    # Convert to decimal odds
    decimal_odds = [american_to_decimal(odd) for odd in odds]
    
    # Calculate the sum of implied probabilities
    implied_probs = [1 / odd for odd in decimal_odds]
    total_implied_prob = sum(implied_probs)
    
    # If the sum is less than 1, there's an arbitrage opportunity
    if total_implied_prob < 1:
        # Calculate the optimal stake distribution
        stakes = [prob / total_implied_prob for prob in implied_probs]
        
        # Calculate the guaranteed profit
        profit_percentage = (1 / total_implied_prob) - 1
        
        return {
            "arbitrage_exists": True,
            "total_implied_probability": total_implied_prob,
            "profit_percentage": profit_percentage * 100,  # Convert to percentage
            "optimal_stakes": stakes
        }
    else:
        return {
            "arbitrage_exists": False,
            "total_implied_probability": total_implied_prob
        }
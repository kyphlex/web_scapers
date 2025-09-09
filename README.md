# Sports Betting Odds Scraper

This project scrapes live betting odds from multiple sportsbook websites, stores the results in a JSON file, and serves them via a FastAPI endpoint. It also includes a feature to compare odds across different sportsbooks.

## Features

- Scrapes betting odds from multiple sportsbooks (DraftKings, FanDuel, BetMGM)
- Stores odds data in a JSON file
- Provides a FastAPI server to access the odds data
- Allows filtering odds by sport and bookmaker
- Includes a comparison feature to find the best odds across different sportsbooks
- Calculates potential arbitrage opportunities

## Installation

1. Clone the repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

The application can be run in three different modes:

### API Server

Run the FastAPI server to serve the odds data:

```bash
python run.py --mode api
```

The API will be available at http://localhost:8000

### One-time Scrape

Run the scrapers once to update the odds data:

```bash
python run.py --mode scrape
```

### Scheduled Scraping

Run the scrapers on a schedule to continuously update the odds data:

```bash
python run.py --mode schedule --interval 300
```

The interval is specified in seconds (default: 300 seconds = 5 minutes).

## API Endpoints

- `GET /`: Welcome message
- `GET /odds`: Get all odds data (can filter by sport and bookmaker)
- `GET /compare`: Compare odds across different bookmakers for a specific sport
- `GET /bookmakers`: Get a list of all available bookmakers
- `GET /sports`: Get a list of all available sports
- `POST /trigger-scrape`: Manually trigger the scraping process

## Project Structure

```
.
├── data/
│   └── odds.json         # Stored odds data
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py   # Base scraper class
│   ├── draftkings_scraper.py
│   ├── fanduel_scraper.py
│   ├── betmgm_scraper.py
│   └── scheduler.py      # Scheduler for running scrapers
├── utils/
│   ├── __init__.py
│   └── odds_comparison.py # Odds comparison utilities
├── main.py               # FastAPI application
├── run.py                # Script to run the application
├── requirements.txt      # Dependencies
└── README.md             # This file
```

## Adding New Scrapers

To add a new scraper for another sportsbook:

1. Create a new scraper class in the `scrapers` directory that inherits from `BaseScraper`
2. Implement the `scrape` method to extract odds data from the sportsbook
3. Add the new scraper to the list in `scrapers/scheduler.py`

## Disclaimer

This project is for educational purposes only. Be aware that web scraping may be against the terms of service of some websites. Always check the terms of service before scraping any website.

## License

MIT
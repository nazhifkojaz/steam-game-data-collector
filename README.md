# Steam Game Data Collector

A unified tool for collecting Steam game data from multiple sources. Fetch steam game data based on its `steam_appid` from Steam Store, Steam Charts, Steam Reviews, Steam Spy, Gamalytic, HowLongToBeat, and Steam Web API.


## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [API Keys & Source Behavior](#api-keys--source-behavior)
- [Rate Limiting](#rate-limiting)
- [Data Model](#data-model)
- [Development & Contributions](#development--contributions)
- [License](#license)


## Features
- **One-stop data collection**: Combine data from multiple sources into a single, unified model.
- **Direct source access**: Call any source directly via:
  ```python
  from gameinsights.sources import SteamStore, SteamCharts, ...
  ```
- **Utilities for discovery**:  
  `gameinsights.utils.GameSearch` can:
  - Fetch the full Steam app list
  - Perform fuzzy search to find `steam_appid` by game name
- **Built-in collectors**:
  - Game reviews
  - Active player time series (SteamCharts)
  - Steam user/player data
- **Planned features**: `Visualizer` and `Analyzer` (coming soon)


## Requirements
- **Python** ≥ 3.10


## Installation

**From PyPI (coming soon)**:
```bash
pip install steam-game-data-collector
```

**From GitHub (beta)**:
```bash
pip install "git+https://github.com/nazhifkojaz/steam-game-data-collector.git"
```

**Using Poetry**:
```bash
poetry add git+https://github.com/nazhifkojaz/steam-game-data-collector.git
```

**For development**:
```bash
git clone https://github.com/nazhifkojaz/steam-game-data-collector.git
cd steam-game-data-collector
poetry install
# Optional: for development extras
poetry install --with dev
```


## Quickstart

**Basic game data (default `recap=False` returns full normalized data):**
```python
from gameinsights.collector import Collector

collector = Collector()
full_data = collector.get_games_data(["570", "730"])
print(full_data[0]["name"], full_data[0].get("owners"))
```
*if no data provided by the sources, 'None' or 'NaN' will be assigned to the data labels*

**Active players (SteamCharts):**
```python
df = collector.get_games_active_player_data(["570", "730"])  # pandas.DataFrame
print(df.head())
```

**Reviews (Steam Reviews):**
```python
reviews_df = collector.get_game_review("570", review_only=True)
```

**Steam user/player data (Steam Web API):**
```python
collector = Collector(steam_api_key="<YOUR_STEAM_WEB_API_KEY>")
users_df = collector.get_user_data(["76561198084297256"], include_free_games=True)
```

**Direct source access:**
```python
from gameinsights.sources import SteamCharts

src = SteamCharts()
result = src.fetch("570")
print(result["success"], result["data"]["active_player_24h"])
```
*(successful fetch will have "success": True and "data" key, while failed fetch will have "success": False and "error" key)*

**Utilities – list & search games:**
```python
from gameinsights.utils.gamesearch import GameSearch

search = GameSearch()
all_games = search.get_game_list()
results = search.search_by_name("Dota", top_n=5)
print(results)  # [{'appid': '570', 'name': 'Dota 2', 'search_score': 99.0}, ...]
```


## API Keys & Source Behavior

- **Steam Store**: No key. Respects `region` & `language`; some appids may be region-restricted.
- **Steam Web API**:  
  - `SteamUser` → requires `steam_api_key` ([Get it here](https://steamcommunity.com/dev/apikey)).
  - `SteamAchievements` → global percentages work without a key; schema/details require a key.
- **Gamalytic**: No key for now (API key support planned).
- **HowLongToBeat**: No key; scraping-based (inspired by [HowLongToBeat-PythonAPI](https://github.com/ScrappyCocco/HowLongToBeat-PythonAPI)).
- **Steam Charts**: No key; BeautifulSoup scraping.
- **Steam Spy**: No key.


## Rate Limiting

**Global wrapper**:  
`Collector(calls=60, period=60)` → limits multi-source operations.

**Per-source** (approximate):
- Steam Store: ~60 requests/min
- Steam Charts: ~60 requests/min
- HowLongToBeat: ~60 requests/min (polite scraping)
- Steam Spy: ~60 requests/min
- Gamalytic: ~500 requests/day
- Steam Achievements: ~100,000 requests/day
- Steam User: ~100,000 requests/day (small internal sleeps via `Collector`)
- Steam Review: ~100,000/day (0.5s sleep per page)

> **Note:** Some sources rely on scraping, which may violate its robots.txt — please use responsibly.


## Data Model

When `recap=False` (default), `get_games_data` returns **full normalized models** per `appid`.

Key fields include:
- **steam_appid**: Steam appid (str)
- **name**: Game name (Steam Store)
- **developers / publishers**: Lists (Steam Store)
- **price_currency / price_initial / price_final**: Pricing info (Steam Store)
- **metacritic_score**: Integer score (Steam Store)
- **release_date / days_since_release**: Datetime & derived days (Steam Store)
- **average_playtime_h / average_playtime**: Hours & seconds (Gamalytic)
- **copies_sold / estimated_revenue / owners**: Sales estimates (Gamalytic)
- **ccu**: Concurrent users (Steam Spy)
- **active_player_24h / peak_active_player_all_time**: Peaks (Steam Charts)
- **monthly_active_player**: Time series data (Steam Charts)
- **review_score / review_score_desc / total_positive / total_negative / total_reviews**: Reviews (Steam Reviews)
- **achievements_count / achievements_percentage_average / achievements_list**: Achievements (Steam Web API)
- **comp_main / comp_plus / comp_100 / comp_all**: Completion times (HowLongToBeat)
- **languages / platforms / categories / genres / tags / content_rating**: Metadata

**If `recap=True`**, returns a subset of the detailed data:
- `steam_appid`, `name`, `developers`, `publishers`
- `release_date`, `days_since_release`
- `price_currency`, `price_initial`, `price_final`
- `copies_sold`, `estimated_revenue`, `owners`
- `total_positive`, `total_negative`, `total_reviews`
- `comp_main`, `comp_plus`, `comp_100`, `comp_all`, `invested_co`, `invested_mp`, `average_playtime`
- `active_player_24h`, `peak_active_player_all_time`
- `achievements_count`, `achievements_percentage_average`
- `categories`, `genres`, `tags`


## Development & Contributions

1. **Fork** the repo & create a feature branch from `main`.
2. **Run style checks** locally:
```bash
poetry run ruff check gameinsights/ tests/
poetry run black gameinsights/ tests/
poetry run mypy gameinsights/
poetry run pytest -vv
```
3. **Open a Pull Request** with:
   - Clear description
   - Tests (if applicable)
   - Small, focused changes
4. Not ready to code? Open an **Issue** describing your idea or bug.

## License
MIT

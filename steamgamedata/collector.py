import json
from typing import Literal
import pandas as pd
from datetime import datetime
import steamgamedata.sources as sources

class SteamGameData:
    def __init__(self, region: str = "us", language: str = "english", steam_api_key: str | None = None, gamalytic_api_key: str | None = None):
        """Initialize the collector with an optional API key.
        Args:
            region (str): Region for the API request. Default is "us".
            language (str): Language for the API request. Default is "english".
            steam_api_key (str): Optional API key for Steam API.
            gamalytic_api_key (str): Optional API key for Gamalytic API.
        """
        self.region = region
        self.language = language
        self.steam_api_key = steam_api_key
        self.gamalytic_api_key = gamalytic_api_key
        
    def set_region(self, region: str):
        """Set the region for the API request.
        Args:
            region (str): Region for the API request.
        """
        self.region = region

    def set_language(self, language: str):
        """Set the language for the API request.
        Args:
            language (str): Language for the API request.
        """
        self.language = language

    def set_steam_api_key(self, steam_api_key: str):
        """Set the API key for the Steam API.
        Args:
            steam_api_key (str): API key for Steam API.
        """
        self.steam_api_key = steam_api_key

    def set_gamalytic_api_key(self, gamalytic_api_key: str):
        """Set the API key for the Gamalytic API.
        Args:
            gamalytic_api_key (str): API key for Gamalytic API.
        """
        self.gamalytic_api_key = gamalytic_api_key

    def _fetch_raw_data(self, appid: str) -> dict:
        """Fetch game data from all sources based on appid.
        Args:
            appid (str): The appid of the game to fetch data for.

        Returns:
            dict: The combined game data from all sources.
        """
        
        # combine the data from all the sources
        ## initialize sources
        sources_to_use = [
            sources.Steam(region=self.region, language=self.language, api_key=self.steam_api_key),
            sources.SteamSpy(),
            sources.Gamalytic(api_key=self.gamalytic_api_key),
            sources.SteamCharts()
        ]
        
        result = {}

        for source in sources_to_use:
            data = source.get_game_data(appid)
            if data.get("status", False):
                # if the status is true, update the result with the data
                result.update(data.get("data"))

        return result
    
    def _additional_data(self, raw_data: dict) -> dict:
        """Process additional data from the raw data.
        Additional data includes:
        - days_since_release: Number of days since the game was released.
        - (more will be added later)

        Args:
            raw_data (dict): The raw game data from all sources.
            
        Returns:
            dict: raw data with additional fields.
        """

        # calculate days since release
        if "release_date" in raw_data and raw_data["release_date"]:
            raw_data["days_since_release"] = (datetime.now() - datetime.strptime(raw_data["release_date"], "%b %d, %Y")).days
        else:
            raw_data["days_since_release"] = None

        return raw_data
    
    def _fetch_data(self, appid: str) -> dict:
        """Fetch game data and process additional fields.
        Args:
            appid (str): The appid of the game to fetch data for.
        
        Returns:
            dict: The processed game data with additional fields.
        """
        
        return self._additional_data(self._fetch_raw_data(appid))
    
    def get_game_recap(self, appid: str, return_as: Literal["json", "dict"] = "dict") -> dict | str:
        """Fetch game recap data.
        Game recap data includes game appid, name, release date, days since released, price and its currency, developer, publisher, genres, positive and negative reviews, review ratio, copies sold, estimated revenue, active players in the last 24 hours and in all time. 
        Args:
            appid (str): The appid of the game to fetch data for.
            return_as (str): Format to return the data, either 'json' or 'dict'. Default is 'dict'.
        
        Returns:
            dict | str: The game recap data from Steam and Gamalytic.
        """
        
        game_data = self._fetch_data(appid)
        
        labels_to_return = [
            "appid", "name", "release_date", "days_since_release", "price_currency", "price_final", "developer", 
            "publisher", "genres", "copies_sold", "estimated_revenue", "estimated_owners",
            "avg_playtime", "active_players_24h", "peak_active_players_all_time"
        ]

        # filter the game data to only include the labels we want
        filtered_data = {key: game_data[key] for key in labels_to_return if key in game_data}

        return json.dumps(filtered_data) if return_as == "json" else filtered_data
    
    def get_games_recap(self, appids: list[str]) -> pd.DataFrame:
        """Fetch game recap data for multiple appids.
        Args:
            appids (list[str]): List of appids to fetch data for.
        
        Returns:
            pd.DataFrame: DataFrame containing game recap data for all appids.
        """
        
        if len(appids) <= 1:
            raise ValueError("At least two appids are required to fetch data.")
        
        all_data = []

        for appid in appids:
            game_recap = self.get_game_recap(appid, return_as="dict")
            if game_recap:
                all_data.append(game_recap)
        
        return pd.DataFrame(all_data)
    
    def get_games_active_player_data(self, appids: list[str], fill_na_as: int = -1) -> pd.DataFrame:
        """Fetch active player data for multiple appids.
        Args:
            appids (list[str]): List of appids to fetch active player data for.
            fill_na_as (int): Value to fill NaN values in the DataFrame. Default is -1.
            
        Returns:
            pd.DataFrame: DataFrame containing active player data for all appids.
        """
        
        if len(appids) <= 1:
            raise ValueError("At least two appids are required.")
        
        all_months = set()
        all_data = []

        for appid in appids:
            active_player_data = sources.SteamCharts().get_active_player_data(appid)
            game_record = {
                "appid": appid,
                "name": active_player_data.get("name", ""),
            }

            if active_player_data.get("status", False):
                monthly_data = {
                    month["month"]: month["avg_players"]
                    for month in active_player_data.get("active_player_data", [])
                }
                game_record.update(monthly_data)
                all_months.update(monthly_data.keys())
            all_data.append(game_record)

        # sort the months chronologically
        sorted_months = sorted(all_months)

        # create a dataframe with all months as columns
        df = pd.DataFrame(all_data, columns=["appid", "name"] + sorted_months)

        # fill NaN values with the specified value
        df.fillna(fill_na_as, inplace=True)

        return df


        
    
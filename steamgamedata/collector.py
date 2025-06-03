import json
from typing import Literal
import pandas as pd
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

    def get_game_data(self, appid: str, return_as: Literal["json", "dict"] = "dict") -> dict | str:
        """Fetch game data from Steam and Gamalytic based on appid.
        Args:
            appid (str): The appid of the game to fetch data for.
            return_as (str): Format to return the data, either 'json' or 'dict'. Default is 'dict'.

        Returns:
            dict | str: The game data from Steam and Gamalytic.
        """
        
        # combine the data from all the sources
        steam = sources.Steam(region=self.region, language=self.language, api_key=self.steam_api_key)
        steamspy = sources.SteamSpy()
        gamalytic = sources.Gamalytic(api_key=self.gamalytic_api_key)
        steamcharts = sources.SteamCharts()

        result = {}

        for source in (steam, steamspy, gamalytic, steamcharts):
            data = source.get_game_data(appid)
            if data:
                result.update(data)
        
        return json.dumps(result) if return_as == "json" else result
    
    def get_games_data(self, appids: list[str]) -> pd.DataFrame:
        """Fetch game data for multiple appids.
        Args:
            appids (list[str]): List of appids to fetch data for.
            
        Returns:
            pd.DataFrame: DataFrame containing game data for all appids.
        """
        
        if len(appids) <= 1:
            raise ValueError("At least two appids are required to fetch data.")
        
        all_data = []

        for appid in appids:
            game_data = self.get_game_data(appid, return_as="dict")
            if game_data:
                all_data.append(game_data)
        
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

            # get the monthly data
            monthly_data = active_player_data.get("active_player_data", [])
            if not monthly_data:
                continue

            for month_data in monthly_data:
                all_months.add(month_data["month"])
                game_record.update({
                    month_data["month"]:month_data["avg_players"]
                })

            all_data.append(game_record)

        # sort the months chronologically
        sorted_months = sorted(all_months)

        # create a dataframe with all months as columns
        df = pd.DataFrame(all_data, columns=["appid", "name"] + sorted_months)

        # fill NaN values with the specified value
        df.fillna(fill_na_as, inplace=True)

        return df


        
    
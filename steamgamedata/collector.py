import json
from datetime import datetime
from typing import Any, Literal

import pandas as pd

import steamgamedata.sources as sources
from steamgamedata.utils.ratelimit import logged_rate_limited


class SteamGameData:
    def __init__(
        self,
        region: str = "us",
        language: str = "english",
        steam_api_key: str | None = None,
        gamalytic_api_key: str | None = None,
        calls: int = 60,
        period: int = 60,
    ) -> None:
        """Initialize the collector with an optional API key.
        Args:
            region (str): Region for the API request. Default is "us".
            language (str): Language for the API request. Default is "english".
            steam_api_key (str): Optional API key for Steam API.
            gamalytic_api_key (str): Optional API key for Gamalytic API.
            calls (int): Max number of API calls allowed per period. Default is 60.
            period (int): Time period in seconds for the rate limit. Default is 60.
        """
        self._region = region
        self._language = language
        self._steam_api_key = steam_api_key
        self._gamalytic_api_key = gamalytic_api_key
        self.calls = calls
        self.period = period

        self._init_sources()

    def _init_sources(self) -> None:
        """Initialize the sources with the current settings."""
        self.steam = sources.Steam(
            region=self.region, language=self.language, api_key=self.steam_api_key
        )
        self.steamspy = sources.SteamSpy()
        self.gamalytic = sources.Gamalytic(api_key=self.gamalytic_api_key)
        self.steamcharts = sources.SteamCharts()
        self.howlongtobeat = sources.HowLongToBeat()

    def id_based_sources(self) -> list[sources.BaseSource]:
        """Get the list of sources that uses appid to fetch data."""
        return [
            self.steam,
            self.steamspy,
            self.gamalytic,
            self.steamcharts,
        ]

    def name_based_sources(self) -> list[sources.BaseSource]:
        """Get the list of sources that uses game name to fetch data."""
        return [
            self.howlongtobeat,
        ]

    @property
    def region(self) -> str:
        return self._region

    @region.setter
    def region(self, value: str) -> None:
        if self._region != value:
            self._region = value
            self.steam.region = value

    @property
    def language(self) -> str:
        return self._language

    @language.setter
    def language(self, value: str) -> None:
        if self._language != value:
            self._language = value
            self.steam.language = value

    @property
    def steam_api_key(self) -> str | None:
        return self._steam_api_key

    @steam_api_key.setter
    def steam_api_key(self, value: str) -> None:
        if self._steam_api_key != value:
            self._steam_api_key = value
            self.steam.api_key = value

    @property
    def gamalytic_api_key(self) -> str | None:
        return self._gamalytic_api_key

    @gamalytic_api_key.setter
    def gamalytic_api_key(self, value: str) -> None:
        if self._gamalytic_api_key != value:
            self._gamalytic_api_key = value
            self.gamalytic.api_key = value

    def _fetch_raw_data(self, appid: str) -> dict[str, Any]:
        """Fetch game data from all sources based on appid.
        Args:
            appid (str): The appid of the game to fetch data for.

        Returns:
            dict: The combined game data from all sources.
        """
        result: dict[str, Any] = {}
        result["appid"] = appid  # add the appid to the result

        for source in self.id_based_sources():
            data = source.fetch(appid)
            if data.get("status", False):
                # if the status is true, update the result with the data
                result.update(data.get("data"))  # type: ignore[arg-type]

        # get the game name from the steam source
        game_name = result.get("name", None)
        if game_name:  # skip if the game name is None
            for source in self.name_based_sources():
                data = source.fetch(result["name"])
                if data.get("status", False):
                    # if the status is true, update the result with the data
                    result.update(data.get("data"))  # type: ignore[arg-type]

        return result

    def _additional_data(self, raw_data: dict[str, Any]) -> dict[str, Any]:
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
            raw_data["days_since_release"] = (
                datetime.now() - datetime.strptime(raw_data["release_date"], "%b %d, %Y")
            ).days
        else:
            raw_data["days_since_release"] = None

        return raw_data

    @logged_rate_limited()
    def _fetch_data(self, appid: str) -> dict[str, Any]:
        """Fetch game data and process additional fields.
        Args:
            appid (str): The appid of the game to fetch data for.

        Returns:
            dict: The processed game data with additional fields.
        """

        return self._additional_data(self._fetch_raw_data(appid))

    def get_game_recap(
        self, appid: str, return_as: Literal["json", "dict"] = "dict"
    ) -> dict[str, Any] | str:
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
            "appid",
            "name",
            "release_date",
            "days_since_release",
            "price_currency",
            "price_final",
            "developers",
            "publishers",
            "genres",
            "reviews",
            "copies_sold",
            "estimated_revenue",
            "estimated_owners",
            "main_story",
            "main_plus_sides",
            "completionist",
            "all_styles",
            "coop",
            "pvp",
            "avg_playtime",
            "active_player_24h",
            "peak_active_player_all_time",
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

    def get_games_active_player_data(
        self, appids: list[str], fill_na_as: int = -1
    ) -> pd.DataFrame:
        """Fetch active player data for multiple appids.
        Args:
            appids (list[str]): List of appids to fetch active player data for.
            fill_na_as (int): Value to fill NaN values in the DataFrame. Default is -1.

        Returns:
            pd.DataFrame: DataFrame containing active player data for all appids.
        """

        if len(appids) <= 1:
            raise ValueError("At least two appids are required.")

        all_months: set[str] = set()
        all_data = []

        for appid in appids:
            active_player_data = sources.SteamCharts().fetch_active_player_data(appid)
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

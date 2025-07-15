import json
from datetime import datetime
from typing import Any, Literal, NamedTuple

import pandas as pd

import steamgamedata.sources as sources
from steamgamedata.utils.ratelimit import logged_rate_limited


class SourceConfig(NamedTuple):
    source: sources.BaseSource
    fields: list[str]


class DataCollector:
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
        self._init_sources_config()

    def _init_sources(self) -> None:
        """Initialize the sources with the current settings."""
        self.steamreview = sources.SteamReview()
        self.steamstore = sources.SteamStore(
            region=self.region, language=self.language, api_key=self.steam_api_key
        )
        self.steamspy = sources.SteamSpy()
        self.gamalytic = sources.Gamalytic(api_key=self.gamalytic_api_key)
        self.steamcharts = sources.SteamCharts()
        self.howlongtobeat = sources.HowLongToBeat()

    def _init_sources_config(self) -> None:
        """Initialize sources config."""
        self._id_based_sources = [
            SourceConfig(
                self.steamstore,
                [
                    "steam_appid",
                    "name",
                    "developers",
                    "publishers",
                    "price_currency",
                    "price_initial",
                    "price_final",
                    "platforms",
                    "genres",
                    "metacritic_score",
                    "achievements",
                    "release_date",
                    "content_rating",
                ],
            ),
            SourceConfig(
                self.gamalytic,
                ["average_playtime", "copies_sold", "revenue", "total_revenue", "owners"],
            ),
            SourceConfig(self.steamspy, ["ccu", "tags"]),
            SourceConfig(
                self.steamcharts,
                ["active_player_24h", "peak_active_player_all_time", "monthly_active_player"],
            ),
            SourceConfig(
                self.steamreview,
                [
                    "review_score",
                    "review_score_desc",
                    "total_positive",
                    "total_negative",
                    "total_reviews",
                ],
            ),
        ]

        self._name_based_sources = [
            SourceConfig(
                self.howlongtobeat,
                [
                    "game_type",
                    "comp_main",
                    "comp_plus",
                    "comp_100",
                    "comp_all",
                    "comp_main_count",
                    "comp_plus_count",
                    "comp_100_count",
                    "comp_all_count",
                    "invested_co",
                    "invested_mp",
                    "invested_co_count",
                    "invested_mp_count",
                    "count_comp",
                    "count_speedrun",
                    "count_backlog",
                    "count_review",
                    "review_score",
                    "count_playing",
                    "count_retired",
                ],
            ),
        ]

    @property
    def id_based_sources(self) -> list[SourceConfig]:
        return self._id_based_sources

    @property
    def name_based_sources(self) -> list[SourceConfig]:
        return self._name_based_sources

    @property
    def region(self) -> str:
        return self._region

    @region.setter
    def region(self, value: str) -> None:
        if self._region != value:
            self._region = value
            self.steamstore.region = value

    @property
    def language(self) -> str:
        return self._language

    @language.setter
    def language(self, value: str) -> None:
        if self._language != value:
            self._language = value
            self.steamstore.language = value

    @property
    def steam_api_key(self) -> str | None:
        return self._steam_api_key

    @steam_api_key.setter
    def steam_api_key(self, value: str) -> None:
        if self._steam_api_key != value:
            self._steam_api_key = value
            self.steamstore.api_key = value

    @property
    def gamalytic_api_key(self) -> str | None:
        return self._gamalytic_api_key

    @gamalytic_api_key.setter
    def gamalytic_api_key(self, value: str) -> None:
        if self._gamalytic_api_key != value:
            self._gamalytic_api_key = value
            self.gamalytic.api_key = value

    def get_game_recap(
        self, steam_appid: str, return_as: Literal["json", "dict"] = "dict", verbose: bool = True
    ) -> dict[str, Any] | str | None:
        """Fetch game recap data.
        Game recap data includes game appid, name, release date, days since released, price and its currency, developer, publisher, genres, positive and negative reviews, review ratio, copies sold, estimated revenue, active players in the last 24 hours and in all time.
        Args:
            steam_appid (str): The appid of the game to fetch data for.
            return_as (str): Format to return the data, either 'json' or 'dict'. Default is 'dict'.
            verbose (bool): If True, will log the fetching process.

        Returns:
            dict | str: The game recap data.

        Behavior:
            - Returns None if ALL sources fail
            - Returns complete/partial data if ALL/ANY sources succeeds
        """

        game_data = self._fetch_data(steam_appid, verbose=verbose)

        if game_data:
            labels_to_return = [
                "steam_appid",
                "name",
                "release_date",
                "days_since_release",
                "price_currency",
                "price_initial",
                "price_final",
                "developers",
                "publishers",
                "genres",
                "tags",
                "total_positive",
                "total_negative",
                "total_reviews" "copies_sold",
                "revenue",
                "owners",
                "comp_main",
                "comp_plus",
                "comp_100",
                "comp_all",
                "invested_co",
                "invested_mp",
                "average_playtime",
                "active_player_24h",
                "peak_active_player_all_time",
            ]

            # filter the game data to only include the labels we want
            filtered_data = {key: game_data[key] for key in labels_to_return if key in game_data}

            return json.dumps(filtered_data) if return_as == "json" else filtered_data
        return None

    def get_game_detail(
        self, steam_appid: str, return_as: Literal["json", "dict"] = "dict", verbose: bool = True
    ) -> dict[str, Any] | str | None:
        """Fetch game detailed data.
        Args:
            steam_appid (str): The appid of the game to fetch data for.
            return_as (str): Format to return the data, either 'json' or 'dict'. Default to dict.
            verbose (bool): If True, will log the fetching process.

        Returns:
            dict | str: The game detailed data.

        Behavior:
            - Returns None if ALL sources fail
            - Returns complete/partial data if ALL/ANY sources succeeds
        """

        game_data = self._fetch_data(steam_appid, verbose=verbose)
        if game_data:
            return json.dumps(game_data) if return_as == "json" else game_data
        return None

    def get_games_recap(self, steam_appids: list[str], verbose: bool = True) -> pd.DataFrame:
        """Fetch game recap data for multiple appids and return it as pandas dataframe.
        Args:
            steam_appids (list[str]): List of appids to fetch data for.
            verbose (str): If True, will log the fetching process.

        Returns:
            pd.DataFrame: DataFrame containing game recap data for all appids.

        Behavior:
            - Raises ValueError if only provided with single steam_appid.
            - Returns complete/partial result if ALL/Any sources succeeds for each rows.
            - Rows will all source fail will be only have "steam_appid" column
        """

        if len(steam_appids) <= 1:
            raise ValueError(
                "At least two appids are required to fetch data. For singular search, use get_game_*"
            )

        all_data = []

        for appid in steam_appids:
            game_recap = self.get_game_recap(appid, return_as="dict", verbose=verbose)
            if game_recap is None:
                game_recap = {"steam_appid": appid}
            all_data.append(game_recap)

        return pd.DataFrame(all_data)

    def get_games_detail(self, steam_appids: list[str], verbose: bool = True) -> pd.DataFrame:
        """Fetch game detailed data for multiple appids and return it as pandas dataframe.

        Args:
            steam_appids (list[str]): List of appids to fetch data for.
            verbose (str): If True, will log the fetching process.

        Returns:
            pd.DataFrame: DataFrame containing game detailed data for all appids.

        Behavior:
            - Raises ValueError if only provided with single steam_appid.
            - Returns complete/partial result if ALL/Any sources succeeds.
        """

        if len(steam_appids) <= 1:
            raise ValueError(
                "At least two appids are required to fetch data. For singular search, use get_game_*"
            )

        all_data = []

        for appid in steam_appids:
            game_detail = self.get_game_detail(appid, return_as="dict", verbose=verbose)
            if game_detail is None:
                game_detail = {"steam_appid": appid}
            all_data.append(game_detail)

        return pd.DataFrame(all_data)

    def get_games_active_player_data(
        self, steam_appids: list[str], fill_na_as: int = -1, verbose: bool = True
    ) -> pd.DataFrame:
        """Fetch active player data for multiple appids.
        Args:
            appids (list[str]): List of appids to fetch active player data for.
            fill_na_as (int): Value to fill NaN values in the DataFrame. Default is -1.
            verbose (str): If True, will log the fetching process.

        Returns:
            pd.DataFrame: DataFrame containing active player data for all appids.
        """

        if len(steam_appids) <= 1:
            raise ValueError("At least two appids are required.")

        all_months: set[str] = set()
        all_data = []

        for appid in steam_appids:
            active_player_data = self.steamcharts.fetch(
                appid,
                verbose=verbose,
                selected_labels=["name", "peak_active_player_all_time", "monthly_active_player"],
            )
            game_record = {
                "steam_appid": appid,
            }

            if active_player_data.get("success"):
                monthly_data = {
                    month["month"]: month["average_players"]
                    for month in active_player_data["data"].get("monthly_active_player", [])
                }
                game_record.update(monthly_data)
                game_record.update(
                    {
                        "name": active_player_data["data"].get("name"),
                        "peak_active_player_all_time": active_player_data["data"].get(
                            "peak_active_player_all_time"
                        ),
                    }
                )
                all_months.update(monthly_data.keys())
            all_data.append(game_record)

        # sort the months chronologically
        sorted_months = sorted(all_months)

        # create a dataframe with all months as columns
        df = pd.DataFrame(
            all_data,
            columns=["steam_appid", "name", "peak_active_player_all_time"] + sorted_months,
        )

        # fill NaN values with the specified value
        df.fillna(fill_na_as, inplace=True)

        return df

    def get_game_review(self, steam_appid: str, verbose: bool = True) -> pd.DataFrame:
        reviews_data = self.steamreview.fetch(
            steam_appid=steam_appid,
            verbose=verbose,
            filter="recent",
            language="all",
            review_type="all",
            purchase_type="all",
            mode="review",
        )

        if reviews_data["success"]:
            return pd.DataFrame(reviews_data["data"]["reviews"])
        return pd.DataFrame([])

    @logged_rate_limited()
    def _fetch_data(self, steam_appid: str, verbose: bool = True) -> dict[str, Any] | None:
        """Fetch game data and process additional fields (if the required fields exist).

        Args:
            appid (str): The appid of the game to fetch data for.
            verbose (str): If true, will log the fetching process.

        Returns:
            dict: The processed game data with additional fields.
        """

        raw_data = self._fetch_raw_data(steam_appid, verbose)

        if raw_data:
            return self._additional_data(raw_data)
        return None

    def _fetch_raw_data(self, steam_appid: str, verbose: bool = True) -> dict[str, Any]:
        """Fetch game data from all sources based on appid.
        Args:
            steam_appid (str): The appid of the game to fetch data for.
            verbose (bool: If True, will log the fetching process

        Returns:
            dict: The combined game data from all sources.
        """
        raw_data: dict[str, Any] = {}

        for config in self.id_based_sources:
            source_data = config.source.fetch(steam_appid, verbose=verbose)
            if source_data["success"]:
                raw_data.update({key: source_data["data"][key] for key in config.fields})

        # if the game name doesn't exist, then the game is not available
        game_name = raw_data.get("name", None)
        if game_name:
            for config in self.name_based_sources:
                source_data = config.source.fetch(game_name, verbose=verbose)
                if source_data["success"]:
                    raw_data.update({key: source_data["data"][key] for key in config.fields})

        return raw_data

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
        self._process_release_date(raw_data)

        return raw_data

    def _process_release_date(self, raw_data: dict[str, Any]) -> None:
        """Calculate days_since_release from the raw data."""
        date_format = "%b %d, %Y"
        if raw_data.get("release_date", None):
            raw_data["days_since_release"] = (
                datetime.now() - datetime.strptime(raw_data["release_date"], date_format)
            ).days

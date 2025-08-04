import time
from typing import Any, Literal, NamedTuple

import pandas as pd

import steamgamedata.sources as sources
from steamgamedata.model.game_data import GameDataModel
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
        self.steamachievements = sources.SteamAchievements(api_key=self.steam_api_key)
        self.steamuser = sources.SteamUser(api_key=self.steam_api_key)

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
                    "release_date",
                    "content_rating",
                ],
            ),
            SourceConfig(
                self.gamalytic,
                ["average_playtime_h", "copies_sold", "estimated_revenue", "owners", "languages"],
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
            SourceConfig(
                self.steamachievements,
                [
                    "achievements_count",
                    "achievements_percentage_average",
                    "achievements_list",
                ],
            ),
        ]

        self._name_based_sources = [
            SourceConfig(
                self.howlongtobeat,
                [
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
            self.steamachievements.api_key = value
            self.steamuser.api_key = value

    @property
    def gamalytic_api_key(self) -> str | None:
        return self._gamalytic_api_key

    @gamalytic_api_key.setter
    def gamalytic_api_key(self, value: str) -> None:
        if self._gamalytic_api_key != value:
            self._gamalytic_api_key = value
            self.gamalytic.api_key = value

    def get_user_data(
        self,
        steamids: str | list[str],
        include_free_games: bool = True,
        return_as: Literal["list", "dataframe"] = "dataframe",
        verbose: bool = True,
    ) -> list[dict[str, Any]] | pd.DataFrame:
        """Fetch user data from provided steamids.
        Args:
            steamids (str | list[str]): Either a single or a list of 64bit SteamIDs
            include_free_games (bool): If True, will include free games when fetching users' owned games list. Default to True.
            return_as (str): Return format, "list" for list of dicts, "dataframe" for pandas DataFrame. Default to "dataframe".
            verbose (bool): If True, will log the fetching process.
        """
        steamid_list = (
            [steamids] if isinstance(steamids, str) or isinstance(steamids, int) else steamids
        )

        results = []

        for steamid in steamid_list:
            fetch_result = self.steamuser.fetch(
                steamid=steamid, include_free_games=include_free_games, verbose=verbose
            )
            if fetch_result["success"]:
                user_data = fetch_result["data"]
                results.append(user_data)
            else:
                user_data = {"steamid": steamid}
                results.append(user_data)

            time.sleep(0.25)  # internal sleep to prevent over-calling

        if return_as == "dataframe":
            return pd.DataFrame(results)

        return results

    def get_games_data(
        self, steam_appids: str | list[str], recap: bool = False, verbose: bool = True
    ) -> list[dict[str, Any]]:
        """Fetch game recap data.
        Game recap data includes game appid, name, release date, days since released, price and its currency, developer, publisher, genres, positive and negative reviews, review ratio, copies sold, estimated revenue, active players in the last 24 hours and in all time.
        Args:
            steam_appids (str): steam_appid of the game(s) to fetch data for.
            recap (bool): If True, will return the recap data (for reference: check _RECAP_LABELS).
            verbose (bool): If True, will log the fetching process.

        Returns:
            list[dict[str, Any]]: List of games recap data.

        Behavior:
            - Returns None if ALL sources fail
            - Returns complete/partial data if ALL/ANY sources succeeds
        """

        if not steam_appids:
            return []

        if isinstance(steam_appids, (str, int)):
            steam_appids = [steam_appids]

        result = []
        for steam_appid in steam_appids:
            game_data = self._fetch_raw_data(steam_appid, verbose=verbose)
            game_data = game_data.get_recap() if recap else game_data.model_dump()

            result.append(game_data)

        return result

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

    def get_game_review(
        self, steam_appid: str, verbose: bool = True, review_only: bool = True
    ) -> pd.DataFrame:
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
            if review_only:
                return pd.DataFrame(reviews_data["data"]["reviews"])
            else:
                return pd.DataFrame([reviews_data["data"]])

        return pd.DataFrame([])

    @logged_rate_limited()
    def _fetch_raw_data(self, steam_appid: str, verbose: bool = True) -> "GameDataModel":
        """Fetch game data from all sources based on appid.
        Args:
            steam_appid (str): The appid of the game to fetch data for.
            verbose (bool: If True, will log the fetching process

        Returns:
            dict: The combined game data from all sources.
        """
        raw_data: dict[str, Any] = {"steam_appid": str(steam_appid)}

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

        return GameDataModel(**raw_data)

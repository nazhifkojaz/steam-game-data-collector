from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup

from steamgamedata.sources.base import BaseSource, SourceResult
from steamgamedata.utils.ratelimit import logged_rate_limited


class SteamCharts(BaseSource):
    """SteamCharts source for fetching active player data from SteamCharts website."""

    def __init__(self) -> None:
        """Initialize the SteamCharts source."""
        self.base_url = "https://steamcharts.com/app/"

    def _make_request(self, appid: str) -> BeautifulSoup | None:
        """Perform a GET request to the SteamCharts API and return the BeautifulSoup object.
        Args:
            appid (str): The appid of the game to fetch data for.

        Returns:
            BeautifulSoup: The BeautifulSoup object containing the response content.
        """
        url = f"{self.base_url}{appid}"

        # Define headers to simulate a browser request
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.6312.86 Safari/537.36"
            )
        }

        response = requests.get(url, headers=headers)
        response.encoding = "utf-8"
        if response.status_code != 200:
            return None

        return BeautifulSoup(response.text, "html.parser")

    @logged_rate_limited(calls=60, period=60)  # web scrape -> 60 requests per minute to be polite
    def fetch(self, appid: str, verbose: bool = True) -> SourceResult:
        """Fetch active player data from SteamCharts based on its appid.
        Args:
            appid (str): The appid of the game to fetch data for.

        Returns:
            SourceResult: A dictionary containing the status, appid, name, active player data, and any error message if applicable.
        """

        self._log(
            f"Fetching active player data for appid {appid}.",
            level="info",
            verbose=verbose,
        )

        result: SourceResult = {"success": False, "data": None, "error": ""}

        soup = self._make_request(appid)

        if not soup:
            # raise ValueError("Failed to fetch data from SteamCharts.")
            result["error"] = "Failed to fetch data from SteamCharts."
            self._log(
                result["error"],
                level="error",
                verbose=verbose,
            )
            return result

        # Get the part where it contains the 24 hour peak and all time peak data
        peak_data = soup.find_all("div", class_="app-stat")
        if not peak_data:
            # raise ValueError("Failed to parse SteamCharts data. No peak data found.")
            result["error"] = "Failed to parse SteamCharts data. No peak data found."
            self._log(
                result["error"],
                level="error",
                verbose=verbose,
            )
            return result

        result["success"] = True
        result["data"] = {
            "active_player_24h": int(peak_data[1].find("span", class_="num").text),  # type: ignore[union-attr,call-arg]
            "peak_active_player_all_time": int(peak_data[2].find("span", class_="num").text),  # type: ignore[union-attr,call-arg]
        }
        return result

    @logged_rate_limited(calls=60, period=60)  # web scrape -> 60 requests per minute to be polite
    def fetch_active_player_data(self, appid: str, verbose: bool = True) -> dict[str, Any]:
        """Fetch active player data from SteamChart based on its appid.
        Args:
            appid (str): The appid of the game to fetch data for.

        Returns:
            dict: The result containing the status, appid, name, active player data, and any error message if applicable.
        """

        self._log(
            f"Fetching active player data for appid {appid}.",
            level="info",
            verbose=verbose,
        )

        result: dict[str, Any] = {
            "success": False,
            "appid": appid,
            "name": None,
            "active_player_data": [],
            "error": None,
        }

        soup = self._make_request(appid)

        if not soup:
            # raise ValueError("Failed to fetch data from SteamCharts.")
            result["error"] = "Failed to fetch data."
            self._log(
                result["error"],
                level="error",
                verbose=verbose,
            )
            return result

        # get the game name, if they don't have a game name, add an error message.
        game_name = soup.find("h1", id="app-title")
        if not game_name:
            # raise ValueError("Failed to parse SteamCharts data. No game name found.")
            result["error"] = "Failed to parse SteamCharts data. No game name found."
        else:
            # if we have a game name, set the game name in the result
            result["name"] = game_name.text

        # get the player data table, if it also doesn't exist, extend the error message and return the empty result
        player_data_table = soup.find("table", class_="common-table")
        if not player_data_table:
            # raise ValueError("Failed to parse SteamCharts data. No player data table found.")
            result["error"] = (
                "Failed to parse SteamCharts data. No player data table found."
                if not result["error"]
                else result["error"] + " No player data table found."
            )

            self._log(
                result["error"],
                level="error",
                verbose=verbose,
            )
            return result

        # if we have a player data table, set the status to True
        result["success"] = True

        # get the player data rows, skipping the first two header rows
        player_data_rows = player_data_table.find_all("tr")[2:]  # type: ignore[attr-defined]

        for row in player_data_rows:
            cols = [col.text.strip() for col in row.find_all("td")]

            month, avg_players, gain, percentage_gain, peak_players = cols[:5]

            result["active_player_data"].append(
                {
                    "month": datetime.strptime(month, "%B %Y").strftime("%Y-%m"),
                    "avg_players": float(avg_players.replace(",", "")),
                    "gain": float(gain.replace(",", "")) if gain not in ("-", "") else None,
                    "percentage_gain": (
                        float(percentage_gain.replace("%", "").replace(",", "").strip())
                        if percentage_gain not in ("-", "")
                        else 0
                    ),
                    "peak_players": float(peak_players.replace(",", "")),
                }
            )

        return result

from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from steamgamedata.sources.base import BaseSource, SourceResult, SuccessResult
from steamgamedata.utils.ratelimit import logged_rate_limited

_STEAMCHARTS_LABELS = (
    "steam_appid",
    "name",
    "active_player_24h",
    "peak_active_player_all_time",
    "monthly_active_player",
)


class SteamCharts(BaseSource):
    """SteamCharts source for fetching active player data from SteamCharts website."""

    _valid_labels: tuple[str, ...] = _STEAMCHARTS_LABELS
    _valid_labels_set: frozenset[str] = frozenset(_STEAMCHARTS_LABELS)
    _base_url = "https://steamcharts.com/app"

    def __init__(self) -> None:
        """Initialize the SteamCharts source."""
        super().__init__()

    @logged_rate_limited(calls=60, period=60)  # web scrape -> 60 requests per minute to be polite
    def fetch(
        self, steam_appid: str, verbose: bool = True, selected_labels: list[str] | None = None
    ) -> SourceResult:
        """Fetch active player data from SteamCharts based on its appid.
        Args:
            steam_appid (str): The steam appid of the game to fetch data for.
            verbose (bool): If True, will log the fetching process.
            selected_labels (list[str] | None): A list of labels to filter the data. If None, all labels will be used.

        Returns:
            SourceResult: A dictionary containing the status, data, or any error message if applicable.

        Behavior:
            - If successful, will return a SuccessResult with the data based on the selected_labels or _valid_labels.
            - If unsuccessful, will return an error message indicating the failure reason.
            - monthly_active_player labels will be returned as empty list if the game have no monthly active user data (for newly released games)
        """

        self.logger.log(
            f"Fetching active player data for appid {steam_appid}.",
            level="info",
            verbose=verbose,
        )

        # Make sure steam_appid is string
        steam_appid = str(steam_appid)

        # Prepare the headers and make the request to steamchart
        response = self._make_request(endpoint=steam_appid, headers=self._get_request_header())

        if response.status_code != 200:
            return self._build_error_result(
                f"Failed to fetch data with status code: {response.status_code}", verbose=verbose
            )

        soup = BeautifulSoup(response.text, "html.parser")

        # check the name part
        game_name = soup.find("h1", id="app-title")
        if not game_name:
            return self._build_error_result(
                "Failed to parse data, game name is not found.", verbose=verbose
            )

        # check stats data
        peak_data = soup.find_all("div", class_="app-stat")
        if len(peak_data) < 3:
            return self._build_error_result(
                "Failed to parse data, expecting atleast 3 'app-stat' divs.", verbose=verbose
            )
        for data in peak_data:
            if not data.find("span", class_="num"):  # type: ignore[union-attr, call-arg]
                return self._build_error_result(
                    "Failed to parse data, incorrect app-stat structure.", verbose=verbose
                )

        active_player_data_table = soup.find("table", class_="common-table")
        if not active_player_data_table:
            return self._build_error_result(
                "Failed to parse data, active player data table is not found.", verbose=verbose
            )

        # Skip the "last 30 days" row
        player_data_rows = active_player_data_table.find_all("tr")[2:]  # type: ignore[attr-defined]

        # check the cols whether the table structure is correct (only when the player_data_rows is populated)
        if len(player_data_rows) > 0:
            cols = [col.get_text(strip=True) for col in player_data_rows[0].find_all("td")]
            if len(cols) < 5:
                return self._build_error_result(
                    "Failed to parse data, the structure of player data table is incorrect.",
                    verbose=verbose,
                )

        data_packed = {
            "steam_appid": steam_appid,
            **self._transform_data(
                {
                    "game_name": game_name,
                    "peak_data": peak_data,
                    "player_data_rows": player_data_rows,
                }
            ),
        }

        if selected_labels:
            data_packed = {
                label: data_packed[label]
                for label in self._filter_valid_labels(selected_labels=selected_labels)
            }

        return SuccessResult(success=True, data=data_packed)

    def _transform_data(self, data: dict[str, Any]) -> dict[str, Any]:
        game_name_text = data["game_name"].get_text()
        active_24h = data["peak_data"][1].span.get_text()
        peak_active = data["peak_data"][2].span.get_text()

        monthly_active_player = []
        for row in data.get("player_data_rows", []):
            cols = [col.get_text(strip=True) for col in row.find_all("td")]
            month, avg_players, gain, percentage_gain, peak_players = cols[:5]

            monthly_active_player.append(
                {
                    "month": datetime.strptime(month, "%B %Y").strftime("%Y-%m"),
                    "average_players": float(avg_players.replace(",", "")),
                    "gain": float(gain.replace(",", "")) if gain not in ("-", "") else None,
                    "percentage_gain": (
                        float(percentage_gain.replace("%", "").replace(",", "").strip())
                        if percentage_gain not in ("-", "")
                        else 0
                    ),
                    "peak_players": float(peak_players.replace(",", "")),
                }
            )

        return {
            "name": game_name_text,
            "active_player_24h": int(active_24h) if active_24h else None,
            "peak_active_player_all_time": int(peak_active) if peak_active else None,
            "monthly_active_player": monthly_active_player,
        }

    def _get_request_header(self) -> dict[str, Any]:
        """Get headers for the request."""
        ua = UserAgent()
        headers = {"User-Agent": ua.random}
        return headers

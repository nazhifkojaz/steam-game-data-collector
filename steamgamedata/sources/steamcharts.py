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
            return self._build_error_result("Failed to fetch data.", verbose=verbose)

        return self._transform_data(steam_appid=steam_appid, data=response.text, verbose=verbose)

    def _transform_data(self, steam_appid: str, data: str, verbose: bool = True) -> SourceResult:  # type: ignore[override]
        soup = BeautifulSoup(data, "html.parser")

        # Get the name part
        game_name = soup.find("h1", id="app-title")
        if not game_name:
            return self._build_error_result(
                "Failed to parse data, game name is not found.", verbose=verbose
            )

        # Get stats data
        peak_data = soup.find_all("div", class_="app-stat")
        if not peak_data:
            return self._build_error_result(
                "Failed to parse data, stats data is not found.", verbose=verbose
            )
        active_player_24h = int(peak_data[1].find("span", class_="num").text)  # type: ignore[union-attr,call-arg]
        peak_active_player_all_time = int(peak_data[2].find("span", class_="num").text)  # type: ignore[union-attr,call-arg]

        # get month active data
        active_player_data_table = soup.find("table", class_="common-table")
        if not active_player_data_table:
            return self._build_error_result(
                "Failed to parse data, active player data table is not found.", verbose=verbose
            )

        # Skip the "last 30 days" row
        player_data_rows = active_player_data_table.find_all("tr")[2:]  # type: ignore[attr-defined]
        monthly_active_player = []

        for row in player_data_rows:
            cols = [col.text.strip() for col in row.find_all("td")]

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

        return SuccessResult(
            success=True,
            data={
                "steam_appid": steam_appid,
                "name": game_name.text,
                "active_player_24h": active_player_24h,
                "peak_active_player_all_time": peak_active_player_all_time,
                "monthly_active_player": monthly_active_player,
            },
        )

    def _get_request_header(self) -> dict[str, Any]:
        """Get headers for the request."""
        ua = UserAgent()
        headers = {"User-Agent": ua.random}
        return headers

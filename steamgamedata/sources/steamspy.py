import requests

from steamgamedata.sources.base import BaseSource, SourceResult
from steamgamedata.utils.ratelimit import logged_rate_limited


class SteamSpy(BaseSource):
    def __init__(self) -> None:
        """Initialize the SteamSpy with the base URL."""
        self.base_url = "https://steamspy.com/api.php"

    @logged_rate_limited(calls=60, period=60)  # 60 requests per minute.
    def fetch(self, appid: str, verbose: bool = True) -> SourceResult:
        """Fetch game data from SteamSpy based on appid.
        Args:
            appid (str): The appid of the game to fetch data for.

        Returns:
            SourceResult: A dictionary containing the status, data, and any error message if applicable.
        """

        self._log(
            f"Fetching data for appid {appid}.",
            level="info",
            verbose=verbose,
        )

        result: SourceResult = {"success": False, "data": None, "error": ""}

        url = f"{self.base_url}?request=appdetails&appid={appid}"
        response = requests.get(url)
        if response.status_code != 200:
            # raise ConnectionError(f"Failed to connect to SteamSpy API. Status code: {response.status_code}")
            result["error"] = (
                f"Failed to connect to SteamSpy API. Status code: {response.status_code}"
            )
            self._log(
                result["error"],
                level="error",
                verbose=verbose,
            )
            return result

        data = response.json()
        if not data.get("name"):
            # raise ValueError(f"Data for appid {appid} not found in SteamSpy.")
            result["error"] = f"Data for appid {appid} not found."
            self._log(
                result["error"],
                level="error",
                verbose=verbose,
            )
            return result

        result["success"] = True
        result["data"] = {
            "appid": data.get("appid", appid),
            # "name": data.get("name", None),
            "average_forever": data.get("average_forever", None),
            "average_2weeks": data.get("average_2weeks", None),
        }

        return result

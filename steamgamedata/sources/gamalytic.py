import requests

from steamgamedata.sources.base import BaseSource, SourceResult
from steamgamedata.utils.ratelimit import logged_rate_limited


class Gamalytic(BaseSource):
    def __init__(self, api_key: str | None = None) -> None:
        """Initialize the Gamalytic with an optional API key.
        Args:
            api_key (str): Optional API key for Gamalytic API.
        """
        self._api_key = api_key
        self.base_url = "https://api.gamalytic.com/"

    @property
    def api_key(self) -> str | None:
        return self._api_key

    @api_key.setter
    def api_key(self, value: str) -> None:
        if self._api_key != value:
            self._api_key = value

    @logged_rate_limited(calls=500, period=24 * 60 * 60)  # 500 requests per day
    def fetch(self, appid: str, verbose: bool = True) -> SourceResult:
        """Fetch game data from Gamalytic based on appid.
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

        result: SourceResult = {"status": False, "data": None, "error": ""}

        url = f"{self.base_url}game/{appid}"

        # will be used later once I have an API key to test with
        # if self.api_key:
        #     url += f"&api_key={self.api_key}"

        response = requests.get(url)
        if response.status_code == 404:
            # raise ValueError(f"Game with appid {appid} not found.")
            result["error"] = f"Game with appid {appid} not found."
            self._log(
                result["error"],
                level="error",
                verbose=verbose,
            )
            return result
        elif response.status_code != 200:
            # raise ConnectionError(f"Failed to connect to Gamalytic API. Status code: {response.status_code}")
            result["error"] = f"Failed to connect to API. Status code: {response.status_code}"
            self._log(
                result["error"],
                level="error",
                verbose=verbose,
            )
            return result

        data = response.json()

        result["status"] = True
        result["data"] = {
            "appid": data.get("steamId", appid),
            # "name": data.get("name", None),
            "reviews": data.get("reviewsSteam", None),
            # "reviews_score": data.get("reviewScore", None),
            "followers": data.get("followers", None),
            "avg_playtime": data.get("avgPlaytime", None),
            "achievements": data.get("achievements", None),
            "languages": data.get("languages", None),
            # "developers": data.get("developers", None),
            # "publishers": data.get("publishers", None),
            "copies_sold": data.get("copiesSold", None),
            "estimated_revenue": data.get("revenue", None),
            "estimated_owners": data.get("owners", None),
        }

        return result

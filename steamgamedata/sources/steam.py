import requests

from steamgamedata.sources.base import BaseSource, SourceResult


class Steam(BaseSource):
    def __init__(self, region: str = "us", language: str = "english", api_key: str | None = None):
        """Initialize the Steam with an optional API key.
        Args:
            region (str): Region for the game data. Default is "us".
            language (str): Language for the API request. Default is "english".
            api_key (str): Optional API key for Steam API.
        """
        self._region = region
        self._language = language
        self._api_key = api_key

    @property
    def region(self) -> str:
        """Get the region for the Steam API."""
        return self._region

    @region.setter
    def region(self, value: str) -> None:
        """Set the region for the Steam API.
        Args:
            value (str): Region for the API request.
        """
        if self._region != value:
            self._region = value

    @property
    def language(self) -> str:
        """Get the language for the Steam API."""
        return self._language

    @language.setter
    def language(self, value: str) -> None:
        """Set the language for the Steam API.
        Args:
            value (str): Language for the API request.
        """
        if self._language != value:
            self._language = value

    @property
    def api_key(self) -> str | None:
        """Get the API key for the Steam API."""
        return self._api_key

    @api_key.setter
    def api_key(self, value: str) -> None:
        """Set the API key for the Steam API.
        Args:
            value (str): API key for Steam API.
        """
        if self._api_key != value:
            self._api_key = value

    def fetch(self, appid: str, verbose: bool = True) -> SourceResult:
        """Fetch game data from steam store based on appid.
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

        appid = str(appid)  # ensure appid is a string
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc={self.region}&l={self.language}"

        response = requests.get(url)

        if response.status_code != 200:
            # raise ConnectionError(f"Failed to connect to Steam store API. Status code: {response.status_code}")
            result["error"] = (
                f"Failed to connect to Steam store API. Status code: {response.status_code}"
            )
            self._log(
                result["error"],
                level="error",
                verbose=verbose,
            )
            return result

        data = response.json()

        # check if the response contains the expected data
        if appid not in data or not data[appid]["success"]:
            # raise ValueError(f"Failed to fetch data for appid {appid} or appid is not available in the specified region/language.")
            result["error"] = (
                f"Failed to fetch data for appid {appid} or appid is not available in the specified region/language."
            )
            self._log(
                result["error"],
                level="error",
                verbose=verbose,
            )
            return result

        game_data = data[appid]["data"]
        result["status"] = True
        result["data"] = {
            "appid": appid,
            "name": game_data.get("name", None),
            "release_date": game_data.get("release_date", {}).get("date", None),
            "developers": game_data.get("developers", None),
            "publishers": game_data.get("publishers", None),
            "genres": [genre["description"] for genre in game_data.get("genres", [])],
            "platforms": [
                platform
                for platform, is_supported in game_data.get("platforms", {}).items()
                if is_supported
            ],
            "achievements": game_data.get("achievements", {}).get("total", None),
            "price_currency": game_data.get("price_overview", {}).get("currency", None),
            "price_initial": (
                game_data.get("price_overview", {}).get("initial", None) / 100
                if game_data.get("price_overview")
                else None
            ),
            "price_final": (
                game_data.get("price_overview", {}).get("final", None) / 100
                if game_data.get("price_overview")
                else None
            ),
            "content_rating": [
                {"rating_type": rating_type, "rating": rating["rating"]}
                for rating_type, rating in game_data.get("ratings", {}).items()
            ],
        }
        return result

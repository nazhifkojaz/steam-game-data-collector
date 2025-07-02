from typing import Any

from steamgamedata.sources.base import BaseSource, SourceResult, SuccessResult
from steamgamedata.utils.ratelimit import logged_rate_limited

_STEAM_LABELS = (
    "steam_appid",
    "name",
    "type",
    "is_free",
    "developers",
    "publishers",
    "price_currency",
    "price_initial",
    "price_final",
    "platforms",
    "categories",
    "genres",
    "metacritic_score",
    "recommendations",
    "achievements",
    "is_coming_soon",
    "release_date",
    "content_rating",
)


class SteamStore(BaseSource):
    _valid_labels: tuple[str, ...] = _STEAM_LABELS
    _valid_labels_set: frozenset[str] = frozenset(_STEAM_LABELS)
    _base_url = "https://store.steampowered.com/api/appdetails"

    def __init__(self, region: str = "us", language: str = "english", api_key: str | None = None):
        """Initialize the Steam with an optional API key.
        Args:
            region (str): Region for the game data. Default is "us".
            language (str): Language for the API request. Default is "english".
            api_key (str): Optional API key for Steam API.
        """
        super().__init__()
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

    @logged_rate_limited(
        calls=60, period=60
    )  # no official rate limit, but 60 requests per minute is a good practice.
    def fetch(
        self, steam_appid: str, verbose: bool = True, selected_labels: list[str] | None = None
    ) -> SourceResult:
        """Fetch game data from steam store based on appid.
        Args:
            steam_appid (str): The steam appid of the game to fetch data for.
            verbose (bool): If True, will log the fetching process.
            selected_labels (list[str] | None): A list of labels to filter the data. If None, all labels will be used.

        Returns:
            SourceResult: A dictionary containing the status, data, or any error message if applicable.
        """

        self._log(
            f"Fetching data for appid {steam_appid}.",
            level="info",
            verbose=verbose,
        )

        # ensure steam_appid is string
        steam_appid = str(steam_appid)

        # Make the request to steam store API
        params = {"appid": steam_appid, "cc": self.region, "l": self.language}
        response = self._make_request(params=params)

        if response.status_code != 200:
            self._build_error_result(
                f"Failed to connect to API. Status code: {response.status_code}.", verbose=verbose
            )

        data = response.json()

        # check if the response contains the expected data
        if steam_appid not in data or not data[steam_appid]["success"]:
            # raise ValueError(f"Failed to fetch data for appid {appid} or appid is not available in the specified region/language.")
            self._build_error_result(
                f"Failed to fetch data for appid {steam_appid}, or appid is not available in the specified region ({self.region}) or language ({self.language}).",
                verbose=verbose,
            )

        data_packed = self._transform_data(data[steam_appid]["data"])

        if selected_labels:
            data_packed = {
                label: data_packed[label] for label in self._filter_valid_labels(selected_labels)
            }

        return SuccessResult(success=True, data=data_packed)

    def _transform_data(self, data: dict[str, Any]) -> dict[str, Any]:
        # repack / process the data if needed
        price_overview = data.get("price_overview", {})
        release_date = data.get("release_date", {})
        platforms = data.get("platforms", {})
        genres = data.get("genres", [])
        categories = data.get("categories", [])
        ratings = data.get("ratings", {})

        return {  # Default to None
            "appid": data.get("steam_appid", None),
            "name": data.get("name", None),
            "type": data.get("type", None),
            "is_coming_soon": release_date.get("coming_soon", None),
            "release_date": release_date.get("date", None),
            "is_free": data.get("is_free", None),
            "price_currency": price_overview.get("currency", None),
            "price_initial": (
                price_overview.get("initial") / 100
                if price_overview.get("initial", None) is not None
                else None
            ),
            "price_final": (
                price_overview.get("final") / 100
                if price_overview.get("final", None) is not None
                else None
            ),
            "developers": data.get("developers", None),
            "publishers": data.get("publishers", None),
            "platforms": [
                platform for platform, is_supported in platforms.items() if is_supported
            ],
            "categories": [category["description"] for category in categories],
            "genres": [genre["description"] for genre in genres],
            "metacritic_score": data.get("metacritic", {}).get("score", None),
            "recommendations": data.get("recommendations", {}).get("total", None),
            "achievements": data.get("achievements", {}).get("total", None),
            "content_rating": [
                {"rating_type": rating_type, "rating": rating["rating"]}
                for rating_type, rating in ratings.items()
            ],
        }

import requests

class Gamalytic:
    def __init__(self, api_key: str | None = None):
        """Initialize the Gamalytic with an optional API key.
        Args:
            api_key (str): Optional API key for Gamalytic API.
        """
        self.api_key = api_key
        self.base_url = "https://api.gamalytic.com/"

    def set_api_key(self, api_key: str):
        """Set the API key for the Gamalytic API.
        Args:
            api_key (str): API key for Gamalytic API.
        """
        self.api_key = api_key

    def get_game_data(self, appid: str) -> dict:
        """Fetch game data from Gamalytic based on appid.
        Args:
            appid (str): The appid of the game to fetch data for.

        Returns:
            dict: The game data from Gamalytic.
        """

        url = f"{self.base_url}game/{appid}"

        # will be used later once I have an API key to test with
        # if self.api_key:
        #     url += f"&api_key={self.api_key}"

        response = requests.get(url)
        if response.status_code == 404:
            raise ValueError(f"Game with appid {appid} not found.")
        elif response.status_code != 200:
            raise ConnectionError(f"Failed to connect to Gamalytic API. Status code: {response.status_code}")
        
        data = response.json()

        return {
            "appid": data.get("steamId", appid),
            "name": data.get("name", None),
            "reviews": data.get("reviews", None),
            "reviews_score": data.get("reviewScore", None),
            "followers": data.get("followers", None),
            "avg_playtime": data.get("avgPlaytime", None),
            "achievements": data.get("achievements", None),
            "languages": data.get("languages", None),
            "developers": data.get("developers", None),
            "publishers": data.get("publishers", None),
            "copies_sold": data.get("copiesSold", None),
            "estimated_revenue": data.get("revenue", None),
            "estimated_owners": data.get("owners", None)
        }
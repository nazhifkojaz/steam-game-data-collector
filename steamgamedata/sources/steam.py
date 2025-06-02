import requests

class Steam:
    def __init__(self, region: str = "us", language: str = "english", api_key: str | None = None):
        """Initialize the Steam with an optional API key.
        Args:
            region (str): Region for the game data. Default is "us".
            language (str): Language for the API request. Default is "english".
            api_key (str): Optional API key for Steam API.
        """
        self.region = region
        self.language = language
        self.api_key = api_key

    def set_region(self, region: str):
        """Set the region for the Steam API.
        Args:
            region (str): Region for the game data.
        """
        self.region = region
    
    def set_language(self, language: str):
        """Set the language for the Steam API.
        Args:
            language (str): Language for the API request.
        """
        self.language = language
        
    def set_api_key(self, api_key: str):
        """Set the API key for the Steam API.
        Args:
            api_key (str): API key for Steam API.
        """
        self.api_key = api_key

    
    def get_game_data(self, appid: str) -> dict:
        """Fetch game data from steam store based on appid.
        Args:
            appid (str): The appid of the game to fetch data for.
            region (str): Region for the game data. Default is "us".
            language (str): Language for the API request. Default is "english".

        Returns:
            dict: The game data from the Steam store.
        """

        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc={self.region}&l={self.language}"
        response = requests.get(url)
        if response.status_code != 200:
            raise ConnectionError(f"Failed to connect to Steam store API. Status code: {response.status_code}")
        
        data = response.json()

        # check if the response contains the expected data
        if appid not in data or not data[appid]["success"]:
            raise ValueError(f"Failed to fetch data for appid {appid} or appid is not available in the specified region/language.")
        
        game_data = data[appid]

        return {
            "appid": appid,
            "name": game_data.get("data", {}).get("name", None),
            "release_date": game_data.get("data", {}).get("release_date", {}).get("date", None),
            "developer": game_data.get("data", {}).get("developers", None),
            "publisher": game_data.get("data", {}).get("publishers", None),
            "genres": [genre["description"] for genre in game_data.get("data", {}).get("genres", [])],
            "platforms": [platform for platform in game_data.get("data", {}).get("platforms", {}) if game_data["data"]["platforms"][platform]],
            "achievements": game_data.get("data", {}).get("achievements", {}).get("total", None),
            "price_currency": game_data.get("data", {}).get("price_overview", {}).get("currency", None),
            "price_initial": game_data.get("data", {}).get("price_overview", {}).get("initial", None) / 100 if game_data.get("data", {}).get("price_overview") else None,
            "price_final": game_data.get("data", {}).get("price_overview", {}).get("final", None) / 100 if game_data.get("data", {}).get("price_overview") else None,
            "content_rating": [
                rating["description"] for rating in game_data.get("data", {}).get("content_descriptors", {}).get("ids", [])
            ] if game_data.get("data", {}).get("content_descriptors") else None
        }
import requests

class SteamSpy:
    def __init__(self):
        """Initialize the SteamSpy with the base URL."""
        self.base_url = "https://steamspy.com/api.php"

    def get_game_data(self, appid: str) -> dict:
        """Fetch game data from SteamSpy based on appid.
        Args:
            appid (str): The appid of the game to fetch data for.

        Returns:
            dict: The game data from SteamSpy.
        """
        url = f"{self.base_url}?request=appdetails&appid={appid}"
        response = requests.get(url)
        if response.status_code != 200:
            raise ConnectionError(f"Failed to connect to SteamSpy API. Status code: {response.status_code}")
        
        data = response.json()
        if not data['name']:
            raise ValueError(f"Data for appid {appid} not found in SteamSpy.")
        
        return {
            "appid": data["appid"],
            "name": data["name"],
            "positive": data["positive"],
            "negative": data["negative"],
            "average_forever": data["average_forever"],
            "average_2weeks": data["average_2weeks"]
        }
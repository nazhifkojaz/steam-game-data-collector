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
            dict: The status, game data, and any error message if applicable.
        """
        result = {"status": False, "data": None, "error": None}

        url = f"{self.base_url}?request=appdetails&appid={appid}"
        response = requests.get(url)
        if response.status_code != 200:
            # raise ConnectionError(f"Failed to connect to SteamSpy API. Status code: {response.status_code}")
            result["error"] = (
                f"Failed to connect to SteamSpy API. Status code: {response.status_code}"
            )
            return result

        data = response.json()
        if not data["name"]:
            # raise ValueError(f"Data for appid {appid} not found in SteamSpy.")
            result["error"] = f"Data for appid {appid} not found in SteamSpy."
            return result

        result["status"] = True
        result["data"] = {
            "appid": data.get("appid", appid),
            "name": data.get("name", ""),
            "average_forever": data.get("average_forever", None),
            "average_2weeks": data.get("average_2weeks", None),
        }

        return result

import requests
from bs4 import BeautifulSoup
from datetime import datetime

class SteamCharts:
    def __init__(self):
        """Initialize the SteamCharts with the appid of the game.
        Args:
            appid (str): The appid of the game to fetch data for.
        """
        self.base_url = "https://steamcharts.com/app/"

    def _do_request(self, appid: str) -> BeautifulSoup:
        """Perform a GET request to the SteamCharts API and return the BeautifulSoup object.
        Args:
            appid (str): The appid of the game to fetch data for.

        Returns:
            BeautifulSoup: The BeautifulSoup object containing the response content.
        """

        url = f"{self.base_url}{appid}"
        
        # define the headers to simulate a browser request
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.6312.86 Safari/537.36"
            )
        }

        response = requests.get(url, headers=headers)
        response.encoding = "utf-8"
        if response.status_code != 200:
            # raise ConnectionError(f"Failed to connect to SteamCharts API. Status code: {response.status_code}")
            return None
        
        return BeautifulSoup(response.text, "html.parser")
    
    def get_game_data(self, appid: str) -> dict:
        """Parse the game stats from the beautifulSoup object.
        Args:
            appid (str): The appid of the game to fetch data for.
            
        Returns:
            dict: The result containing status, game data, and any error message if applicable.
        """
        result = {
            "status": False,
            "data": None,
            "error": None
        }

        soup = self._do_request(appid)

        if not soup:
            # raise ValueError("Failed to fetch data from SteamCharts.")
            result["error"] = "Failed to fetch data from SteamCharts."
            return result
        
        # get the part where it contains the 24 hour peak and all time peak data
        peak_data = soup.find_all("div", class_="app-stat")
        if not peak_data:
            # raise ValueError("Failed to parse SteamCharts data. No peak data found.")
            result["error"] = "Failed to parse SteamCharts data. No peak data found."
            return result
        
        result["status"] = True
        result["data"] = {
            "active_player_24h": int(peak_data[1].find("span", class_="num").text),
            "peak_active_player_all_time": int(peak_data[2].find("span", class_="num").text)
        }
        return result
    
    def get_active_player_data(self, appid: str) -> dict:
        """Fetch active player data from SteamChart based on its appid.
        Args:
            appid (str): The appid of the game to fetch data for.

        Returns:
            dict: The result containing the status, appid, name, active player data, and any error message if applicable.
        """
        result = {
            "status": False,
            "appid": appid,
            "name": None,
            "active_player_data": [],
            "error": None
        }

        soup = self._do_request(appid)

        if not soup:
            # raise ValueError("Failed to fetch data from SteamCharts.")
            result["error"] = "Failed to fetch data from SteamCharts."
            return result
        
        # get the game name, if they don't have a game name, add an error message.        
        game_name = soup.find("h1", id="app-title")
        if not game_name:
            # raise ValueError("Failed to parse SteamCharts data. No game name found.")
            result["error"] = "Failed to parse SteamCharts data. No game name found."
        else:
            # if we have a game name, set the game name in the result
            result["name"] = game_name.text
        
        # get the player data table, if it also doesn't exist, extend the error message and return the empty result
        player_data_table = soup.find("table", class_="common-table")
        if not player_data_table:
            # raise ValueError("Failed to parse SteamCharts data. No player data table found.")
            result["error"] = "Failed to parse SteamCharts data. No player data table found." if not result["error"] else result["error"] + " No player data table found."
            return result
        
        # if we have a player data table, set the status to True
        result["status"] = True

        # get the player data rows, skipping the first two header rows
        player_data_rows = player_data_table.find_all("tr")[2:]

        for row in player_data_rows:
            cols = [col.text.strip() for col in row.find_all("td")]

            month, avg_players, gain, percentage_gain, peak_players = cols[:5]

            result["active_player_data"].append(
                {
                    "month": datetime.strptime(month, "%B %Y").strftime("%Y-%m"),
                    "avg_players": float(avg_players.replace(",", "")),
                    "gain": float(gain.replace(",", "")) if gain not in ("-", "") else None,
                    "percentage_gain": float(percentage_gain.replace("%", "").replace(",", "").strip()) if percentage_gain not in ("-", "") else 0,
                    "peak_players": float(peak_players.replace(",", ""))
                }
            )

        return result

import requests
from bs4 import BeautifulSoup
from datetime import datetime

class SteamCharts:
    def __init__(self, appid: str):
        """Initialize the SteamCharts with the appid of the game.
        Args:
            appid (str): The appid of the game to fetch data for.
        """
        self.appid = appid
        self.base_url = "https://steamcharts.com/app/"

    def do_request(self, appid: str) -> BeautifulSoup:
        """Perform a GET request to the SteamCharts API and return the BeautifulSoup object.
        Args:
            appid (str): The appid of the game to fetch data for.

        Returns:
            BeautifulSoup: The BeautifulSoup object containing the response content.
        """
        url = f"{self.base_url}{appid}"
        result = {}
        result["appid"] = appid

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
            raise ConnectionError(f"Failed to connect to SteamCharts API. Status code: {response.status_code}")
        
        return BeautifulSoup(response.text, "html.parser")
    
    def _parse_game_name(self, soup: BeautifulSoup) -> str:
        """Parse the game name from the BeautifulSoup object.
        Args:
            soup (BeautifulSoup): The BeautifulSoup object containing the response content.

        Returns:
            str: The parsed game name.
        """
        game_name = soup.find("h1", id="app-title")
        if not game_name:
            raise ValueError("Failed to parse SteamCharts data. No game name found.")
        
        return game_name.text
    
    def _parse_game_data(self, soup: BeautifulSoup) -> dict:
        """Parse the game data from the BeautifulSoup object.
        Args:
            soup (BeautifulSoup): The BeautifulSoup object containing the response content.

        Returns:
            dict: The parsed game data.
        """
        result = {}

        # get the part where it contains the 24 hour peak and all time peak data
        peak_data = soup.find_all("div", class_="app-stat")
        if not peak_data:
            raise ValueError("Failed to parse SteamCharts data. No peak data found.")
        
        # get the 24 hour peak and all time peak data
        result["24h_peak"] = int(peak_data[1].find("span", class_="num").text)
        result["all_time_peak"] = int(peak_data[2].find("span", class_="num").text)

        return result
    
    def _parse_active_player_data(self, soup: BeautifulSoup) -> list:
        """Parse the active player data from the BeautifulSoup object.
        Args:
            soup (BeautifulSoup): The BeautifulSoup object containing the response content.

        Returns:
            list: The parsed active player data.
        """
        result = []
        
        player_data_table = soup.find("table", class_="common-table")
        if not player_data_table:
            raise ValueError("Failed to parse SteamCharts data. No player data table found.")
        
        player_data_rows = player_data_table.find_all("tr")[2:]

        for row in player_data_rows:
            cols = [col.text.strip() for col in row.find_all("td")]

            month, avg_players, gain, percentage_gain, peak_players = cols[:5]

            result.append(
                {
                    "month": datetime.strptime(month, "%B %Y").strftime("%Y-%m"),
                    "avg_players": float(avg_players.replace(",", "")),
                    "gain": float(gain.replace(",", "")) if gain not in ("-", "") else None,
                    "percentage_gain": float(percentage_gain.replace("%", "").replace(",", "").strip()) if percentage_gain not in ("-", "") else 0,
                    "peak_players": float(peak_players.replace(",", ""))
                }
            )

        return result
    
    def get_game_data(self, appid: str) -> dict:
        """Fetch game data from SteamCharts based on appid.
        Args:
            appid (str): The appid of the game to fetch data for.

        Returns:
            dict: The game data from SteamCharts.
        """
        soup = self.do_request(appid)
        return {
            "appid": appid,
            "name": self._parse_game_name(soup),
            **self._parse_game_data(soup)
        }
    
    def get_active_player_data(self, appid: str) -> list:
        """Fetch active player data from SteamCharts based on appid.
        Args:
            appid (str): The appid of the game to fetch data for.

        Returns:
            list: The active player data from SteamCharts.
        """
        soup = self.do_request(appid)
        return self._parse_active_player_data(soup)
    
    def get_all_data(self, appid: str) -> dict:
        """Fetch all game data from SteamCharts based on appid.
        Args:
            appid (str): The appid of the game to fetch data for.

        Returns:
            dict: The game data from SteamCharts.
        """
        soup = self.do_request(appid)
        return {
            "appid": appid,
            "name": self._parse_game_name(soup),
            **self._parse_game_data(soup),
            "active_player_data": self._parse_active_player_data(soup)
        }
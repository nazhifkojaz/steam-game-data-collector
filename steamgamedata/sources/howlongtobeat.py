# ---------------------------
# This code is based on the original code from HowLongToBeatAPI (https://github.com/ScrappyCocco/HowLongToBeat-PythonAPI/)
# But modified to fit this project, all credit goes to the original author
# ---------------------------

import json
import re

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from steamgamedata.sources.base import BaseSource


class SearchInformation:
    """Class to hold search information extracted from the HLTB script."""

    def __init__(self, title_headers: dict) -> None:
        self.api_key = None
        self.search_url = None
        self._get_search_informations(title_headers=title_headers)
        if self.search_url:
            self.search_url = self.search_url.lstrip("/")

    def _extract_api_from_script(self, script_content: str) -> str | None:
        """Extract the API key from the script content.
        Args:
            script_content (str): The content of the script to search for the API key.
        Returns:
            str | None: The extracted API key if found, otherwise None.
        """

        api_key_pattern = r'users\s*:\s*{\s*id\s*:\s*"([^"]+)"'
        matches = re.findall(api_key_pattern, script_content)

        if matches:
            key = "".join(matches)
            return key

        concat_api_key_pattern = r'\/api\/\w+\/"(?:\.concat\("[^"]*"\))*'
        matches = re.findall(concat_api_key_pattern, script_content)

        if matches:
            matches = str(matches).split(".concat")
            matches = [re.sub(r'["\(\)\[\]\']', "", match) for match in matches[1:]]
            key = "".join(matches)
            return key

        return None

    def _extract_search_url_script(self, script_content: str) -> str | None:
        """Extract the search URL from the script content.
        Args:
            script_content (str): The content of the script to search for the search URL.
        Returns:
            str | None: The extracted search URL if found, otherwise None.
        """
        pattern = re.compile(
            r'fetch\(\s*["\'](\/api\/[^"\']*)["\']'  # Matches the endpoint
            r'((?:\s*\.concat\(\s*["\']([^"\']*)["\']\s*\))+)'  # Captures concatenated strings
            r"\s*,",  # Matches up to the comma
            re.DOTALL,
        )
        matches = pattern.finditer(script_content)
        for match in matches:
            endpoint = match.group(1)
            concat_calls = match.group(2)
            # Extract all concatenated strings
            concat_strings = re.findall(r'\.concat\(\s*["\']([^"\']*)["\']\s*\)', concat_calls)
            concatenated_str = "".join(concat_strings)
            # Check if the concatenated string matches the known string
            if concatenated_str == self.api_key:
                return endpoint
        # Unable to find :(
        return None

    def _get_search_informations(self, title_headers) -> None:
        response = requests.get(HowLongToBeat.BASE_URL, headers=title_headers, timeout=60)

        if response.status_code == 200 and response.text:
            soup = BeautifulSoup(response.text, "html.parser")
            scripts = soup.find_all("script", src=True)

            matching_scripts = []
            non_matching_scripts = []

            for script in scripts:
                src = script.get("src")
                if src:
                    if "_app-" in src:
                        matching_scripts.append(src)
                    else:
                        non_matching_scripts.append(src)

            # look for scripts that provide the api key
            self._process_script(matching_scripts, title_headers=title_headers)

            # if we still don't have the api key, try to get it from the other scripts
            if self.api_key is None:
                self._process_script(non_matching_scripts, title_headers=title_headers)

    def _process_script(self, script_urls: list[str], title_headers: dict) -> None:
        """Process the script content to extract API key and search URL.
        Args:
            script_urls (list[str]): List of script URLs to process.
        """
        for script_url in script_urls:
            script_url = HowLongToBeat.BASE_URL + script_url
            script_response = requests.get(script_url, headers=title_headers, timeout=60)
            if script_response.status_code == 200 and script_response.text:
                self.api_key = self._extract_api_from_script(script_response.text)
                self.search_url = self._extract_search_url_script(script_response.text)
                if self.api_key:
                    break


class HowLongToBeat(BaseSource):
    """HowLongToBeat source for fetching game completion times."""

    BASE_URL = "https://howlongtobeat.com/"
    REFERER_HEADER = BASE_URL

    def _make_request(self, game_name: str, page: int = 1) -> str | None:
        """Send a web request to HowLongToBeat to fetch game data.
        Args:
            game_name (str): The name of the game to search for.
            page (int): The page number to fetch results from. (default is 1).

        Returns:
            str: HTML response text if the request is successful.
        """

        title_headers = HowLongToBeat._get_title_request_headers()
        search_headers = HowLongToBeat._get_search_request_headers()
        search_info_data = SearchInformation(title_headers=title_headers)

        search_url = HowLongToBeat.BASE_URL + "api/s/"
        if search_info_data.search_url:
            search_url = HowLongToBeat.BASE_URL + search_info_data.search_url

        search_url_with_key = search_url + search_info_data.api_key
        payload = HowLongToBeat._generate_data_payload(game_name, page, None)
        response = requests.post(
            search_url_with_key, headers=search_headers, data=payload, timeout=60
        )

        if response.status_code == 200:
            return response.text

        # if the request failed, try to use the search URL with API key in the payload
        payload = HowLongToBeat._generate_data_payload(game_name, page, search_info_data)
        response = requests.post(search_url, headers=search_headers, data=payload, timeout=60)

        if response.status_code == 200:
            return response.text

        return None

    @staticmethod
    def _get_title_request_headers() -> dict:
        """Get headers for the title request."""
        ua = UserAgent()
        headers = {"User-Agent": ua.random, "referer": HowLongToBeat.REFERER_HEADER}
        return headers

    @staticmethod
    def _get_search_request_headers() -> dict:
        ua = UserAgent()
        headers = {
            "content-type": "application/json",
            "accept": "*/*",
            "User-Agent": ua.random.strip(),
            "Referer": HowLongToBeat.REFERER_HEADER,
        }

        return headers

    @staticmethod
    def _generate_data_payload(
        game_name: str, page: int, search_info: SearchInformation = None
    ) -> str:
        """Generate data payload
        Args:
            game_name (str): The game name to fetch data for.
            page: The page to search
            search_info (SearchInformation): Search information containing API key and search URL of the HLTB.

        Returns:
            str: JSON string of the payload to be sent in the request.

        """
        payload = {
            "searchType": "games",
            "searchTerms": game_name.split(),
            "searchPage": page,
            "size": 20,
            "searchOptions": {
                "games": {
                    "userId": 0,
                    "platform": "",
                    "sortCategory": "popular",
                    "rangeCategory": "main",
                    "rangeTime": {"min": 0, "max": 0},
                    "gameplay": {"perspective": "", "flow": "", "genre": "", "difficulty": ""},
                    "rangeYear": {"max": "", "min": ""},
                    "modifier": "",
                },
                "users": {"sortCategory": "postcount"},
                "lists": {"sortCategory": "follows"},
                "filter": "",
                "sort": 0,
                "randomizer": 0,
            },
            "useCache": True,
        }

        # If api_key is passed add it to the dict
        if search_info and search_info.api_key:
            payload["searchOptions"]["users"]["id"] = search_info.api_key

        return json.dumps(payload)

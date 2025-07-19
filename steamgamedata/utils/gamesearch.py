from typing import Any, cast

import requests
from rapidfuzz import fuzz, process


class GameSearch:
    _STEAM_APPLIST_URL = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"

    def __init__(self) -> None:
        self._cached_games: list[dict[str, Any]] = []
        self._cached_names: list[str] = []

    def refresh(self, force: bool = False) -> None:
        """assign _cached_games and _cached_names"""
        if force or not self._cached_games:
            self._cached_games = self.get_game_list()
            self._cached_names = [game["name"].lower() for game in self._cached_games]
            # self._cached_names = [(idx, game["name"].lower()) for idx, game in enumerate(self._cached_games)]

    def get_game_list(self) -> list[dict[str, Any]]:
        response = requests.get(self._STEAM_APPLIST_URL)
        response.raise_for_status()

        return cast(list[dict[str, Any]], response.json()["applist"]["apps"])

    def search_by_name(self, game_name: str, top_n: int = 5) -> list[dict[str, Any]]:
        self.refresh()
        query = game_name.lower()

        # search through candidates
        matches = process.extract(
            query,
            self._cached_names,
            scorer=fuzz.WRatio,
            limit=top_n * 2,
            score_cutoff=60,
        )

        return [
            {
                "appid": str(self._cached_games[idx]["appid"]),
                "name": self._cached_games[idx]["name"],
                "search_score": round(score, 2),
            }
            for (_, score, idx) in matches
        ][:top_n]

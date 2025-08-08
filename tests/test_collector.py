import pytest
import pandas as pd
from steamgamedata.collector import DataCollector
from steamgamedata.model import GameDataModel
from steamgamedata.sources import Gamalytic, howlongtobeat, HowLongToBeat, SteamAchievements, SteamCharts, SteamReview, SteamSpy, SteamStore

class TestDataCollector:

    @pytest.fixture(autouse=True)
    def mock_sources(self, mock_request_response, monkeypatch, request):

        # mock the SearchInforomation needed by HowLongToBeat to prevent API calls
        class SearchInformation:
            def __init__(self, *args, **kwargs):
                self.api_key = "mock_api_key"
                self.search_url = "api/s/"
        monkeypatch.setattr(howlongtobeat, "SearchInformation", SearchInformation)
        
        # then mock the request responses for each source
        # pair the source class with the mock data
        sources = [
            {Gamalytic: {"json_data": request.getfixturevalue("gamalytic_success_response_data")}},
            {HowLongToBeat: {"text_data": request.getfixturevalue("hltb_success_response_data")}},
            {SteamAchievements: {"json_data": request.getfixturevalue("achievements_success_response_data")}},
            {SteamCharts: {"text_data": request.getfixturevalue("steamcharts_success_response_data")}},
            {SteamReview: {"json_data": request.getfixturevalue("review_only_tchinese")}},
            {SteamSpy: {"json_data": request.getfixturevalue("steamspy_success_response_data")}},
            {SteamStore: {"json_data": request.getfixturevalue("steamstore_success_response_data")}},
        ]

        for source in sources:
            for target_class, data in source.items():
                mock_request_response(
                    target_class=target_class,
                    **data
                )

    def test_fetch_raw_data(self):
        collector = DataCollector()
        raw_data = collector._fetch_raw_data(
            steam_appid="12345"
        )

        assert isinstance(raw_data, GameDataModel)

    @pytest.mark.parametrize(
        "appids, expected_len",
        [
            ("12345", 1),
            (["12345", "12345"], 2),
            ([], 0)
        ],
        ids=[
            "single_appid",
            "multiple_appids",
            "empty_appids"
        ]
    )
    def test_get_games_data(
        self,
        appids,
        expected_len
    ):
        collector = DataCollector()
        games_data = collector.get_games_data(steam_appids=appids)

        assert isinstance(games_data, list)
        assert len(games_data) == expected_len

        if expected_len > 0:
            assert isinstance(games_data[0], dict)
            assert games_data[0]["steam_appid"] == "12345"

    @pytest.mark.parametrize(
        "appids, expected_len",
        [
            ("12345", 1),
            (["12345", "12345"], 2),
            ([], 0)
        ],
        ids=[
            "single_appid",
            "multiple_appids",
            "empty_appids"
        ]
    )
    def test_get_games_active_player_data(
        self,
        appids,
        expected_len
    ):
        collector = DataCollector()
        active_player_data = collector.get_games_active_player_data(steam_appids=appids)

        assert isinstance(active_player_data, pd.DataFrame)
        assert len(active_player_data) == expected_len

        if expected_len > 0:
            assert "steam_appid" in active_player_data.columns
            assert active_player_data["steam_appid"].iloc[0] == "12345"

    @pytest.mark.parametrize(
        "review_only, has_reviews_labels",
        [
            (True, False),
            (False, True)
        ],
        ids=[
            "review_only_true",
            "review_only_false"
        ]
    )
    def test_get_game_review(
        self,
        review_only,
        has_reviews_labels
    ):
        collector = DataCollector()
        review_data = collector.get_game_review(
            steam_appid="12345",
            review_only=review_only
        )

        assert isinstance(review_data, pd.DataFrame)

        if has_reviews_labels:
            assert "reviews" in review_data.columns
            assert len(review_data["reviews"]) > 0
        else:
            assert "reviews" not in review_data.columns
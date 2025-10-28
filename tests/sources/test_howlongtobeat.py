import pytest

from gameinsights.sources import howlongtobeat
from gameinsights.sources.howlongtobeat import HowLongToBeat


class TestHowLongToBeat:

    @pytest.fixture(autouse=True)
    def mock_search_information(self, monkeypatch):
        class SearchInformation:
            def __init__(self, *args, **kwargs):
                self.api_key = "mock_api_key"
                self.search_url = "api/s/"

        monkeypatch.setattr(howlongtobeat, "SearchInformation", SearchInformation)

    def test_fetch_success(self, source_fetcher, hltb_success_response_data):
        result = source_fetcher(
            HowLongToBeat,
            mock_kwargs={"text_data": hltb_success_response_data},
            call_kwargs={"game_name": "mock_name"},
        )

        assert result["success"] is True
        assert result["data"]["game_id"] == 1234
        assert result["data"]["game_name"] == "Mock Game: The Adventure"

        # check if the not-listed labels are None as well
        assert result["data"]["comp_main"] is None

        # check if there number of labels are correct (no stray or missing labels)
        assert len(result["data"]) == 22

    @pytest.mark.parametrize(
        "selected_labels, expected_labels, expected_len",
        [
            (["game_name"], ["game_name"], 1),
            (["game_name", "invalid_label"], ["game_name"], 1),
            (["invalid_label"], [], 0),
        ],
    )
    def test_fetch_success_with_filtering(
        self,
        source_fetcher,
        hltb_success_response_data,
        selected_labels,
        expected_labels,
        expected_len,
    ):
        result = source_fetcher(
            HowLongToBeat,
            mock_kwargs={"text_data": hltb_success_response_data},
            call_kwargs={"game_name": "mock_name", "selected_labels": selected_labels},
        )

        assert result["success"] is True

        result_keys = list(result["data"].keys())
        assert sorted(result_keys) == sorted(expected_labels)

        assert len(result["data"]) == expected_len

    def test_fetch_success_but_empty_game_not_found(
        self,
        source_fetcher,
        hltb_success_but_not_found_data,
    ):
        result = source_fetcher(
            HowLongToBeat,
            mock_kwargs={"text_data": hltb_success_but_not_found_data},
            call_kwargs={"game_name": "mock_name"},
        )

        assert result["success"] is False
        assert "error" in result
        assert result["error"] == "Game is not found."

    def test_fetch_error_on_request(self, monkeypatch):

        def mock_method(*args, **kwargs):
            return None

        monkeypatch.setattr(HowLongToBeat, "_fetch_search_results", mock_method)

        source = HowLongToBeat()
        result = source.fetch(game_name="mock_data")

        assert result["success"] is False
        assert "error" in result
        assert result["error"] == "Failed to fetch data."

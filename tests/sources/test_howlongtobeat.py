import pytest

from steamgamedata.sources import howlongtobeat
from steamgamedata.sources.howlongtobeat import HowLongToBeat


class TestHowLongToBeat:

    @pytest.fixture(autouse=True)
    def mock_search_information(self, monkeypatch):
        class SearchInformation:
            def __init__(self, *args, **kwargs):
                self.api_key = "mock_api_key"
                self.search_url = "api/s/"

        monkeypatch.setattr(howlongtobeat, "SearchInformation", SearchInformation)

    def _setup_fetch(
        self,
        mock_request_response,
        status_code=200,
        response_data=None,
        game_name="mock_name",
        selected_labels=None,
    ):
        mock_request_response(
            target_class=HowLongToBeat, status_code=status_code, text_data=response_data
        )
        source = HowLongToBeat()
        return source.fetch(game_name=game_name, selected_labels=selected_labels)

    def test_fetch_success(self, mock_request_response, hltb_success_response_data):
        result = self._setup_fetch(
            mock_request_response=mock_request_response,
            response_data=hltb_success_response_data,
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
        mock_request_response,
        hltb_success_response_data,
        selected_labels,
        expected_labels,
        expected_len,
    ):
        result = self._setup_fetch(
            mock_request_response=mock_request_response,
            response_data=hltb_success_response_data,
            selected_labels=selected_labels,
        )

        assert result["success"] is True

        result_keys = list(result["data"].keys())
        assert sorted(result_keys) == sorted(expected_labels)

        assert len(result["data"]) == expected_len

    def test_fetch_success_but_empty_game_not_found(
        self,
        mock_request_response,
        hltb_success_but_not_found_data,
    ):
        result = self._setup_fetch(
            mock_request_response=mock_request_response,
            response_data=hltb_success_but_not_found_data,
        )

        assert result["success"] is False
        assert "error" in result
        assert result["error"] == "Game is not found."

    def test_fetch_error_on_request(self, monkeypatch):

        def mock_method(*args, **kwargs):
            return None

        monkeypatch.setattr(HowLongToBeat, "_make_request", mock_method)

        source = HowLongToBeat()
        result = source.fetch(game_name="mock_data")

        assert result["success"] is False
        assert "error" in result
        assert result["error"] == "Failed to fetch data."

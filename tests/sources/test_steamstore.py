import pytest

from gameinsights.sources import steamstore
from gameinsights.sources.steamstore import SteamStore


class TestSteamStore:

    def _setup_fetch(
        self,
        mock_request_response,
        status_code=200,
        response_data=None,
        steam_appid="12345",
        selected_labels=None,
    ):
        mock_request_response(
            target_class=SteamStore, status_code=status_code, json_data=response_data
        )

        # predefined with the default region since if the region/language inputted invalid, it'll default to the region where the user ip's region
        source = SteamStore(region="us", language="english")

        return source.fetch(steam_appid=steam_appid, selected_labels=selected_labels)

    def test_fetch_success(self, mock_request_response, steamstore_success_response_data):
        result = self._setup_fetch(
            mock_request_response=mock_request_response,
            response_data=steamstore_success_response_data,
        )

        assert result["success"] is True
        assert result["data"]["steam_appid"] == 12345
        assert result["data"]["type"] == "mock"
        assert len(result["data"]) == len(steamstore._STEAM_LABELS)

        # check if it successfully process the content_rating
        assert result["data"]["content_rating"][0]["rating_type"] == "pegi"
        assert result["data"]["content_rating"][0]["rating"] == "12"

    @pytest.mark.parametrize(
        "selected_labels, expected_labels",
        [
            (["name"], ["name"]),
            (["name", "invalid_label"], ["name"]),
            (["steam_appid", "name", "invalid_label"], ["name", "steam_appid"]),
            (["invalid_label"], []),
        ],
        ids=[
            "normal_filtering",
            "filtering_with_invalid_label",
            "filter_labels_unordered",
            "filtering_with_only_invalid_label",
        ],
    )
    def test_fetch_with_filtering(
        self,
        mock_request_response,
        steamstore_success_response_data,
        selected_labels,
        expected_labels,
    ):
        result = self._setup_fetch(
            mock_request_response=mock_request_response,
            response_data=steamstore_success_response_data,
            selected_labels=selected_labels,
        )

        assert result["success"] is True

        result_keys = list(result["data"].keys())
        assert sorted(result_keys) == sorted(expected_labels)
        assert len(result["data"]) == len(expected_labels)

    def test_fetch_error_connection_fail(
        self,
        mock_request_response,
    ):
        result = self._setup_fetch(
            mock_request_response=mock_request_response,
            status_code=400,
        )

        assert result["success"] is False
        assert "error" in result
        assert result["error"] == "Failed to connect to API. Status code: 400."

    def test_fetch_error_game_not_found(
        self, mock_request_response, steamstore_not_found_response_data
    ):
        result = self._setup_fetch(
            mock_request_response=mock_request_response,
            response_data=steamstore_not_found_response_data,
        )

        assert result["success"] is False
        assert "error" in result
        assert (
            result["error"]
            == "Failed to fetch data for appid 12345, or appid is not available in the specified region (us) or language (english)."
        )

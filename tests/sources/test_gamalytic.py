import pytest

from gameinsights.sources.gamalytic import Gamalytic


class TestGamalytic:

    def _setup_fetch(
        self,
        mock_request_response,
        status_code=200,
        gamalytic_success_response_data=None,
        steam_appid="12345",
        selected_labels=None,
    ):
        mock_request_response(
            target_class=Gamalytic,
            status_code=status_code,
            json_data=gamalytic_success_response_data,
        )
        source = Gamalytic()
        return source.fetch(steam_appid=steam_appid, selected_labels=selected_labels)

    def test_fetch_success(self, mock_request_response, gamalytic_success_response_data):
        result = self._setup_fetch(
            mock_request_response=mock_request_response,
            gamalytic_success_response_data=gamalytic_success_response_data,
        )

        assert result["success"] is True
        assert result["data"]["steam_appid"] == "12345"
        assert result["data"]["name"] == "Mock Game: The Adventure"

        # should be none because in the mock data, I didn't provide the developers
        assert result["data"]["developers"] is None

        # should be 22 labels because I only take 24 out of all data they provided
        # and leave 2 commented
        assert len(result["data"]) == 22

    def test_fetch_success_numeric_appid(
        self, mock_request_response, gamalytic_success_response_data
    ):
        result = self._setup_fetch(
            mock_request_response=mock_request_response,
            gamalytic_success_response_data=gamalytic_success_response_data,
            steam_appid=12345,
        )

        assert result["success"] is True
        assert result["data"]["steam_appid"] == "12345"
        assert result["data"]["name"] == "Mock Game: The Adventure"
        assert result["data"]["developers"] is None
        assert len(result["data"]) == 22

    @pytest.mark.parametrize(
        "selected_labels, expected_labels, expected_len",
        [
            (["name"], ["name"], 1),
            (["name", "invalid_label"], ["name"], 1),
            (["invalid_label"], [], 0),
        ],
    )
    def test_fetch_success_with_filtering(
        self,
        mock_request_response,
        gamalytic_success_response_data,
        selected_labels,
        expected_labels,
        expected_len,
    ):
        result = self._setup_fetch(
            mock_request_response=mock_request_response,
            gamalytic_success_response_data=gamalytic_success_response_data,
            selected_labels=selected_labels,
        )

        assert result["success"] is True

        result_keys = list(result["data"].keys())
        assert sorted(result_keys) == sorted(expected_labels)

        assert len(result["data"]) == expected_len

    @pytest.mark.parametrize(
        "status_code, expected_error",
        [
            (404, {"success": False, "error": "Game with appid 12345 is not found."}),
            (500, {"success": False, "error": "Failed to connect to API. Status code: 500"}),
            (403, {"success": False, "error": "Failed to connect to API. Status code: 403"}),
        ],
    )
    def test_fetch_error(self, mock_request_response, status_code, expected_error):
        result = self._setup_fetch(
            mock_request_response=mock_request_response,
            status_code=status_code,
        )

        assert result["success"] == expected_error["success"]
        assert "error" in result
        assert result["error"] == expected_error["error"]

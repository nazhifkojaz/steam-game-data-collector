import pytest

from gameinsights.sources.steamcharts import SteamCharts


class TestSteamCharts:
    def _setup_fetch(
        self,
        mock_request_response,
        status_code=200,
        response_data=None,
        steam_appid="12345",
        selected_labels=None,
    ):
        mock_request_response(
            target_class=SteamCharts, status_code=status_code, text_data=response_data
        )

        source = SteamCharts()

        return source.fetch(steam_appid=steam_appid, selected_labels=selected_labels)

    def test_fetch_success(
        self,
        mock_request_response,
        steamcharts_success_response_data,
    ):
        result = self._setup_fetch(
            mock_request_response=mock_request_response,
            response_data=steamcharts_success_response_data,
        )

        assert result["success"] is True
        assert result["data"]["steam_appid"] == "12345"
        assert result["data"]["name"] == "Mock Game: The Adventure"

        # check the number of labels
        assert len(result["data"]) == 5

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
        steamcharts_success_response_data,
        selected_labels,
        expected_labels,
        expected_len,
    ):
        result = self._setup_fetch(
            mock_request_response=mock_request_response,
            response_data=steamcharts_success_response_data,
            selected_labels=selected_labels,
        )

        assert result["success"] is True

        result_keys = list(result["data"].keys())
        assert sorted(result_keys) == sorted(expected_labels)

        assert len(result["data"]) == expected_len

    @pytest.mark.parametrize(
        "response_data, expected_error",
        [
            (
                "steamcharts_error_response_no_app_title",
                "Failed to parse data, game name is not found.",
            ),
            (
                "steamcharts_error_response_incorrect_appstat_count",
                "Failed to parse data, expecting atleast 3 'app-stat' divs.",
            ),
            (
                "steamcharts_error_response_incorrect_appstat_structure",
                "Failed to parse data, incorrect app-stat structure.",
            ),
            (
                "steamcharts_error_response_no_player_data_table",
                "Failed to parse data, active player data table is not found.",
            ),
            (
                "steamcharts_error_response_player_data_table_incorrect_structure",
                "Failed to parse data, the structure of player data table is incorrect.",
            ),
        ],
        ids=[
            "no_app_title",
            "incorrect_appstat_count",
            "incorrect_appstat_structure",
            "no_player_data_table",
            "incorrect_player_data_table_structure",
        ],
    )
    def test_fetch_parse_error(
        self, mock_request_response, request, response_data, expected_error
    ):

        response_text = request.getfixturevalue(response_data)

        result = self._setup_fetch(
            mock_request_response=mock_request_response,
            response_data=response_text,
        )

        assert result["success"] is False
        assert "error" in result
        assert result["error"] == expected_error

    @pytest.mark.parametrize(
        "status_code, expected_error",
        [
            (404, {"success": False, "error": "Failed to fetch data with status code: "}),
            (500, {"success": False, "error": "Failed to fetch data with status code: "}),
            (403, {"success": False, "error": "Failed to fetch data with status code: "}),
        ],
    )
    def test_fetch_error(self, mock_request_response, status_code, expected_error):
        result = self._setup_fetch(
            mock_request_response=mock_request_response,
            status_code=status_code,
        )

        assert result["success"] == expected_error["success"]
        assert "error" in result
        assert result["error"] == expected_error["error"] + str(status_code)

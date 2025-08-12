import pytest

from gameinsights.sources.steamachievements import SteamAchievements


class Test_SteamAchievements:

    @pytest.mark.parametrize(
        "api_key, selected_labels, expected_result",
        [
            (
                None,
                None,
                {
                    "achievements_count": 2,
                    "achievements_percentage_average": 12.3,
                    "achievements_list": [
                        {"name": "Mock_1", "percent": 12.3},
                        {"name": "Mock_2", "percent": 12.3},
                    ],
                },
            ),
            (None, ["achievements_count"], {"achievements_count": 2}),
            (None, ["achievements_count", "invalid_label"], {"achievements_count": 2}),
            (None, ["invalid_label"], {}),
            (
                "mockapikey",
                None,
                {
                    "achievements_count": 2,
                    "achievements_percentage_average": 12.3,
                    "achievements_list": [
                        {
                            "name": "Mock_1",
                            "percent": 12.3,
                            "display_name": "Mock One",
                            "hidden": 0,
                            "description": "Clear Mock One",
                        },
                        {
                            "name": "Mock_2",
                            "percent": 12.3,
                            "display_name": "Mock Two",
                            "hidden": 1,
                            "description": None,
                        },
                    ],
                },
            ),
            ("mockapikey", ["achievements_count"], {"achievements_count": 2}),
            ("mockapikey", ["achievements_count", "invalid_label"], {"achievements_count": 2}),
            ("mockapikey", ["invalid_label"], {}),
        ],
        ids=[
            "no_apikey_no_filtering",
            "no_apikey_with_filtering",
            "no_apikey_with_filtering_include_invalid_label",
            "no_apikey_but_empty_due_to_filtering_only_invalid_label",
            "apikey_no_filtering",
            "apikey_with_filtering",
            "apikey_with_filtering_include_invalid_label",
            "apikey_but_empty_due_to_filtering_only_invalid_label",
        ],
    )
    def test_fetch_success(
        self,
        mock_request_response,
        achievements_success_response_data,
        scheme_success_response_data,
        api_key,
        selected_labels,
        expected_result,
    ):
        source = SteamAchievements(api_key=api_key)

        # if api_key is assigned, use the side_effect to mock multiple times
        if api_key:
            mock_request_response(
                target_class=SteamAchievements,
                side_effect=[
                    {"json_data": achievements_success_response_data},
                    {"json_data": scheme_success_response_data},
                ],
            )
        else:
            mock_request_response(
                target_class=SteamAchievements, json_data=achievements_success_response_data
            )

        result = source.fetch(
            steam_appid="12345",
            selected_labels=selected_labels,
        )

        assert result["success"] is True
        assert len(result["data"]) == len(expected_result)
        assert result["data"] == expected_result

    @pytest.mark.parametrize(
        "api_key, achievements_status_code, schema_status_code , expected_result",
        [
            (None, 400, None, "Failed to connect to API. Status code: 400."),
            ("mockapikey", 200, 403, "Access denied, verify your API Key. Status code: 403."),
            ("mockapikey", 200, 400, "Failed to connect to API. Status code: 400."),
        ],
    )
    def test_fetch_error(
        self,
        mock_request_response,
        api_key,
        achievements_status_code,
        schema_status_code,
        expected_result,
    ):
        source = SteamAchievements(api_key=api_key)
        if api_key:
            mock_request_response(
                target_class=SteamAchievements,
                side_effect=[
                    {"status_code": achievements_status_code},
                    {"status_code": schema_status_code},
                ],
            )
        else:
            mock_request_response(
                target_class=SteamAchievements,
                status_code=achievements_status_code,
            )

        result = source.fetch(
            steam_appid="12345",
        )

        assert result["success"] is False
        assert "error" in result
        assert result["error"] == expected_result

    @pytest.mark.parametrize(
        "percentages_data, schema_data, expected_result",
        [
            (
                {
                    "achievementpercentages": {
                        "achievements": [{"name": "Mock_1", "percent": "12.3"}]
                    }
                },
                {},
                {
                    "achievements_count": 1,
                    "achievements_percentage_average": 12.3,
                    "achievements_list": [{"name": "Mock_1", "percent": 12.3}],
                },
            ),
            (
                {
                    "achievementpercentages": {
                        "achievements": [{"name": "Mock_1", "percent": "12.3"}]
                    }
                },
                {
                    "game": {
                        "availableGameStats": {
                            "achievements": [
                                {"name": "Mock_1", "displayName": "Mock One", "hidden": 1}
                            ]
                        }
                    }
                },
                {
                    "achievements_count": 1,
                    "achievements_percentage_average": 12.3,
                    "achievements_list": [
                        {
                            "name": "Mock_1",
                            "percent": 12.3,
                            "display_name": "Mock One",
                            "hidden": 1,
                            "description": None,
                        }
                    ],
                },
            ),
        ],
        ids=[
            "percentages_data_with_empty_schema_data",
            "percentages_data_with_correct_schema_data",
        ],
    )
    def test_transform_data_success(self, percentages_data, schema_data, expected_result):
        source = SteamAchievements()
        result = source._transform_data(data=percentages_data, schema_data=schema_data)

        assert len(result) == len(expected_result)
        assert result == expected_result

    @pytest.mark.parametrize(
        "percentages_data, schema_data, expected_result",
        [
            (
                {},
                {},
                {
                    "achievements_count": None,
                    "achievements_percentage_average": None,
                    "achievements_list": None,
                },
            ),
            (
                {"achievementpercentages": {"notachievements": [{"key_text": 1234}]}},
                {},
                {
                    "achievements_count": None,
                    "achievements_percentage_average": None,
                    "achievements_list": None,
                },
            ),
            (
                {"achievementpercentages": {"achievements": [{"key_text": 1234}]}},
                {},
                {
                    "achievements_count": 0,
                    "achievements_percentage_average": 0.0,
                    "achievements_list": [],
                },
            ),
            (
                {
                    "achievementpercentages": {
                        "achievements": [{"name": "Mock_1", "percent": "12.3"}]
                    }
                },
                {"game": {"availableGameStats": {"achievements": [{"wrong_key": "wrong_value"}]}}},
                {
                    "achievements_count": 1,
                    "achievements_percentage_average": 12.3,
                    "achievements_list": [
                        {
                            "name": "Mock_1",
                            "percent": 12.3,
                            "display_name": None,
                            "hidden": None,
                            "description": None,
                        }
                    ],
                },
            ),
            (
                {
                    "achievementpercentages": {
                        "achievements": [
                            {"name": "Mock_1", "percent": "12.3"},
                            {"name": "Mock_2", "percent": "12.3"},
                        ]
                    }
                },
                {
                    "game": {
                        "availableGameStats": {
                            "achievements": [
                                {"name": "Mock_1", "displayName": "Mock One", "hidden": 1},
                                {"wrong_key": "wrong_value"},
                            ]
                        }
                    }
                },
                {
                    "achievements_count": 2,
                    "achievements_percentage_average": 12.3,
                    "achievements_list": [
                        {
                            "name": "Mock_1",
                            "percent": 12.3,
                            "display_name": "Mock One",
                            "hidden": 1,
                            "description": None,
                        },
                        {
                            "name": "Mock_2",
                            "percent": 12.3,
                            "display_name": None,
                            "hidden": None,
                            "description": None,
                        },
                    ],
                },
            ),
        ],
        ids=[
            "no_percentages_data_no_schema_data",
            "incorrect_percentage_data_no_schema_data",
            "percentages_data_with_incorrect_achievements_structure_no_schema_data",
            "percentages_data_incorrect_schema_data_structure",
            "percentages_data_schema_data_with_incorrect_entry",
        ],
    )
    def test_transform_data_fail_cases(
        self,
        percentages_data,
        schema_data,
        expected_result,
    ):
        source = SteamAchievements()
        result = source._transform_data(data=percentages_data, schema_data=schema_data)

        assert len(result) == len(expected_result)
        assert result == expected_result

from unittest.mock import Mock

import pytest
import requests

from gameinsights.sources.base import BaseSource


@pytest.fixture
def mock_request_response(monkeypatch):
    """Factory fixture to mock a response and patch _make_request in the target class"""

    def _patch_method(
        target_class,
        method_name="_make_request",
        status_code: int = 200,
        json_data: dict | None = None,
        text_data: str | None = None,
        side_effect: list | None = None,
    ):
        class Response:
            def __init__(self, status_code, json_data, text_data):
                self.status_code = status_code
                self.ok = 200 <= status_code < 300
                self._json = json_data
                self._text = text_data or ""

            def json(self):
                return self._json

            @property
            def text(self):
                return self._text

            def raise_for_status(self):
                if not self.ok:
                    raise requests.HTTPError(f"Mock error {self.status_code}")

        if side_effect:
            responses = [
                Response(r.get("status_code", 200), r.get("json_data"), r.get("text_data"))
                for r in side_effect
            ]
            mock_method = Mock(side_effect=responses)
        else:
            mock_method = Mock(return_value=Response(status_code, json_data, text_data))

        monkeypatch.setattr(target_class, method_name, mock_method)

    return _patch_method


@pytest.fixture
def base_source_fixture():

    class _TestSource(BaseSource):
        _valid_labels = ("test_label_1", "test_label_2")
        _valid_labels_set = frozenset(_valid_labels)
        _base_url = "https://api.testurl.com/"

        def fetch(self, *args, **kwargs):
            pass

        def _transform_data(self, data):
            pass

    return _TestSource()


@pytest.fixture
def gamalytic_success_response_data():
    # since we allow impartial result and return pre-defined labels, no need to cover everything
    return {
        "steamId": "12345",
        "name": "Mock Game: The Adventure",
        "price": 12.34,
        "reviews": 1234,
        "reviewsSteam": 1234,
        "followers": 1234,
        "avgPlaytime": 12.34,
    }


@pytest.fixture
def hltb_success_response_data():
    data = """
    {
    "count": 1,
    "pageCurrent": 1,
    "pageTotal": 1,
    "pageSize": 20,
    "data": [
        {
        "game_id": 1234,
        "game_name": "Mock Game: The Adventure",
        "game_type": "game"
        }
    ]
    }
    """

    return data


@pytest.fixture
def hltb_success_but_not_found_data():
    data = """
    {
    "count": 0,
    "pageCurrent": 1,
    "pageTotal": 1,
    "pageSize": 20,
    "data": []
    }
    """

    return data


@pytest.fixture
def achievements_success_response_data():
    return {
        "achievementpercentages": {
            "achievements": [
                {"name": "Mock_1", "percent": "12.3"},
                {"name": "Mock_2", "percent": "12.3"},
            ]
        }
    }


@pytest.fixture
def achievements_success_with_unexpected_data():
    return {
        "achievementpercentages": {
            "achievements": [
                {"nama": "Mock_1", "percent": "12.3"},  # incorrect 'name' label
                {"name": "Mock_2", "percen": "12.3"},  # incorrect 'percent' label
                {"name": "Mock_3", "percent": "12.3"},  # correct label
            ]
        }
    }


@pytest.fixture
def scheme_success_response_data():
    return {
        "game": {
            "gameName": "Mock Game: The Adventure",
            "gameVersion": "1",
            "availableGameStats": {
                "achievements": [
                    {
                        "name": "Mock_1",
                        "defaultValue": 0,
                        "displayName": "Mock One",
                        "hidden": 0,
                        "description": "Clear Mock One",
                        "icon": "https://someurl.com",
                        "icongray": "https://anotherurl.com",
                    },
                    {
                        "name": "Mock_2",
                        "defaultValue": 0,
                        "displayName": "Mock Two",
                        "hidden": 1,
                        "icon": "https://someurl.com",
                        "icongray": "https://anotherurl.com",
                    },
                ]
            },
        }
    }


@pytest.fixture
def steamcharts_success_response_data():
    data = """
    <!DOCTYPE html>

    <html lang="en">
    <head>
    <meta charset="utf-8"/>
    <title>Mock Game - Steam Charts</title>
    </head>
    <body>
    <h1 id="app-title"><a href="">Mock Game: The Adventure</a></h1>
    <div class="app-stat">
    <span class="num">1234</span>
    <br/>playing <abbr class="timeago" title="1234-05-06T07:08:09Z"></abbr>
    </div>
    <div class="app-stat">
    <span class="num">4321</span>
    <br/>24-hour peak
        </div>
    <div class="app-stat">
    <span class="num">12345</span>
    <br/>all-time peak
        </div>
    </div>
    <div class="content">
    <table class="common-table">
    <thead>
    <tr>
    <th class="left">Month</th>
    <th class="right">Avg. Players</th>
    <th class="right">Gain</th>
    <th class="right">% Gain</th>
    <th class="right">Peak Players</th>
    </tr>
    </thead>
    <tbody>
    <tr class="odd">
    <td class="month-cell left italic">Last 30 Days</td>
    <td class="right num-f italic">123.45</td>
    <td class="right num-p gainorloss italic">-12.34</td>
    <td class="right gainorloss italic">-12.34%</td>
    <td class="right num italic">1234</td>
    </tr>
    <tr>
    <td class="month-cell left">June 1234</td>
    <td class="right num-f">123.45</td>
    <td class="right num-p gainorloss">12.34</td>
    <td class="right gainorloss">+12.34%</td>
    <td class="right num">12345</td>
    </tr>
    </tbody>
    </table>
    </div>
    </body>
    </html>
    """
    return data


@pytest.fixture
def steamcharts_error_response_no_app_title():
    data = """
    <!DOCTYPE html>

    <html lang="en">
    <head>
    <meta charset="utf-8"/>
    <title>Mock Game - Steam Charts</title>
    </head>
    <body>
    </div>
    </body>
    </html>
    """
    return data


@pytest.fixture
def steamcharts_error_response_incorrect_appstat_count():
    data = """
    <!DOCTYPE html>

    <html lang="en">
    <head>
    <meta charset="utf-8"/>
    <title>Mock Game - Steam Charts</title>
    </head>
    <body>
    <h1 id="app-title"><a href="">Mock Game: The Adventure</a></h1>
    <div class="app-stat">
    <span class="num">1234</span>
    <br/>playing <abbr class="timeago" title="1234-05-06T07:08:09Z"></abbr>
    </div>
    </body>
    </html>
    """
    return data


@pytest.fixture
def steamcharts_error_response_incorrect_appstat_structure():
    data = """
    <!DOCTYPE html>

    <html lang="en">
    <head>
    <meta charset="utf-8"/>
    <title>Mock Game - Steam Charts</title>
    </head>
    <body>
    <h1 id="app-title"><a href="">Mock Game: The Adventure</a></h1>
    <div class="app-stat">
    <span class="str">1234</span>
    <br/>playing <abbr class="timeago" title="1234-05-06T07:08:09Z"></abbr>
    </div>
    <div class="app-stat">
    <span class="str">4321</span>
    <br/>24-hour peak
        </div>
    <div class="app-stat">
    <span class="str">12345</span>
    <br/>all-time peak
        </div>
    </div>
    </body>
    </html>
    """
    return data


@pytest.fixture
def steamcharts_error_response_no_player_data_table():
    data = """
    <!DOCTYPE html>

    <html lang="en">
    <head>
    <meta charset="utf-8"/>
    <title>Mock Game - Steam Charts</title>
    </head>
    <body>
    <h1 id="app-title"><a href="">Mock Game: The Adventure</a></h1>
    <div class="app-stat">
    <span class="num">1234</span>
    <br/>playing <abbr class="timeago" title="1234-05-06T07:08:09Z"></abbr>
    </div>
    <div class="app-stat">
    <span class="num">4321</span>
    <br/>24-hour peak
        </div>
    <div class="app-stat">
    <span class="num">12345</span>
    <br/>all-time peak
        </div>
    </div>
    </body>
    </html>
    """
    return data


@pytest.fixture
def steamcharts_error_response_player_data_table_incorrect_structure():
    data = """
    <!DOCTYPE html>

    <html lang="en">
    <head>
    <meta charset="utf-8"/>
    <title>Mock Game - Steam Charts</title>
    </head>
    <body>
    <h1 id="app-title"><a href="">Mock Game: The Adventure</a></h1>
    <div class="app-stat">
    <span class="num">1234</span>
    <br/>playing <abbr class="timeago" title="1234-05-06T07:08:09Z"></abbr>
    </div>
    <div class="app-stat">
    <span class="num">4321</span>
    <br/>24-hour peak
        </div>
    <div class="app-stat">
    <span class="num">12345</span>
    <br/>all-time peak
        </div>
    </div>
    <div class="content">
    <table class="common-table">
    <thead>
    <tr>
    <th class="left">Month</th>
    <th class="right">Avg. Players</th>
    <th class="right">Gain</th>
    <th class="right">% Gain</th>
    </tr>
    </thead>
    <tbody>
    <tr class="odd">
    <td class="month-cell left italic">Last 30 Days</td>
    <td class="right num-f italic">123.45</td>
    <td class="right num-p gainorloss italic">-12.34</td>
    <td class="right gainorloss italic">-12.34%</td>
    </tr>
    <tr>
    <td class="month-cell left">June 1234</td>
    <td class="right num-f">123.45</td>
    <td class="right num-p gainorloss">12.34</td>
    <td class="right gainorloss">+12.34%</td>
    </tr>
    </tbody>
    </table>
    </div>
    </body>
    </html>
    """
    return data


@pytest.fixture
def steamspy_success_response_data():
    return {
        "appid": 12345,
        "name": "Mock Game: The Adventure",
        "positive": 1234,
        "negative": 12,
    }


@pytest.fixture
def steamspy_success_unexpected_data():
    return {
        "appid": 12345,
        "name": "Mock Game: The Adventure",
        "positive": [1234],
        "negative": 12,
        "tags": None,  # unexpected None value
    }


@pytest.fixture
def steamspy_not_found_response_data():
    return {
        "appid": 12345,
        "name": None,
        "developer": "",
        "publisher": "",
        "positive": 0,
        "negative": 0,
    }


@pytest.fixture
def steamstore_success_response_data():
    return {
        "12345": {
            "success": True,
            "data": {
                "type": "mock",
                "name": "Mock Game: The Adventure",
                "steam_appid": 12345,
                "ratings": {"pegi": {"rating": "12", "descriptors": "Bad Language"}},
            },
        }
    }


@pytest.fixture
def steamstore_success_partial_unexpected_data():
    return {
        "12345": {
            "success": True,
            "data": {
                "type": "mock",
                "name": "Mock Game: The Adventure",
                "steam_appid": 12345,
                "categories": [{"id": 1, "unexpected_label": "unexpected_value"}],
                "price_overview": [],  # unexpected data type
                "ratings": None,  # this as well
            },
        }
    }


@pytest.fixture
def steamstore_not_found_response_data():
    return {"12345": {"success": False}}


@pytest.fixture
def usersummary_success_response_open_profile():
    return {
        "response": {
            "players": [
                {
                    "steamid": "12345",
                    "communityvisibilitystate": 3,
                    "profilestate": 1,
                    "personaname": "Mock Player",
                    "profileurl": "https://mocksteam.com/profiles/12345",
                    "lastlogoff": 123456789,
                    "realname": "Mock Player The Third",
                    "timecreated": 123456789,
                    "loccountrycode": "MO",
                    "locstatecode": "CK",
                    "loccityid": 12,
                }
            ]
        }
    }


@pytest.fixture
def usersummary_success_response_closed_profile():
    return {
        "response": {
            "players": [
                {
                    "steamid": "12345",
                    "communityvisibilitystate": 1,
                    "profilestate": 1,
                    "personaname": "Private Mockو",
                    "profileurl": "https://mocksteam.com/profiles/12345",
                    "personastate": 0,
                }
            ]
        }
    }


@pytest.fixture
def usersummary_not_found_response_data():
    return {"response": {"players": []}}


@pytest.fixture
def owned_games_exclude_free_response():
    return {
        "response": {
            "game_count": 2,
            "games": [
                {"appid": 12345, "playtime_forever": 123},
                {"appid": 23456, "playtime_forever": 1234},
            ],
        }
    }


@pytest.fixture
def owned_games_include_free_response():
    return {
        "response": {
            "game_count": 3,
            "games": [
                {"appid": 12345, "playtime_forever": 123},
                {"appid": 23456, "playtime_forever": 1234},
                {"appid": 570, "playtime_forever": 12345},  # free game / Dota 2
            ],
        }
    }


@pytest.fixture
def owned_games_no_games_owned():
    return {"response": {}}


@pytest.fixture
def owned_games_only_own_free_games():
    return {
        "response": {
            "game_count": 1,
            "games": [
                {
                    "appid": 570,
                    "playtime_forever": 12345,
                }
            ],
        }
    }


@pytest.fixture
def recently_played_games_active_player_response_data():
    return {
        "response": {
            "total_count": 2,
            "games": [
                {
                    "appid": 12345,
                    "name": "Mock Game",
                    "playtime_2weeks": 12,
                    "playtime_forever": 123,
                },
                {
                    "appid": 23456,
                    "name": "Mock Online",
                    "playtime_2weeks": 1,
                    "playtime_forever": 1234,
                },
            ],
        }
    }


@pytest.fixture
def recently_played_games_free_player_response_data():
    return {
        "response": {
            "total_count": 1,
            "games": [
                {
                    "appid": 570,
                    "name": "Dota 2",
                    "playtime_2weeks": 1234,
                    "playtime_forever": 12345,
                }
            ],
        }
    }


@pytest.fixture
def recently_played_games_inactive_player_response_data():
    return {"response": {}}


@pytest.fixture
def review_initial_page():
    return {
        "success": 1,
        "query_summary": {
            "num_reviews": 2,
            "review_score": 5,
            "review_score_desc": "Mostly Positive",
            "total_positive": 2,
            "total_negative": 2,
            "total_reviews": 4,
        },
        "reviews": [
            {
                "recommendationid": "1",
                "author": {
                    "steamid": "1",
                    "num_games_owned": 1,
                    "num_reviews": 1,
                    "playtime_forever": 3,
                    "playtime_last_two_weeks": 0,
                    "playtime_at_review": 3,
                    "last_played": 12345,
                },
                "language": "english",
                "review": "mock review",
                "voted_up": True,
            },
            {
                "recommendationid": "2",
                "author": {
                    "steamid": "2",
                    "num_games_owned": 1,
                    "num_reviews": 1,
                    "playtime_forever": 2,
                    "playtime_last_two_weeks": 1,
                    "playtime_at_review": 2,
                    "last_played": 12345,
                },
                "language": "tchinese",
                "review": "mock review but in tchinese",
                "voted_up": False,
            },
        ],
        "cursor": "nextcursor",
    }


@pytest.fixture
def review_second_page():
    return {
        "success": 1,
        "query_summary": {
            "num_reviews": 2,
        },
        "reviews": [
            {
                "recommendationid": "3",
                "author": {
                    "steamid": "3",
                    "num_games_owned": 1,
                    "num_reviews": 1,
                    "playtime_forever": 3,
                    "playtime_last_two_weeks": 0,
                    "playtime_at_review": 3,
                    "last_played": 12345,
                },
                "language": "english",
                "review": "mock review",
                "voted_up": True,
            },
            {
                "recommendationid": "4",
                "author": {
                    "steamid": "4",
                    "num_games_owned": 1,
                    "num_reviews": 1,
                    "playtime_forever": 2,
                    "playtime_last_two_weeks": 1,
                    "playtime_at_review": 2,
                    "last_played": 12345,
                },
                "language": "schinese",
                "review": "another mock review",
                "voted_up": False,
            },
        ],
        "cursor": "nextcursor",
    }


@pytest.fixture
def review_error_not_found_response():
    return {"success": 1, "query_summary": {"num_reviews": 0}, "reviews": [], "cursor": None}


@pytest.fixture
def review_error_unsuccessful_response():
    return {"success": 0, "query_summary": {"num_reviews": 0}, "reviews": [], "cursor": None}


@pytest.fixture
def review_empty_response():
    return {
        "success": 1,
        "query_summary": {
            "num_reviews": 0,
            "review_score": 0,
            "review_score_desc": "No user reviews",
            "total_positive": 0,
            "total_negative": 0,
            "total_reviews": 0,
        },
        "reviews": [],
        "cursor": "*",
    }


@pytest.fixture
def review_only_tchinese():
    return {
        "success": 1,
        "query_summary": {
            "num_reviews": 1,
            "review_score": 0,
            "total_positive": 0,
            "total_negative": 1,
            "total_reviews": 1,
        },
        "reviews": [
            {
                "recommendationid": "2",
                "author": {
                    "steamid": "2",
                    "num_games_owned": 1,
                    "num_reviews": 1,
                    "playtime_forever": 3,
                    "playtime_last_two_weeks": 0,
                    "playtime_at_review": 3,
                    "last_played": 12345,
                },
                "language": "tchinese",
                "review": "mock review but in tchinese",
                "voted_up": False,
            },
        ],
        "cursor": "*",
    }


@pytest.fixture
def raw_data_normal():
    # normal raw_data with correct data type
    return {
        "steam_appid": "12345",
        "name": "Mock Game: The Adventure",
        "developers": ["devmock_1", "devmock_2"],
        "price_final": 12.34,
        "owners": 1234,
        "tags": ["RPG", "MOBA"],
        "average_playtime_h": 1234,
        "release_date": "Jan 1, 2025",
    }


@pytest.fixture
def raw_data_invalid_types():
    # raw_data with some invalid types
    return {
        "steam_appid": 23456,  # should be a string,
        "name": "mock game 2",  # correct type
        "developers": "devmock 3",  # should be a list of string
        "price_final": "12.34",  # should be a float
        "owners": "1234",  # should be an integer
        "tags": ["RPG", "MOBA"],
        "release_date": "Not a date",  # should be a None
    }


@pytest.fixture
def raw_data_missing_steam_appid():
    # I'm not sure if this is a valid case, but let's cover it
    return {
        "name": "mock game 3",
        "developers": ["devmock 4"],
        "price_final": 12.34,
        "owners": 1234,  # missing steam_appid
    }

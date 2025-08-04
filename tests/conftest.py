import pytest
import requests

from unittest.mock import Mock
from steamgamedata.sources.base import BaseSource

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
                Response(
                    r.get("status_code", 200),
                    r.get("json_data"),
                    r.get("text_data")
                )
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

        def fetch(self, *args, **kwargs): pass
        def _transform_data(self, data): pass

    return _TestSource()


@pytest.fixture
def gamalytic_success_response_data():
    # since we allow impartial result and return pre-defined labels, no need to cover everything
    return {
        "steamId": "12345",
        "name": 'mock_name',
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
        "game_name": "mock_name",
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
    "achievementpercentages":
        {
        "achievements":
            [
            {"name": "Mock_1", "percent": "12.3"},
            {"name": "Mock_2", "percent": "12.3"}
            ]
        }
    }

@pytest.fixture
def scheme_success_response_data():
    return {
        'game': {
            'gameName': 'Mock Game: The Adventure',
            'gameVersion': '1',
            'availableGameStats': {
                'achievements': [
                    {'name': 'Mock_1', 'defaultValue': 0, 'displayName': 'Mock One', 'hidden': 0, 'description': 'Clear Mock One', 'icon': 'https://someurl.com', 'icongray': 'https://anotherurl.com',},
                    {'name': 'Mock_2', 'defaultValue': 0, 'displayName': 'Mock Two', 'hidden': 1, 'icon': 'https://someurl.com', 'icongray': 'https://anotherurl.com',}
                ]
            }
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


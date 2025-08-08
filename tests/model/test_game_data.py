import pytest

from datetime import datetime
from pydantic import ValidationError
from steamgamedata.model.game_data import GameDataModel

class TestGameDataModel():
    def test_game_data_model_normal_data(self, raw_data_normal):
        game_data = GameDataModel(**raw_data_normal)

        # check if the model is created correctly
        assert isinstance(game_data, GameDataModel)

        # check if steam_appid is set correctly
        assert game_data.steam_appid == "12345"

        # check if release_date is converted to datetime
        assert isinstance(game_data.release_date, datetime)
        assert game_data.release_date == datetime(2025, 1, 1)

        # check if the model has all fields (50 fields, with the missing ones set to its default value)
        included_fields = {
            name for name, fields in GameDataModel.model_fields.items()
            if not fields.exclude
        }
        assert set(game_data.model_dump().keys()) == set(included_fields)

    def test_game_data_model_invalid_types(self, raw_data_invalid_types):
        game_data = GameDataModel(**raw_data_invalid_types)

        # check if the model is created correctly
        assert isinstance(game_data, GameDataModel)

        # check if relase_date is a datetime object
        assert game_data.release_date is None

        # check if average_playtime_h is NaN and average_playtime is None
        assert game_data.average_playtime_h != game_data.average_playtime_h # nan check
        assert game_data.average_playtime is None

        # check if steam_appid is set correctly
        assert isinstance(game_data.steam_appid, str)
        assert game_data.steam_appid == "23456"

        # check if "developers" is a list
        assert isinstance(game_data.developers, list)
        assert game_data.developers == ["devmock 3"]

        # check if "price_final" is a float
        assert isinstance(game_data.price_final, float)
        assert game_data.price_final == 12.34

        # check if "owners" is an integer
        assert isinstance(game_data.owners, int)
        assert game_data.owners == 1234

        # check if the model has all fields (50 fields, with the missing ones set to its default value)
        assert len(game_data.model_dump()) == 50

    def test_game_data_model_missing_steam_appid(self, raw_data_missing_steam_appid):
        # should raise a ValidationError if steam_appid is missing
        with pytest.raises(ValidationError):
            GameDataModel(**raw_data_missing_steam_appid)

    @pytest.mark.parametrize(
        "raw_data_fixture, expected_playtime, expected_days_since_release",
        [
            ("raw_data_normal", 1234 * 3600, (datetime.now() - datetime(2025, 1, 1)).days),
            ("raw_data_invalid_types", None, None),
        ],
        ids=[
            "normal_data",
            "missing_playtime_and_days_since_release"
        ]
    )
    def test_game_data_model_preprocess_data(
        self,
        request,
        raw_data_fixture,
        expected_playtime,
        expected_days_since_release,
    ):
        raw_data = request.getfixturevalue(raw_data_fixture)
        game_data = GameDataModel(**raw_data)

        # check if the model is created correctly
        assert isinstance(game_data, GameDataModel)

        # check if average_playtime is set correctly
        assert game_data.average_playtime == expected_playtime

        # check if days_since_release is set correctly
        assert game_data.days_since_release == expected_days_since_release

    def test_game_data_model_get_recap(self, raw_data_normal):
        game_data = GameDataModel(**raw_data_normal)

        # check if the recap data is correct
        recap_data = game_data.get_recap()
        assert isinstance(recap_data, dict)
        assert recap_data["steam_appid"] == "12345"
        assert recap_data["name"] == "Mock Game: The Adventure"
        assert recap_data["developers"] == ["devmock_1", "devmock_2"]
        assert recap_data["release_date"] == datetime(2025, 1, 1)
        assert recap_data["price_final"] == 12.34
        assert recap_data["owners"] == 1234
        assert recap_data["tags"] == ["RPG", "MOBA"]
        assert recap_data["average_playtime"] == 1234 * 3600 # check if conversion is a success
        assert recap_data["total_reviews"] == None # unset in raw data, should be None

        # check the length of the recap data
        assert len(recap_data) == 29
        assert "count_retired" not in recap_data # this field should not be in recap data

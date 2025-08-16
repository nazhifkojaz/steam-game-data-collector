import pytest
import requests

from gameinsights.sources import base
from gameinsights.sources.base import BaseSource


class TestBaseSource:
    @pytest.fixture
    def base_source_fixture(self):
        class _TestSource(BaseSource):
            _valid_labels = ("test_label_1", "test_label_2")
            _valid_labels_set = frozenset(_valid_labels)
            _base_url = "https://api.testurl.com/"

            def fetch(self, *args, **kwargs):
                pass

            def _transform_data(self, data):
                pass

        return _TestSource()

    @pytest.mark.parametrize(
        "selected_labels, valid_labels, expected",
        [
            # using default valid_labels (from fixture)
            (["test_label_1"], None, ["test_label_1"]),
            (["test_label_1", "invalid"], None, ["test_label_1"]),
            (["invalid"], None, []),
            # using custom valid_labels parameter
            (["custom_1"], ["custom_1", "custom_2"], ["custom_1"]),
            (["custom_1", "invalid"], ["custom_1", "custom_2"], ["custom_1"]),
            (["invalid"], ["custom_1"], []),
            # empty and all
            ([], None, []),
            (["test_label_1", "test_label_2"], None, ["test_label_1", "test_label_2"]),
        ],
    )
    def test_filter_valid_labels(
        self, base_source_fixture, selected_labels, valid_labels, expected
    ):
        """Test label filtering with various combinations"""
        if valid_labels is not None:
            result = base_source_fixture._filter_valid_labels(
                selected_labels=selected_labels, valid_labels=valid_labels
            )
        else:
            result = base_source_fixture._filter_valid_labels(selected_labels=selected_labels)

        assert isinstance(result, list)
        assert result == expected

    @pytest.mark.parametrize(
        "attempt, expected_result",
        [
            (
                [requests.exceptions.ConnectionError("fail 1"), {"json_data": {"ok": True}}],
                {"retries": 2, "status_code": 200},
            ),
            (
                [
                    requests.exceptions.Timeout("timeout 1"),
                    requests.exceptions.Timeout("timeout 2"),
                    {"json_data": {"ok": True}},
                ],
                {"retries": 3, "status_code": 200},
            ),
        ],
        ids=["connection_error_once", "timeout_twice"],
    )
    def test_make_request_retries_on_exception_to_retry(
        self, mock_request_response, base_source_fixture, attempt, expected_result
    ):
        mock_get = mock_request_response(
            target_class=requests, method_name="get", side_effect=attempt
        )
        result = base_source_fixture._make_request()

        assert result.status_code == expected_result["status_code"]
        assert mock_get.call_count == expected_result["retries"]

    def test_make_request_max_retries(self, mock_request_response, base_source_fixture):
        attempt = [
            requests.exceptions.Timeout("timeout 1"),
            requests.exceptions.Timeout("timeout 2"),
            requests.exceptions.Timeout("timeout 3"),
        ]
        mock_get = mock_request_response(
            target_class=requests, method_name="get", side_effect=attempt
        )
        result = base_source_fixture._make_request()

        assert mock_get.call_count == 3
        assert result.status_code == base.SYNTHETIC_ERROR_CODE
        assert not result.ok

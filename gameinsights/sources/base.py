import time
from abc import ABC, abstractmethod
from typing import Any, Literal, TypedDict
from urllib.parse import urljoin

import requests
from fake_useragent import UserAgent
from requests.exceptions import (
    ConnectionError,
    InvalidURL,
    RequestException,
    SSLError,
    Timeout,
    TooManyRedirects,
)

from gameinsights.utils import LoggerWrapper


class SuccessResult(TypedDict):
    success: Literal[True]
    data: dict[str, Any]


class ErrorResult(TypedDict):
    success: Literal[False]
    error: str


SourceResult = SuccessResult | ErrorResult

# a custom error code for the synthetic response
SYNTHETIC_ERROR_CODE = 599


class BaseSource(ABC):
    _base_url: str | None = None

    def __init__(self) -> None:
        """Initialize the base class for all its children."""
        self._logger = LoggerWrapper(self.__class__.__name__)

    @property
    def logger(self) -> "LoggerWrapper":
        return self._logger

    @property
    @abstractmethod
    def _valid_labels(self) -> tuple[str, ...]:
        """Get the valid labels for the data fetched from the source."""
        pass

    @property
    @abstractmethod
    def _valid_labels_set(self) -> frozenset[str]:
        """Get the valid labels as a frozenset for quick membership testing."""
        pass

    @property
    def valid_labels(self) -> tuple[str, ...]:
        """Get the valid labels for the data fetched from the source."""
        return self._valid_labels

    @abstractmethod
    def fetch(
        self, appid: str, verbose: bool = True, selected_labels: list[str] | None = None
    ) -> SuccessResult | ErrorResult:
        """Abstract method to fetch data from the source.

        Args:
            appid (str): The appid of the game to fetch data for.
            verbose (bool): If True, will log the fetching process.
            selected_labels (list[str] | None): A list of labels to filter the data.

        Returns:
            SuccessResult | ErrorResult: A dictionary containing the status, data, or any error message if applicable.
        """
        pass

    def _make_request(
        self,
        url: str | None = None,
        endpoint: str | None = None,
        headers: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        retries: int = 3,
        backoff_factor: float = 0.5,
        timeout: float | tuple[float, float] = (30, 60),
    ) -> requests.Response:
        """Default implementation for request.
        Args:
            url (str): Optional url if _base_url is not set
            endpoint (str): Optional path to append to base URL (e.g., steam_appid)
            headers (dict | None): Optional headers dictionary
            params (dict | None): Optional query parameters dictionary
            retries (int): Max number of retries
            backoff_factor (float): Multiplier for sleep/cooldown between retries
        Return:
            requests.Response: The response of the request call.
        """
        source_url = url if url else self._base_url
        final_url = source_url.rstrip("/")  # type: ignore[union-attr]
        if endpoint:
            final_url = urljoin(final_url + "/", endpoint.rstrip("/"))

        # add user-agent in params
        ua = UserAgent()
        params_ua = {"User-Agent": ua.random}
        if params is None:
            params = params_ua
        else:
            params.update(params_ua)

        exception_to_retry = (ConnectionError, Timeout)
        exception_to_abort = (
            InvalidURL,
            SSLError,
            TooManyRedirects,
        )

        for attempts in range(1, retries + 2):
            try:
                return requests.get(final_url, headers=headers, params=params, timeout=timeout)
            except exception_to_retry as e:
                if attempts < retries:
                    sleep_duration = backoff_factor * (2 ** (attempts - 1))  # the cooldown period
                    self.logger.log(
                        f"Encounter error {e}. Retrying in {sleep_duration: .1f}s. (Attempt {attempts+1} of {retries})",
                        level="warning",
                        verbose=True,
                    )
                    time.sleep(sleep_duration)
                    continue
                else:
                    return self._create_synthetic_response(url=final_url, reason=str(e))
            except exception_to_abort as e:
                self.logger.log(
                    f"Encounter fatal error {e}. Abort process..",
                    level="error",
                    verbose=True,
                )
                return self._create_synthetic_response(url=final_url, reason=str(e))
            except RequestException as e:
                self.logger.log(
                    f"Encounter unknown error {e}. Abort process..",
                    level="error",
                    verbose=True,
                )
                return self._create_synthetic_response(url=final_url, reason=str(e))

        return self._create_synthetic_response(url=final_url, reason="unexpected request error")

    def _create_synthetic_response(self, url: str, reason: str) -> requests.Response:
        """create a synthetic response to return"""
        response = requests.Response()
        response.status_code = SYNTHETIC_ERROR_CODE
        response._content = b""
        response.url = url
        response.reason = reason
        response.headers = {}  # type: ignore[assignment]
        return response

    @abstractmethod
    def _transform_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Repack and transform the data fetched from the source."""
        pass

    def _filter_valid_labels(
        self, selected_labels: list[str], valid_labels: list[str] | tuple[str, ...] | None = None
    ) -> list[str]:
        """Filter the selected labels to only include valid labels.

        Args:
            selected_labels (list[str]): A list of labels to filter.
            valid_labels (list[str] | tuple[str, ...] | None): Valid labels to compare with. If None, uses the class's valid labels.
        Returns:
            list[str]: A list of valid labels.
        """

        validation_set = (
            frozenset(valid_labels) if valid_labels is not None else self._valid_labels_set
        )

        valid: list[str] = []
        invalid: list[str] = []
        for label in selected_labels:
            (valid if label in validation_set else invalid).append(label)

        # log the invalid labels if any
        if invalid:
            reference_labels = valid_labels if valid_labels is not None else self._valid_labels
            self.logger.log(
                f"Ignoring the following invalid labels: {invalid}, valid labels are: {reference_labels}",
                level="warning",
                verbose=True,
            )

        return valid

    def _build_error_result(self, error_message: str, verbose: bool = True) -> ErrorResult:
        """Error message/returns handler.
        Args:
            error_message (str): Error Message.
            verbose (bool): If True, will log the error message. (Default to True)
        Returns:
            ErrorResult: A dictionary containing the ErrorResult.
        """
        self.logger.log(error_message, level="error", verbose=verbose)

        return ErrorResult(success=False, error=error_message)

import logging
from abc import ABC, abstractmethod
from typing import Any, Literal, TypedDict
from urllib.parse import urljoin

import requests


class SuccessResult(TypedDict):
    success: Literal[True]
    data: dict[str, Any]


class ErrorResult(TypedDict):
    success: Literal[False]
    error: str


SourceResult = SuccessResult | ErrorResult


class BaseSource(ABC):
    _base_url: str

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
        """Fetch game data from the source based on appid.

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
        endpoint: str | None = None,
        headers: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:
        """Default implementation for request
        Args:
            endpoint (str): Optional path to append to base URL (e.g., steam_appid)
            headers (dict | None): Optional headers dictionary
            params (dict | None): Optional query parameters dictionary
        Return:
            requests.Response: The response of the request call.
        """
        final_url = self._base_url.rstrip("/")  # remove trailing slash if any
        if endpoint:
            final_url = urljoin(final_url + "/", endpoint.rstrip("/"))
        return requests.get(final_url, headers=headers, params=params)

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
        Returns:
            list[str]: A list of valid labels.
        """

        validation_set = (
            frozenset(valid_labels) if valid_labels is not None else self._valid_labels_set
        )

        valid: list[str] = []
        invalid: list[str] = []
        for label in validation_set:
            (valid if label in validation_set else invalid).append(label)

        # log the invalid labels if any
        if invalid:
            reference_labels = valid_labels if valid_labels is not None else self._valid_labels
            self._log(
                f"Ignoring the following invalid labels: {invalid}, valid labels are: {reference_labels}",
                level="warning",
                verbose=True,
            )

        return valid

    @property
    def logger(self) -> logging.Logger:
        """initialize logger"""
        if not hasattr(self, "_logger"):
            self._logger = logging.getLogger(self.__class__.__name__)
            self._logger.propagate = False  # prevent logging from propagating to the root logger
            # avoid duplicate handler
            if not self._logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(logging.Formatter("%(levelname)s - %(name)s: %(message)s"))
                self._logger.addHandler(handler)
                self._logger.setLevel(logging.INFO)
        return self._logger

    def _log(self, message: str, level: str = "info", verbose: bool = False) -> None:
        """Log the message at the specified level.
        Args:
            message (str): The message to log.
            level (str): The logging level ('debug', 'info', 'warning', 'error', etc.).
            verbose (bool): If False, will not log the message
        """
        if verbose:
            getattr(self.logger, level.lower())(message)

    def _build_error_result(self, error_message: str, verbose: bool = True) -> ErrorResult:
        """Error message/returns handler.
        Args:
            error_message (str): Error Message.
            verbose (bool): If True, will log the error message. (Default to True)
        Returns:
            ErrorResult: A dictionary containing the ErrorResult.
        """
        self._log(error_message, level="error", verbose=verbose)

        return ErrorResult(success=False, error=error_message)

import logging
from abc import ABC, abstractmethod
from typing import Any, TypedDict


class SourceResult(TypedDict, total=False):
    success: bool
    data: dict[str, Any] | list[Any] | None
    error: str


class BaseSource(ABC):
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
    ) -> SourceResult:
        """Fetch game data from the source based on appid.

        Args:
            appid (str): The appid of the game to fetch data for.
            verbose (bool): If True, will log the fetching process.
            selected_labels (list[str] | None): A list of labels to filter the data.

        Returns:
            SourceResult: A dictionary containing the status, data, and any error message if applicable.
        """
        pass

    def _filter_valid_labels(self, selected_labels: list[str] | None) -> list[str]:
        """Filter the selected labels to only include valid labels.

        Args:
            selected_labels (list[str] | None): A list of labels to filter. If None, all valid labels will be used.
        Returns:
            list[str]: A list of valid labels.
        """
        if selected_labels is None:
            return list(self._valid_labels)

        valid = [label for label in selected_labels if label in self._valid_labels_set]
        invalid = [label for label in selected_labels if label not in self._valid_labels_set]

        # log the invalid labels if any
        if invalid:
            self._log(
                f"Ignoring the following invalid labels: {invalid}, valid labels are: {self._valid_labels}",
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

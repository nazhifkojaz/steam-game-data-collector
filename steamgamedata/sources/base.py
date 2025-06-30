import logging
from abc import ABC, abstractmethod
from typing import Any, TypedDict


class SourceResult(TypedDict, total=False):
    status: bool
    data: dict[str, Any] | list[Any] | None
    error: str


class BaseSource(ABC):
    @abstractmethod
    def fetch(self, appid: str, verbose: bool = True) -> SourceResult:
        """Fetch game data from the source based on appid.

        Args:
            appid (str): The appid of the game to fetch data for.

        Returns:
            SourceResult: A dictionary containing the status, data, and any error message if applicable.
        """
        pass

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

from abc import ABC, abstractmethod
from typing import Any, Optional, TypedDict, Union


class SourceResult(TypedDict, total=False):
    status: bool
    data: Union[dict[str, Any], list[Any], None]
    error: Optional[str]


class BaseSource(ABC):
    @abstractmethod
    def fetch(self, appid: str) -> SourceResult:
        """Fetch game data from the source based on appid.

        Args:
            appid (str): The appid of the game to fetch data for.

        Returns:
            SourceResult: A dictionary containing the status, data, and any error message if applicable.
        """
        pass

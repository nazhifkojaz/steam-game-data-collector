import logging


class LoggerWrapper:
    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)
        self._configure_logger()

    def _configure_logger(self) -> None:
        self._logger.propagate = False
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(levelname)s - %(name)s: %(message)s"))
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)

    def log(self, message: str, level: str = "info", verbose: bool = False) -> None:
        """Log the message at the specified level.
        Args:
            message (str): The message to log.
            level (str): The logging level ('debug', 'info', 'warning', 'error', etc.).
            verbose (bool): If False, will not log the message
        """
        if verbose:
            getattr(self._logger, level.lower())(message)

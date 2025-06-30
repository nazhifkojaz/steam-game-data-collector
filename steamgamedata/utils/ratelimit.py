import logging
import time
from functools import wraps
from typing import Any, Callable

from ratelimit import RateLimitException, limits

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def logged_sleep_and_retry(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        while True:
            try:
                return func(*args, **kwargs)
            except RateLimitException as e:
                logger.info(
                    f"[RateLimiter] Rate limit exceeded. "
                    f"Sleeping for {e.period_remaining:.2f}s before retrying..."
                )
                time.sleep(e.period_remaining)

    return wrapper


def logged_rate_limited(
    calls: int | None = None, period: int | None = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for rate limiting with logging.
    Args:
        calls (int): Max number of calls allowed.
        period (int): Time period in seconds for the rate limit.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            actual_calls = calls if calls is not None else getattr(self, "calls", 60)
            actual_period = period if period is not None else getattr(self, "period", 60)

            @logged_sleep_and_retry
            @limits(calls=actual_calls, period=actual_period)  # type: ignore[misc]
            def limited_execution() -> Any:
                return func(self, *args, **kwargs)

            return limited_execution()

        return wrapper

    return decorator

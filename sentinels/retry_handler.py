"""
retry_handler.py — Exponential backoff retry decorator for the AI Employee vault.

Usage:
    from sentinels.retry_handler import with_retry, TransientError

    @with_retry(max_attempts=3, base_delay=1, max_delay=60)
    def call_gmail_api():
        ...
"""

import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)


class TransientError(Exception):
    """Raised for errors that are safe to retry (network, rate limit, timeout)."""


class AuthenticationError(Exception):
    """Raised for expired/revoked credentials — do NOT retry, alert human."""


class DataError(Exception):
    """Raised for corrupted or missing data — quarantine and alert."""


class LogicError(Exception):
    """Raised when Claude misinterprets input or hits an invalid state — human review."""


def with_retry(max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """
    Decorator that retries a function on TransientError with exponential backoff.

    Args:
        max_attempts: Total attempts before re-raising (default 3).
        base_delay:   Initial delay in seconds (doubles each attempt).
        max_delay:    Cap on delay between retries (default 60s).

    Raises:
        TransientError: If all attempts are exhausted.
        Any other exception: Passed through immediately (no retry).

    Example:
        @with_retry(max_attempts=3, base_delay=2, max_delay=30)
        def fetch_data():
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except TransientError as e:
                    if attempt == max_attempts - 1:
                        logger.error(
                            "[retry_handler] %s failed after %d attempts: %s",
                            func.__name__,
                            max_attempts,
                            e,
                        )
                        raise
                    delay = min(base_delay * (2**attempt), max_delay)
                    logger.warning(
                        "[retry_handler] %s attempt %d/%d failed: %s — retrying in %.1fs",
                        func.__name__,
                        attempt + 1,
                        max_attempts,
                        e,
                        delay,
                    )
                    time.sleep(delay)

        return wrapper

    return decorator

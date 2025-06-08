"""
Error handling and retry logic for GitHub API interactions.

This module provides utilities for handling various types of errors that can occur
when interacting with GitHub's API, including network issues, rate limiting,
server errors, and GraphQL errors. It implements exponential backoff retry logic
and circuit breaker patterns for resilient API calls.
"""

import asyncio
import random
import time
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Callable, Dict, Optional

import httpx


class ErrorType(Enum):
    """Classification of different error types for retry logic."""

    NETWORK = "network"  # Connection timeouts, DNS failures
    TIMEOUT = "timeout"  # Request timeouts
    SERVER = "server"  # 5xx HTTP status codes
    CLIENT = "client"  # 4xx HTTP status codes (non-retryable)
    RATE_LIMIT = "rate_limit"  # GitHub API rate limiting
    GRAPHQL = "graphql"  # GraphQL-specific errors


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open and blocks a request."""

    pass


def classify_error(error: Exception) -> ErrorType:
    """
    Classify an exception to determine if it should be retried.

    Args:
        error: The exception to classify

    Returns:
        ErrorType indicating how the error should be handled
    """
    if isinstance(error, httpx.TimeoutException):
        # Timeout errors (TimeoutException subclasses RequestError)
        return ErrorType.TIMEOUT

    if isinstance(error, httpx.RequestError):
        # Network-level errors (connection issues, DNS failures)
        return ErrorType.NETWORK

    if isinstance(error, httpx.HTTPStatusError):
        status_code = error.response.status_code

        # Check for rate limiting first
        if status_code == 403 and _is_rate_limited(error.response):
            return ErrorType.RATE_LIMIT

        # Server errors (5xx) are typically retryable
        if 500 <= status_code < 600:
            return ErrorType.SERVER

        # Client errors (4xx) are typically not retryable
        if 400 <= status_code < 500:
            return ErrorType.CLIENT

    # GraphQL errors or other ValueError exceptions
    if isinstance(error, ValueError) and "GraphQL" in str(error):
        return ErrorType.GRAPHQL

    # Default to non-retryable for unknown errors
    return ErrorType.CLIENT


def _is_rate_limited(response: httpx.Response) -> bool:
    """Check if a response indicates rate limiting."""
    headers = response.headers

    # Handle case where headers might be a Mock object
    try:
        return (
            headers.get("x-ratelimit-remaining") == "0"
            or "retry-after" in headers
            or "rate limit" in getattr(response, "text", "").lower()
        )
    except (TypeError, AttributeError):
        # If headers is a Mock or doesn't support 'in' operator
        return headers.get("x-ratelimit-remaining") == "0"


def calculate_backoff_delay(
    attempt: int, base_delay: float = 1.0, max_delay: float = 60.0, jitter: bool = True
) -> float:
    """
    Calculate exponential backoff delay with optional jitter.

    Args:
        attempt: The attempt number (1, 2, 3, ...)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Whether to add random jitter to avoid thundering herd

    Returns:
        Delay in seconds
    """
    # Exponential backoff: base_delay * 2^(attempt-1)
    delay = base_delay * (2 ** (attempt - 1))

    # Add jitter (±25% variance, but ensure we don't go below base_delay)
    if jitter:
        jitter_range = delay * 0.25
        delay += random.uniform(-jitter_range, jitter_range)  # nosec B311
        # Ensure delay doesn't go below base_delay
        delay = max(base_delay, delay)

    # Cap at maximum delay (after jitter)
    delay = min(delay, max_delay)

    return max(0, delay)


def parse_rate_limit_reset(headers: Dict[str, str]) -> Optional[datetime]:
    """
    Parse rate limit reset time from response headers.

    Args:
        headers: HTTP response headers

    Returns:
        DateTime when rate limit resets, or None if not found
    """
    # Check for x-ratelimit-reset (Unix timestamp)
    if "x-ratelimit-reset" in headers:
        try:
            timestamp = int(headers["x-ratelimit-reset"])
            return datetime.utcfromtimestamp(timestamp)
        except (ValueError, OSError):
            pass

    # Check for retry-after (seconds)
    if "retry-after" in headers:
        try:
            seconds = int(headers["retry-after"])
            return datetime.utcnow() + timedelta(seconds=seconds)
        except ValueError:
            pass

    return None


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_errors: tuple = (
        ErrorType.NETWORK,
        ErrorType.TIMEOUT,
        ErrorType.SERVER,
        ErrorType.RATE_LIMIT,
    ),
):
    """
    Decorator that adds retry logic to async functions.

    Args:
        max_attempts: Maximum number of attempts
        base_delay: Base delay for exponential backoff
        max_delay: Maximum delay between retries
        retryable_errors: Tuple of ErrorType values that should be retried

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as error:
                    last_error = error
                    error_type = classify_error(error)

                    # Don't retry if error type is not retryable
                    if error_type not in retryable_errors:
                        raise

                    # Don't retry on last attempt
                    if attempt >= max_attempts:
                        raise

                    # Calculate delay
                    if error_type == ErrorType.RATE_LIMIT:
                        delay = _calculate_rate_limit_delay(error, base_delay)
                    else:
                        delay = calculate_backoff_delay(attempt, base_delay, max_delay)

                    # Wait before retry
                    await asyncio.sleep(delay)

            # This should never be reached, but just in case
            raise last_error

        return wrapper

    return decorator


def _calculate_rate_limit_delay(error: Exception, base_delay: float) -> float:
    """Calculate delay for rate limit errors."""
    if isinstance(error, httpx.HTTPStatusError):
        headers = error.response.headers
        reset_time = parse_rate_limit_reset(headers)

        if reset_time:
            # Wait until rate limit resets, plus a small buffer
            now = datetime.utcnow()
            if reset_time > now:
                return (reset_time - now).total_seconds() + 1

    # Fallback to base delay if we can't parse reset time
    return base_delay


class CircuitBreaker:
    """
    Circuit breaker implementation for resilient API calls.

    The circuit breaker has three states:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failing fast, requests are blocked
    - HALF_OPEN: Testing if service has recovered
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self._state = "closed"

    @property
    def state(self) -> str:
        """Get current circuit breaker state."""
        if self._state == "open" and self._should_attempt_reset():
            self._state = "half-open"
        return self._state

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return False
        return time.time() - self.last_failure_time > self.recovery_timeout

    def can_attempt(self) -> bool:
        """Check if a request can be attempted."""
        return self.state in ("closed", "half-open")

    def record_success(self):
        """Record a successful operation."""
        self.failure_count = 0
        self.last_failure_time = None
        self._state = "closed"

    def record_failure(self):
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self._state = "open"

    def protected(self, func: Callable) -> Callable:
        """
        Decorator that protects a function with circuit breaker logic.

        Args:
            func: Function to protect

        Returns:
            Protected function
        """

        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not self.can_attempt():
                raise CircuitBreakerError("Circuit breaker is open")

            try:
                result = await func(*args, **kwargs)
                self.record_success()
                return result
            except Exception:
                self.record_failure()
                raise

        return wrapper

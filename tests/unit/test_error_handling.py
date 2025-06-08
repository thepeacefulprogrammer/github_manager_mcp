"""
Unit tests for GitHub API error handling and retry logic.
"""

from datetime import datetime
from unittest.mock import Mock

import httpx
import pytest


class TestErrorClassification:
    """Test suite for error classification and handling."""

    def test_classify_retryable_http_errors(self):
        """Test classification of retryable HTTP errors."""
        from src.github_project_manager_mcp.utils.error_handling import (
            ErrorType,
            classify_error,
        )

        # Test network and timeout errors
        network_errors = [
            (httpx.RequestError("Connection timeout"), ErrorType.NETWORK),
            (httpx.TimeoutException("Request timeout"), ErrorType.TIMEOUT),
        ]

        for error, expected_type in network_errors:
            error_type = classify_error(error)
            assert error_type == expected_type

        # Test server errors (5xx)
        server_status_codes = [500, 502, 503, 504]
        for status_code in server_status_codes:
            response = Mock(status_code=status_code)
            response.headers = {}
            response.text = ""
            error = httpx.HTTPStatusError(
                f"Server Error {status_code}", request=Mock(), response=response
            )

            error_type = classify_error(error)
            assert error_type == ErrorType.SERVER

    def test_classify_non_retryable_http_errors(self):
        """Test classification of non-retryable HTTP errors."""
        from src.github_project_manager_mcp.utils.error_handling import (
            ErrorType,
            classify_error,
        )

        # Test non-retryable HTTP errors
        non_retryable_status_codes = [400, 401, 403, 404, 422]

        for status_code in non_retryable_status_codes:
            response = Mock(status_code=status_code)
            response.headers = {}  # Empty headers, no rate limiting
            response.text = ""
            error = httpx.HTTPStatusError(
                f"HTTP {status_code}", request=Mock(), response=response
            )

            error_type = classify_error(error)
            assert error_type == ErrorType.CLIENT

    def test_classify_rate_limit_errors(self):
        """Test classification of rate limit errors."""
        from src.github_project_manager_mcp.utils.error_handling import (
            ErrorType,
            classify_error,
        )

        # Test rate limit error with x-ratelimit-remaining: 0
        rate_limit_response = Mock(status_code=403)
        rate_limit_response.headers = {"x-ratelimit-remaining": "0"}
        rate_limit_response.text = ""
        rate_limit_error = httpx.HTTPStatusError(
            "Rate limit exceeded", request=Mock(), response=rate_limit_response
        )

        error_type = classify_error(rate_limit_error)
        assert error_type == ErrorType.RATE_LIMIT

    def test_classify_graphql_errors(self):
        """Test classification of GraphQL errors."""
        from src.github_project_manager_mcp.utils.error_handling import (
            ErrorType,
            classify_error,
        )

        # Test GraphQL errors
        graphql_error = ValueError("GraphQL errors: Bad credentials")
        error_type = classify_error(graphql_error)
        assert error_type == ErrorType.GRAPHQL


class TestRetryLogic:
    """Test suite for retry logic and exponential backoff."""

    def test_calculate_backoff_delay(self):
        """Test exponential backoff delay calculation."""
        from src.github_project_manager_mcp.utils.error_handling import (
            calculate_backoff_delay,
        )

        # Test exponential backoff without jitter for predictable results
        delay1 = calculate_backoff_delay(
            1, base_delay=1.0, max_delay=60.0, jitter=False
        )
        delay2 = calculate_backoff_delay(
            2, base_delay=1.0, max_delay=60.0, jitter=False
        )
        delay3 = calculate_backoff_delay(
            3, base_delay=1.0, max_delay=60.0, jitter=False
        )

        assert delay1 == 1.0  # 1 * 2^(1-1) = 1
        assert delay2 == 2.0  # 1 * 2^(2-1) = 2
        assert delay3 == 4.0  # 1 * 2^(3-1) = 4
        assert delay1 < delay2 < delay3

    def test_calculate_backoff_delay_with_jitter(self):
        """Test backoff delay includes jitter for avoiding thundering herd."""
        from src.github_project_manager_mcp.utils.error_handling import (
            calculate_backoff_delay,
        )

        # Multiple calls should return slightly different values due to jitter
        delays = [calculate_backoff_delay(2, base_delay=1.0) for _ in range(10)]
        assert len(set(delays)) > 1  # Should have variance due to jitter

    def test_calculate_backoff_delay_respects_max_delay(self):
        """Test that backoff delay respects maximum delay."""
        from src.github_project_manager_mcp.utils.error_handling import (
            calculate_backoff_delay,
        )

        # High attempt count should be capped at max_delay
        delay = calculate_backoff_delay(
            10, base_delay=1.0, max_delay=30.0, jitter=False
        )
        assert delay == 30.0

    def test_parse_rate_limit_reset_time(self):
        """Test parsing rate limit reset time from headers."""
        from src.github_project_manager_mcp.utils.error_handling import (
            parse_rate_limit_reset,
        )

        # Test with x-ratelimit-reset header (Unix timestamp)
        headers = {"x-ratelimit-reset": "1640995200"}  # 2022-01-01 00:00:00 UTC
        reset_time = parse_rate_limit_reset(headers)
        assert isinstance(reset_time, datetime)

        # Test with retry-after header (seconds)
        headers = {"retry-after": "60"}
        reset_time = parse_rate_limit_reset(headers)
        assert isinstance(reset_time, datetime)
        assert reset_time > datetime.utcnow()

    def test_parse_rate_limit_reset_time_no_headers(self):
        """Test parsing rate limit reset when no headers present."""
        from src.github_project_manager_mcp.utils.error_handling import (
            parse_rate_limit_reset,
        )

        reset_time = parse_rate_limit_reset({})
        assert reset_time is None


class TestRetryDecorator:
    """Test suite for retry decorator functionality."""

    @pytest.mark.asyncio
    async def test_retry_decorator_success_on_first_try(self):
        """Test retry decorator when function succeeds on first try."""
        from src.github_project_manager_mcp.utils.error_handling import with_retry

        call_count = 0

        @with_retry(max_attempts=3)
        async def test_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await test_function()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_decorator_success_after_retries(self):
        """Test retry decorator when function succeeds after retries."""
        from src.github_project_manager_mcp.utils.error_handling import with_retry

        call_count = 0

        @with_retry(max_attempts=3, base_delay=0.001)  # Fast for testing
        async def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.RequestError("Temporary network error")
            return "success"

        result = await test_function()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_decorator_exhausts_attempts(self):
        """Test retry decorator when all attempts are exhausted."""
        from src.github_project_manager_mcp.utils.error_handling import with_retry

        call_count = 0

        @with_retry(max_attempts=2, base_delay=0.001)
        async def test_function():
            nonlocal call_count
            call_count += 1
            raise httpx.RequestError("Persistent network error")

        with pytest.raises(httpx.RequestError):
            await test_function()
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_decorator_skips_non_retryable_errors(self):
        """Test retry decorator doesn't retry non-retryable errors."""
        from src.github_project_manager_mcp.utils.error_handling import with_retry

        call_count = 0

        @with_retry(max_attempts=3)
        async def test_function():
            nonlocal call_count
            call_count += 1
            # 401 is non-retryable
            response = Mock(status_code=401)
            raise httpx.HTTPStatusError(
                "Unauthorized", request=Mock(), response=response
            )

        with pytest.raises(httpx.HTTPStatusError):
            await test_function()
        assert call_count == 1  # Should not retry

    @pytest.mark.asyncio
    async def test_retry_decorator_handles_rate_limits(self):
        """Test retry decorator handles rate limit errors specially."""
        from src.github_project_manager_mcp.utils.error_handling import with_retry

        call_count = 0

        @with_retry(max_attempts=2, base_delay=0.001)
        async def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                response = Mock(status_code=403)
                response.headers = {"x-ratelimit-remaining": "0", "retry-after": "1"}
                raise httpx.HTTPStatusError(
                    "Rate limit", request=Mock(), response=response
                )
            return "success"

        result = await test_function()
        assert result == "success"
        assert call_count == 2


class TestCircuitBreaker:
    """Test suite for circuit breaker functionality."""

    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initializes correctly."""
        from src.github_project_manager_mcp.utils.error_handling import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=5, recovery_timeout=30.0)
        assert cb.failure_count == 0
        assert cb.state == "closed"
        assert cb.failure_threshold == 5
        assert cb.recovery_timeout == 30.0

    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures."""
        from src.github_project_manager_mcp.utils.error_handling import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=3)

        # Record failures
        for _ in range(3):
            cb.record_failure()

        assert cb.state == "open"
        assert cb.failure_count == 3

    def test_circuit_breaker_allows_retry_after_timeout(self):
        """Test circuit breaker allows retry after recovery timeout."""
        from src.github_project_manager_mcp.utils.error_handling import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.001)

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "open"

        # Wait for recovery timeout
        import time

        time.sleep(0.002)

        # Should transition to half-open
        assert cb.can_attempt()
        assert cb.state == "half-open"

    def test_circuit_breaker_resets_on_success(self):
        """Test circuit breaker resets failure count on success."""
        from src.github_project_manager_mcp.utils.error_handling import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=3)

        # Record some failures
        cb.record_failure()
        cb.record_failure()
        assert cb.failure_count == 2

        # Record success - should reset
        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state == "closed"

    @pytest.mark.asyncio
    async def test_circuit_breaker_decorator(self):
        """Test circuit breaker decorator functionality."""
        from src.github_project_manager_mcp.utils.error_handling import (
            CircuitBreaker,
            CircuitBreakerError,
        )

        cb = CircuitBreaker(failure_threshold=2)
        call_count = 0

        @cb.protected
        async def test_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        # First two calls should execute and fail
        with pytest.raises(ValueError):
            await test_function()
        with pytest.raises(ValueError):
            await test_function()

        # Third call should be blocked by circuit breaker
        with pytest.raises(CircuitBreakerError):
            await test_function()

        assert call_count == 2  # Function called twice, third blocked

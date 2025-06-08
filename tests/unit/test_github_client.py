"""
Unit tests for GitHub GraphQL API client.
"""

from unittest.mock import Mock, patch

import pytest


class TestGitHubClient:
    """Test suite for GitHub GraphQL client."""

    def test_github_client_initialization_with_token(self):
        """Test GitHub client initializes correctly with auth token."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        token = "test_token_123"
        client = GitHubClient(token=token)

        assert client.token == token
        assert client.base_url == "https://api.github.com/graphql"
        assert hasattr(client, "session")

    def test_github_client_initialization_without_token_raises_error(self):
        """Test GitHub client raises error when no token provided."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        with pytest.raises(ValueError, match="GitHub token is required"):
            GitHubClient(token=None)

    def test_github_client_initialization_with_custom_base_url(self):
        """Test GitHub client accepts custom base URL (for GitHub Enterprise)."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        custom_url = "https://github.enterprise.com/api/graphql"
        client = GitHubClient(token="test_token", base_url=custom_url)

        assert client.base_url == custom_url

    def test_github_client_sets_proper_headers(self):
        """Test GitHub client sets proper authorization and content headers."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        token = "test_token_123"
        client = GitHubClient(token=token)

        # Check that our specific headers are set correctly
        # (httpx adds additional headers, so we check individual ones)
        assert client.session.headers["authorization"] == f"Bearer {token}"
        assert client.session.headers["content-type"] == "application/json"
        assert client.session.headers["accept"] == "application/vnd.github.v4+json"

    @pytest.mark.asyncio
    async def test_github_client_has_async_query_method(self):
        """Test GitHub client has async query method."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token")

        # Should have an async query method
        assert hasattr(client, "query")
        assert callable(getattr(client, "query"))

    @pytest.mark.asyncio
    async def test_github_client_has_async_mutate_method(self):
        """Test GitHub client has async mutate method."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token")

        # Should have an async mutate method
        assert hasattr(client, "mutate")
        assert callable(getattr(client, "mutate"))

    def test_github_client_context_manager_support(self):
        """Test GitHub client supports async context manager protocol."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token")

        # Should have async context manager methods
        assert hasattr(client, "__aenter__")
        assert hasattr(client, "__aexit__")

    def test_github_client_has_close_method(self):
        """Test GitHub client has close method for cleanup."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token")

        # Should have close method
        assert hasattr(client, "close")
        assert callable(getattr(client, "close"))

    def test_github_client_initializes_with_rate_limiting_disabled_by_default(self):
        """Test GitHub client initializes with rate limiting disabled by default."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token")

        assert hasattr(client, "rate_limit_enabled")
        assert client.rate_limit_enabled is False
        assert hasattr(client, "requests_per_hour")
        assert client.requests_per_hour == 5000  # GitHub default

    def test_github_client_can_enable_rate_limiting(self):
        """Test GitHub client can be initialized with rate limiting enabled."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token", rate_limit_enabled=True)

        assert client.rate_limit_enabled is True

    def test_github_client_can_set_custom_rate_limit(self):
        """Test GitHub client can be initialized with custom rate limit."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        custom_limit = 1000
        client = GitHubClient(
            token="test_token", rate_limit_enabled=True, requests_per_hour=custom_limit
        )

        assert client.requests_per_hour == custom_limit

    def test_github_client_initializes_rate_limit_state(self):
        """Test GitHub client initializes rate limit tracking state."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token", rate_limit_enabled=True)

        assert hasattr(client, "remaining_requests")
        assert hasattr(client, "reset_time")
        assert hasattr(client, "request_timestamps")
        assert isinstance(client.request_timestamps, list)

    @pytest.mark.asyncio
    async def test_rate_limit_tracking_updates_remaining_requests(self):
        """Test rate limit tracking updates remaining requests from headers."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token", rate_limit_enabled=True)

        # Mock response with rate limit headers
        mock_response = Mock()
        mock_response.headers = {
            "x-ratelimit-remaining": "4999",
            "x-ratelimit-reset": "1640995200",
            "x-ratelimit-limit": "5000",
        }

        await client._update_rate_limit_state(mock_response)

        assert client.remaining_requests == 4999
        assert client.reset_time == 1640995200

    @pytest.mark.asyncio
    async def test_rate_limit_enforced_when_enabled(self):
        """Test rate limiting enforces delays when enabled."""
        import time

        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token", rate_limit_enabled=True)

        # Simulate being at rate limit
        client.requests_per_hour = 10  # Very low limit for testing

        # Fill up request history to exactly the limit
        current_time = time.time()
        client.request_timestamps = [
            current_time - i for i in range(10)  # 10 requests (at limit)
        ]

        # This should trigger rate limiting
        with patch("asyncio.sleep") as mock_sleep:
            await client._enforce_rate_limit()
            mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limit_not_enforced_when_disabled(self):
        """Test rate limiting is not enforced when disabled."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token", rate_limit_enabled=False)

        # This should not trigger any delays
        with patch("asyncio.sleep") as mock_sleep:
            await client._enforce_rate_limit()
            mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_rate_limit_cleans_old_timestamps(self):
        """Test rate limiting cleans up old request timestamps."""
        import time

        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token", rate_limit_enabled=True)

        current_time = time.time()
        # Add timestamps from over an hour ago and recent ones
        client.request_timestamps = [
            current_time - 7200,  # 2 hours ago (should be removed)
            current_time - 5400,  # 1.5 hours ago (should be removed)
            current_time - 1800,  # 30 minutes ago (should stay)
            current_time - 300,  # 5 minutes ago (should stay)
        ]

        await client._enforce_rate_limit()

        # Only recent timestamps should remain (less than 1 hour old)
        assert len(client.request_timestamps) == 3  # 2 old + 1 new from enforce call
        assert all(
            current_time - ts < 3700  # Account for the new timestamp added
            for ts in client.request_timestamps
        )

    @pytest.mark.asyncio
    async def test_query_method_enforces_rate_limiting(self):
        """Test query method enforces rate limiting when enabled."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token", rate_limit_enabled=True)

        # Mock the HTTP response properly
        mock_response = Mock()
        mock_response.json = Mock(return_value={"data": {"test": "data"}})
        mock_response.headers = {
            "x-ratelimit-remaining": "4999",
            "x-ratelimit-reset": "1640995200",
        }
        mock_response.raise_for_status = Mock()

        with patch.object(client, "_enforce_rate_limit") as mock_enforce:
            with patch.object(client.session, "post", return_value=mock_response):
                await client.query("{ viewer { login } }")

                mock_enforce.assert_called_once()

    @pytest.mark.asyncio
    async def test_mutate_method_enforces_rate_limiting(self):
        """Test mutate method enforces rate limiting when enabled."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token", rate_limit_enabled=True)

        # Mock the HTTP response properly
        mock_response = Mock()
        mock_response.json = Mock(return_value={"data": {"test": "data"}})
        mock_response.headers = {
            "x-ratelimit-remaining": "4999",
            "x-ratelimit-reset": "1640995200",
        }
        mock_response.raise_for_status = Mock()

        with patch.object(client, "_enforce_rate_limit") as mock_enforce:
            with patch.object(client.session, "post", return_value=mock_response):
                await client.mutate("mutation { test }")

                mock_enforce.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limit_calculates_correct_delay(self):
        """Test rate limiting calculates appropriate delay based on request rate."""
        import time

        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token", rate_limit_enabled=True)
        client.requests_per_hour = 10  # Very low limit for testing

        current_time = time.time()
        # Add exactly 10 requests (at the limit)
        client.request_timestamps = [current_time - (i * 60) for i in range(10)]

        with patch("asyncio.sleep") as mock_sleep:
            await client._enforce_rate_limit()

            # Should sleep since we're at the limit
            mock_sleep.assert_called_once()
            sleep_time = mock_sleep.call_args[0][0]
            assert sleep_time > 0  # Should sleep for some positive amount

    def test_github_client_has_rate_limit_methods(self):
        """Test GitHub client has all necessary rate limiting methods."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token", rate_limit_enabled=True)

        # Should have rate limiting methods
        assert hasattr(client, "_enforce_rate_limit")
        assert hasattr(client, "_update_rate_limit_state")
        assert hasattr(client, "get_rate_limit_status")

        assert callable(getattr(client, "_enforce_rate_limit"))
        assert callable(getattr(client, "_update_rate_limit_state"))
        assert callable(getattr(client, "get_rate_limit_status"))

    def test_get_rate_limit_status_returns_current_state(self):
        """Test get_rate_limit_status returns current rate limit information."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token", rate_limit_enabled=True)
        client.remaining_requests = 4500
        client.reset_time = 1640995200

        status = client.get_rate_limit_status()

        assert isinstance(status, dict)
        assert status["remaining"] == 4500
        assert status["reset_time"] == 1640995200
        assert status["limit"] == 5000
        assert "requests_in_last_hour" in status

    @pytest.mark.asyncio
    async def test_query_method_with_variables(self):
        """Test query method handles variables correctly."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token")

        # Mock the HTTP response
        mock_response = Mock()
        mock_response.json = Mock(return_value={"data": {"project": {"id": "123"}}})
        mock_response.headers = {}
        mock_response.raise_for_status = Mock()

        variables = {"projectId": "test-project-123", "first": 10}

        with patch.object(
            client.session, "post", return_value=mock_response
        ) as mock_post:
            result = await client.query(
                "query($projectId: ID!, $first: Int) { ... }", variables
            )

            # Verify the request was made correctly
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[1]["json"]["variables"] == variables
            assert result == {"project": {"id": "123"}}

    @pytest.mark.asyncio
    async def test_mutate_method_with_variables(self):
        """Test mutate method handles variables correctly."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token")

        # Mock the HTTP response
        mock_response = Mock()
        mock_response.json = Mock(
            return_value={"data": {"createProject": {"id": "new-123"}}}
        )
        mock_response.headers = {}
        mock_response.raise_for_status = Mock()

        variables = {"title": "New Project", "description": "Project description"}

        with patch.object(
            client.session, "post", return_value=mock_response
        ) as mock_post:
            result = await client.mutate(
                "mutation($title: String!, $description: String) { ... }", variables
            )

            # Verify the request was made correctly
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[1]["json"]["variables"] == variables
            assert result == {"createProject": {"id": "new-123"}}

    @pytest.mark.asyncio
    async def test_query_method_handles_graphql_errors(self):
        """Test query method properly handles GraphQL errors in response."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token")

        # Mock response with GraphQL errors
        mock_response = Mock()
        mock_response.json = Mock(
            return_value={
                "data": None,
                "errors": [
                    {"message": "Field 'invalid' doesn't exist on type 'Query'"},
                    {"message": "Variable '$projectId' is required but not provided"},
                ],
            }
        )
        mock_response.headers = {}
        mock_response.raise_for_status = Mock()

        with patch.object(client.session, "post", return_value=mock_response):
            with pytest.raises(ValueError) as exc_info:
                await client.query("query { invalid }")

            error_msg = str(exc_info.value)
            assert "GraphQL errors:" in error_msg
            assert "Field 'invalid' doesn't exist" in error_msg
            assert "Variable '$projectId' is required" in error_msg

    @pytest.mark.asyncio
    async def test_mutate_method_handles_graphql_errors(self):
        """Test mutate method properly handles GraphQL errors in response."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token")

        # Mock response with GraphQL errors
        mock_response = Mock()
        mock_response.json = Mock(
            return_value={
                "data": None,
                "errors": [{"message": "Resource not accessible by integration"}],
            }
        )
        mock_response.headers = {}
        mock_response.raise_for_status = Mock()

        with patch.object(client.session, "post", return_value=mock_response):
            with pytest.raises(ValueError) as exc_info:
                await client.mutate("mutation { createProject }")

            error_msg = str(exc_info.value)
            assert "GraphQL errors:" in error_msg
            assert "Resource not accessible by integration" in error_msg

    @pytest.mark.asyncio
    async def test_query_method_handles_http_errors(self):
        """Test query method handles HTTP errors correctly."""
        import httpx

        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token")

        # Mock HTTP error response
        mock_response = Mock()
        mock_response.raise_for_status = Mock(
            side_effect=httpx.HTTPStatusError(
                "401 Unauthorized", request=Mock(), response=Mock()
            )
        )

        with patch.object(client.session, "post", return_value=mock_response):
            with pytest.raises(httpx.HTTPStatusError):
                await client.query("query { viewer { login } }")

    @pytest.mark.asyncio
    async def test_mutate_method_handles_http_errors(self):
        """Test mutate method handles HTTP errors correctly."""
        import httpx

        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token")

        # Mock HTTP error response
        mock_response = Mock()
        mock_response.raise_for_status = Mock(
            side_effect=httpx.HTTPStatusError(
                "403 Forbidden", request=Mock(), response=Mock()
            )
        )

        with patch.object(client.session, "post", return_value=mock_response):
            with pytest.raises(httpx.HTTPStatusError):
                await client.mutate("mutation { createProject }")

    @pytest.mark.asyncio
    async def test_context_manager_properly_closes_session(self):
        """Test async context manager properly closes the session."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        async with GitHubClient(token="test_token") as client:
            assert hasattr(client, "session")
            assert client.session is not None
            # Session should be active during context
            assert not client.session.is_closed

        # Session should be closed after exiting context
        assert client.session.is_closed

    @pytest.mark.asyncio
    async def test_manual_close_method(self):
        """Test manual close method properly cleans up session."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token")
        assert not client.session.is_closed

        await client.close()
        assert client.session.is_closed

    @pytest.mark.asyncio
    async def test_rate_limit_state_update_with_missing_headers(self):
        """Test rate limit state update handles missing headers gracefully."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token", rate_limit_enabled=True)
        initial_reset = client.reset_time

        # Mock response with partial headers
        mock_response = Mock()
        mock_response.headers = {
            "x-ratelimit-remaining": "4000"
            # Missing x-ratelimit-reset
        }

        await client._update_rate_limit_state(mock_response)

        # Should update what's available
        assert client.remaining_requests == 4000
        # Should leave other values unchanged
        assert client.reset_time == initial_reset

    @pytest.mark.asyncio
    async def test_rate_limit_state_update_with_invalid_headers(self):
        """Test rate limit state update handles invalid header values gracefully."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token", rate_limit_enabled=True)

        # Mock response with invalid headers
        mock_response = Mock()
        mock_response.headers = {
            "x-ratelimit-remaining": "invalid_number",
            "x-ratelimit-reset": "not_a_timestamp",
        }

        # Should not crash on invalid values
        with pytest.raises(ValueError):
            await client._update_rate_limit_state(mock_response)

    def test_github_client_timeout_configuration(self):
        """Test GitHub client sets proper timeout configuration."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token")

        # Should have a reasonable timeout configured
        assert client.session.timeout.connect == 30.0
        assert client.session.timeout.read == 30.0
        assert client.session.timeout.write == 30.0
        assert client.session.timeout.pool == 30.0

    @pytest.mark.asyncio
    async def test_query_without_variables_omits_variables_field(self):
        """Test query method omits variables field when none provided."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token")

        # Mock the HTTP response
        mock_response = Mock()
        mock_response.json = Mock(
            return_value={"data": {"viewer": {"login": "testuser"}}}
        )
        mock_response.headers = {}
        mock_response.raise_for_status = Mock()

        with patch.object(
            client.session, "post", return_value=mock_response
        ) as mock_post:
            await client.query("query { viewer { login } }")

            # Verify the request payload doesn't include variables
            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert "variables" not in payload
            assert payload["query"] == "query { viewer { login } }"

    @pytest.mark.asyncio
    async def test_rate_limiting_disabled_skips_header_processing(self):
        """Test that rate limiting disabled skips processing rate limit headers."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token", rate_limit_enabled=False)

        # Mock response with rate limit headers
        mock_response = Mock()
        mock_response.json = Mock(return_value={"data": {"test": "data"}})
        mock_response.headers = {
            "x-ratelimit-remaining": "4999",
            "x-ratelimit-reset": "1640995200",
        }
        mock_response.raise_for_status = Mock()

        with patch.object(client.session, "post", return_value=mock_response):
            await client.query("{ test }")

            # Rate limit state should remain None since it's disabled
            assert client.remaining_requests is None
            assert client.reset_time is None

    def test_get_rate_limit_status_with_disabled_rate_limiting(self):
        """Test get_rate_limit_status when rate limiting is disabled."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        client = GitHubClient(token="test_token", rate_limit_enabled=False)

        status = client.get_rate_limit_status()

        assert status["enabled"] is False
        assert status["remaining"] is None
        assert status["reset_time"] is None
        assert status["requests_in_last_hour"] == 0

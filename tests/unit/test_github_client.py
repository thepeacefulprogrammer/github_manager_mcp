"""
Unit tests for GitHub GraphQL API client.
"""

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

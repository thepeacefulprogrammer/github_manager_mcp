"""
Test error handling for GitHub client initialization failures in search handlers.

Tests for Task 3.4: Update error handling for GitHub client initialization failures
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from github_project_manager_mcp.github_client import GitHubClient
from github_project_manager_mcp.handlers import project_search_handlers
from github_project_manager_mcp.utils.project_search import ProjectSearchManager


class TestSearchErrorHandling:
    """Test error handling for GitHub client initialization in search functionality."""

    def setup_method(self):
        """Set up test environment."""
        # Reset global state
        project_search_handlers.github_client = None
        project_search_handlers.search_manager = None
        project_search_handlers._search_manager_client_id = None

    def teardown_method(self):
        """Clean up after each test."""
        project_search_handlers.github_client = None
        project_search_handlers.search_manager = None
        project_search_handlers._search_manager_client_id = None

    @pytest.mark.asyncio
    async def test_search_projects_handler_returns_proper_error_when_client_not_initialized(
        self,
    ):
        """Test that search_projects_handler returns a proper user-friendly error when GitHub client is not initialized."""
        # Arrange - ensure github_client is None
        project_search_handlers.github_client = None
        arguments = {"query": "test", "limit": 10}

        # Act
        result = await project_search_handlers.search_projects_handler(arguments)

        # Assert
        assert result.isError is True
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        error_text = result.content[0].text
        assert "GitHub client not initialized" in error_text
        assert "Please check your GitHub token" in error_text
        # Should be user-friendly, not technical
        assert "ValueError" not in error_text
        assert "Exception" not in error_text

    @pytest.mark.asyncio
    async def test_search_projects_advanced_handler_returns_proper_error_when_client_not_initialized(
        self,
    ):
        """Test that search_projects_advanced_handler returns a proper user-friendly error when GitHub client is not initialized."""
        # Arrange - ensure github_client is None
        project_search_handlers.github_client = None
        arguments = {"search_config": {"query": "test"}}

        # Act
        result = await project_search_handlers.search_projects_advanced_handler(
            arguments
        )

        # Assert
        assert result.isError is True
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        error_text = result.content[0].text
        assert "GitHub client not initialized" in error_text
        assert "Please check your GitHub token" in error_text
        # Should be user-friendly, not technical
        assert "ValueError" not in error_text
        assert "Exception" not in error_text

    @pytest.mark.asyncio
    async def test_search_manager_initialization_failure_handled_gracefully(self):
        """Test that search manager initialization failures are handled gracefully with user-friendly errors."""
        # Arrange - set up a mock client that exists but causes search manager to fail
        mock_client = Mock(spec=GitHubClient)
        project_search_handlers.github_client = mock_client

        # Mock ProjectSearchManager to raise an exception during initialization
        with patch(
            "github_project_manager_mcp.handlers.project_search_handlers.ProjectSearchManager"
        ) as mock_manager_class:
            mock_manager_class.side_effect = RuntimeError(
                "Error initializing search functionality: GitHub API connection failed"
            )

            arguments = {"query": "test", "limit": 10}

            # Act
            result = await project_search_handlers.search_projects_handler(arguments)

            # Assert
            assert result.isError is True
            assert len(result.content) == 1
            assert result.content[0].type == "text"
            error_text = result.content[0].text
            # Should contain descriptive error information without exposing technical details
            assert "Error initializing search functionality" in error_text
            assert "Please check your GitHub token and try again" in error_text
            # Should not expose internal exception types directly
            assert "RuntimeError" not in error_text

    @pytest.mark.asyncio
    async def test_github_client_token_validation_error_handling(self):
        """Test error handling when GitHub client has invalid or expired token."""
        # Arrange - set up a mock client that appears valid but fails during search
        mock_client = Mock(spec=GitHubClient)
        project_search_handlers.github_client = mock_client

        # Mock search manager that fails with authentication error
        mock_search_manager = Mock()
        mock_search_manager.search_projects = AsyncMock(
            side_effect=Exception("Bad credentials: Invalid or expired token")
        )
        project_search_handlers.search_manager = mock_search_manager
        project_search_handlers._search_manager_client_id = id(mock_client)

        arguments = {"query": "test", "limit": 10}

        # Act
        result = await project_search_handlers.search_projects_handler(arguments)

        # Assert
        assert result.isError is True
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        error_text = result.content[0].text
        assert "Authentication failed" in error_text
        assert "Please check your GitHub token" in error_text
        assert "required permissions (project:read, read:org)" in error_text

    @pytest.mark.asyncio
    async def test_github_api_rate_limit_error_handling(self):
        """Test error handling when GitHub API rate limit is exceeded."""
        # Arrange
        mock_client = Mock(spec=GitHubClient)
        project_search_handlers.github_client = mock_client

        # Mock search manager that fails with rate limit error
        mock_search_manager = Mock()
        mock_search_manager.search_projects = AsyncMock(
            side_effect=Exception("API rate limit exceeded. Please try again later.")
        )
        project_search_handlers.search_manager = mock_search_manager
        project_search_handlers._search_manager_client_id = id(mock_client)

        arguments = {"query": "test", "limit": 10}

        # Act
        result = await project_search_handlers.search_projects_handler(arguments)

        # Assert
        assert result.isError is True
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        error_text = result.content[0].text
        assert "GitHub API rate limit exceeded" in error_text
        assert "Please wait a few minutes and try again" in error_text
        assert "Consider using a personal access token for higher limits" in error_text

    @pytest.mark.asyncio
    async def test_github_api_network_connection_error_handling(self):
        """Test error handling when network connection to GitHub API fails."""
        # Arrange
        mock_client = Mock(spec=GitHubClient)
        project_search_handlers.github_client = mock_client

        # Mock search manager that fails with network error
        mock_search_manager = Mock()
        mock_search_manager.search_projects = AsyncMock(
            side_effect=Exception("Connection timeout: Unable to reach GitHub API")
        )
        project_search_handlers.search_manager = mock_search_manager
        project_search_handlers._search_manager_client_id = id(mock_client)

        arguments = {"query": "test", "limit": 10}

        # Act
        result = await project_search_handlers.search_projects_handler(arguments)

        # Assert
        assert result.isError is True
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        error_text = result.content[0].text
        assert "Network connection error" in error_text
        assert "Unable to connect to GitHub API" in error_text
        assert "Check your internet connection and try again" in error_text

    @pytest.mark.asyncio
    async def test_github_permissions_error_handling(self):
        """Test error handling when GitHub token lacks required permissions."""
        # Arrange
        mock_client = Mock(spec=GitHubClient)
        project_search_handlers.github_client = mock_client

        # Mock search manager that fails with permissions error
        mock_search_manager = Mock()
        mock_search_manager.search_projects = AsyncMock(
            side_effect=Exception("Resource not accessible by integration")
        )
        project_search_handlers.search_manager = mock_search_manager
        project_search_handlers._search_manager_client_id = id(mock_client)

        arguments = {"query": "test", "limit": 10}

        # Act
        result = await project_search_handlers.search_projects_handler(arguments)

        # Assert
        assert result.isError is True
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        error_text = result.content[0].text
        assert "Permission denied" in error_text
        assert "GitHub token does not have required permissions" in error_text
        assert "project:read" in error_text
        assert "read:org" in error_text

    @pytest.mark.asyncio
    async def test_unexpected_exception_handling_with_logging(self):
        """Test that unexpected exceptions are properly handled, logged, and provide helpful error messages."""
        # Arrange
        mock_client = Mock(spec=GitHubClient)
        project_search_handlers.github_client = mock_client

        # Mock search manager to raise unexpected error during search
        mock_search_manager = Mock()
        mock_search_manager.search_projects = AsyncMock(
            side_effect=Exception("Unexpected internal error")
        )
        project_search_handlers.search_manager = mock_search_manager
        project_search_handlers._search_manager_client_id = id(mock_client)

        arguments = {"query": "test", "limit": 10}

        # Act
        with patch(
            "github_project_manager_mcp.handlers.project_search_handlers.logger"
        ) as mock_logger:
            result = await project_search_handlers.search_projects_handler(arguments)

            # Assert
            assert result.isError is True
            assert len(result.content) == 1
            assert result.content[0].type == "text"
            error_text = result.content[0].text
            assert "An unexpected error occurred" in error_text
            assert "Please try again" in error_text
            assert (
                "If the problem persists, check your GitHub token and network connection"
                in error_text
            )
            # Logger should have been called for debugging
            mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_client_reinitialization_error_handling(self):
        """Test error handling when client is reinitialized during search operation."""
        # Arrange
        mock_client_1 = Mock(spec=GitHubClient)
        mock_client_2 = Mock(spec=GitHubClient)

        # Set up initial client and search manager
        project_search_handlers.github_client = mock_client_1
        project_search_handlers.search_manager = Mock()
        project_search_handlers._search_manager_client_id = id(mock_client_1)

        # Simulate client change during search (race condition)
        async def client_change_during_search(*args, **kwargs):
            project_search_handlers.github_client = mock_client_2
            raise Exception("Client changed during operation")

        project_search_handlers.search_manager.search_projects = AsyncMock(
            side_effect=client_change_during_search
        )

        arguments = {"query": "test", "limit": 10}

        # Act
        result = await project_search_handlers.search_projects_handler(arguments)

        # Assert
        assert result.isError is True
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        error_text = result.content[0].text
        assert "Search operation was interrupted" in error_text
        assert "Please try again" in error_text

    def test_github_client_initialization_error_handling(self):
        """Test error handling during GitHub client initialization."""
        # This test simulates errors that might occur during client setup

        # Mock GitHubClient to raise an exception during initialization
        with patch(
            "github_project_manager_mcp.handlers.project_search_handlers.GitHubClient"
        ) as mock_client_class:
            mock_client_class.side_effect = Exception("Invalid token format")

            # Act & Assert - should handle initialization errors gracefully
            try:
                project_search_handlers.initialize_github_client("invalid-token")
                # If we get here, the error wasn't handled properly
                assert False, "Expected initialization error to be raised or handled"
            except Exception as e:
                # Should provide helpful error message
                assert "token" in str(e).lower()

    def test_github_client_initialization_preserves_existing_functionality(self):
        """Test that proper GitHub client initialization preserves existing functionality."""
        # Arrange
        test_token = "test_token_123"

        # Act
        project_search_handlers.initialize_github_client(test_token)

        # Assert
        assert project_search_handlers.github_client is not None
        assert isinstance(project_search_handlers.github_client, GitHubClient)
        assert project_search_handlers.github_client.token == test_token
        # Search manager should be reset when client changes
        assert project_search_handlers.search_manager is None
        assert project_search_handlers._search_manager_client_id is None

    @pytest.mark.asyncio
    async def test_search_manager_thread_safety_error_handling(self):
        """Test error handling for potential thread safety issues in search manager."""
        # Arrange
        mock_client_1 = Mock(spec=GitHubClient)
        mock_client_2 = Mock(spec=GitHubClient)

        # Set up initial client
        project_search_handlers.github_client = mock_client_1

        # Simulate concurrent access where client changes during search
        async def concurrent_client_change():
            project_search_handlers.github_client = mock_client_2

        # Mock search manager to detect client changes
        with patch(
            "github_project_manager_mcp.handlers.project_search_handlers.ProjectSearchManager"
        ) as mock_manager_class:
            mock_search_manager = Mock()
            mock_search_manager.search_projects = AsyncMock(
                return_value=Mock(projects=[], total_count=0, search_time_ms=10.0)
            )
            mock_manager_class.return_value = mock_search_manager

            arguments = {"query": "test", "limit": 10}

            # Act - simulate concurrent access
            await concurrent_client_change()
            result = await project_search_handlers.search_projects_handler(arguments)

            # Assert - should handle gracefully
            assert result.isError is False  # Should work with new client
            # Search manager should be recreated with new client
            mock_manager_class.assert_called_with(mock_client_2)

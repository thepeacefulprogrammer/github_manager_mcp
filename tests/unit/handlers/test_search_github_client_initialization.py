"""
Test GitHub client initialization for search handlers.

Tests for Task 3.1: Debug the "GitHub client not initialized" error in search_projects handler
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from github_project_manager_mcp.github_client import GitHubClient
from github_project_manager_mcp.handlers import project_search_handlers


class TestSearchGitHubClientInitialization:
    """Test GitHub client initialization for search functionality."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Reset global state before each test."""
        project_search_handlers.github_client = None
        project_search_handlers.search_manager = None
        project_search_handlers._search_manager_client_id = None

    def test_search_github_client_not_initialized_by_default(self):
        """Test that the search handlers' github_client is None by default."""
        # This should fail initially, showing the issue
        assert project_search_handlers.github_client is None

    def test_initialize_github_client_sets_global_client(self):
        """Test that initialize_github_client properly sets the global client."""
        # Arrange
        test_token = "test_token_123"

        # Act
        project_search_handlers.initialize_github_client(test_token)

        # Assert
        assert project_search_handlers.github_client is not None
        assert isinstance(project_search_handlers.github_client, GitHubClient)
        assert project_search_handlers.github_client.token == test_token

    @pytest.mark.asyncio
    async def test_search_projects_handler_fails_when_client_not_initialized(self):
        """Test that search_projects_handler returns error when GitHub client is not initialized."""
        # Arrange - ensure github_client is None
        project_search_handlers.github_client = None
        arguments = {"query": "test", "limit": 10}

        # Act
        result = await project_search_handlers.search_projects_handler(arguments)

        # Assert
        assert result.isError is True
        assert "GitHub client not initialized" in result.content[0].text

    @pytest.mark.asyncio
    async def test_search_projects_advanced_handler_fails_when_client_not_initialized(
        self,
    ):
        """Test that search_projects_advanced_handler returns error when GitHub client is not initialized."""
        # Arrange - ensure github_client is None
        project_search_handlers.github_client = None
        arguments = {"search_config": {"query": "test"}}

        # Act
        result = await project_search_handlers.search_projects_advanced_handler(
            arguments
        )

        # Assert
        assert result.isError is True
        assert "GitHub client not initialized" in result.content[0].text

    @pytest.mark.asyncio
    async def test_search_projects_handler_works_when_client_initialized(self):
        """Test that search_projects_handler works when GitHub client is properly initialized."""
        # Arrange
        mock_client = Mock(spec=GitHubClient)
        mock_search_manager = Mock()
        mock_search_result = Mock()
        mock_search_result.projects = []
        mock_search_result.total_count = 0
        mock_search_result.search_time_ms = 50.0
        mock_search_manager.search_projects = AsyncMock(return_value=mock_search_result)

        project_search_handlers.github_client = mock_client
        project_search_handlers.search_manager = mock_search_manager

        arguments = {"query": "test", "limit": 10}

        # Act
        result = await project_search_handlers.search_projects_handler(arguments)

        # Assert
        assert result.isError is False
        assert "No projects found" in result.content[0].text

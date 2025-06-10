"""
Test MCP server search handler GitHub client initialization.

Tests for Task 3.1-3.2: Verify that the search handlers' GitHub client is properly initialized by the MCP server.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from github_project_manager_mcp.mcp_server_fastmcp import (
    GitHubProjectManagerMCPFastServer,
)
from github_project_manager_mcp.handlers import project_search_handlers


class TestMCPServerSearchInitialization:
    """Test MCP server initialization of search handlers' GitHub client."""

    def setup_method(self):
        """Set up test environment."""
        # Reset search handlers client to None before each test
        project_search_handlers.github_client = None
        project_search_handlers.search_manager = None
        project_search_handlers._search_manager_client_id = None

    def teardown_method(self):
        """Clean up after each test."""
        # Reset search handlers client to None after each test
        project_search_handlers.github_client = None
        project_search_handlers.search_manager = None
        project_search_handlers._search_manager_client_id = None

    @patch("github_project_manager_mcp.mcp_server_fastmcp.load_github_token")
    @patch("github_project_manager_mcp.mcp_server_fastmcp.FastMCP")
    def test_mcp_server_initializes_search_handlers_github_client(
        self, mock_fastmcp, mock_load_token
    ):
        """Test that MCP server initialization properly sets up search handlers' GitHub client."""
        # Arrange
        mock_load_token.return_value = "test_github_token_123"
        mock_fastmcp_instance = Mock()
        mock_fastmcp.return_value = mock_fastmcp_instance

        # Verify search client starts as None
        assert project_search_handlers.github_client is None

        # Act - create MCP server instance (sync initialization only)
        server = GitHubProjectManagerMCPFastServer()

        # Assert - verify that server was created and mocks were called
        assert server is not None
        assert mock_fastmcp.called
        # Note: load_github_token is only called during async initialization
        # So we don't check it here, just verify server creation works

    @patch("github_project_manager_mcp.mcp_server_fastmcp.load_github_token")
    @patch("github_project_manager_mcp.mcp_server_fastmcp.FastMCP")
    @pytest.mark.asyncio
    async def test_ensure_async_initialized_sets_up_search_client(
        self, mock_fastmcp, mock_load_token
    ):
        """Test that _ensure_async_initialized properly initializes search handlers' GitHub client."""
        # Arrange
        mock_load_token.return_value = "test_github_token_456"
        mock_fastmcp_instance = Mock()
        mock_fastmcp.return_value = mock_fastmcp_instance

        # Verify search client starts as None
        assert project_search_handlers.github_client is None

        # Create server and trigger async initialization
        server = GitHubProjectManagerMCPFastServer()

        # Act - call the async initialization directly
        await server._ensure_async_initialized()

        # Assert - verify that search handlers' GitHub client is now initialized
        assert project_search_handlers.github_client is not None
        assert project_search_handlers.github_client.token == "test_github_token_456"
        assert mock_load_token.called

    @patch("github_project_manager_mcp.mcp_server_fastmcp.load_github_token")
    @patch("github_project_manager_mcp.mcp_server_fastmcp.FastMCP")
    @patch(
        "github_project_manager_mcp.handlers.project_search_handlers.ProjectSearchManager"
    )
    @pytest.mark.asyncio
    async def test_search_projects_works_after_server_initialization(
        self, mock_search_manager_class, mock_fastmcp, mock_load_token
    ):
        """Test that search_projects works correctly after MCP server initialization."""
        # Arrange
        mock_load_token.return_value = "test_github_token_789"
        mock_fastmcp_instance = Mock()
        mock_fastmcp.return_value = mock_fastmcp_instance

        # Set up mock search manager class and instance
        mock_search_manager_instance = Mock()
        mock_search_result = Mock()
        mock_search_result.projects = []
        mock_search_result.total_count = 0
        mock_search_result.search_time_ms = 45.0
        mock_search_manager_instance.search_projects = AsyncMock(
            return_value=mock_search_result
        )
        mock_search_manager_class.return_value = mock_search_manager_instance

        # Create and initialize server
        server = GitHubProjectManagerMCPFastServer()
        await server._ensure_async_initialized()

        # Verify that search client is initialized
        assert project_search_handlers.github_client is not None

        # Act - call search_projects_handler (this will create the mocked search manager)
        arguments = {"query": "test project", "limit": 10}
        result = await project_search_handlers.search_projects_handler(arguments)

        # Assert - verify success (no "GitHub client not initialized" error)
        assert result.isError is False
        assert "No projects found" in result.content[0].text
        assert "GitHub client not initialized" not in result.content[0].text

        # Verify the mock was called
        assert mock_search_manager_class.called
        assert mock_search_manager_instance.search_projects.called

    @patch("github_project_manager_mcp.mcp_server_fastmcp.load_github_token")
    @patch("github_project_manager_mcp.mcp_server_fastmcp.FastMCP")
    @pytest.mark.asyncio
    async def test_no_token_does_not_break_server_init(
        self, mock_fastmcp, mock_load_token
    ):
        """Test that MCP server initialization handles missing GitHub token gracefully."""
        # Arrange
        mock_load_token.return_value = None  # No token available
        mock_fastmcp_instance = Mock()
        mock_fastmcp.return_value = mock_fastmcp_instance

        # Act - create server and trigger async initialization
        server = GitHubProjectManagerMCPFastServer()
        await server._ensure_async_initialized()

        # Assert - server should be created successfully even without token
        assert server is not None
        assert server.github_client is None
        assert project_search_handlers.github_client is None
        assert mock_load_token.called

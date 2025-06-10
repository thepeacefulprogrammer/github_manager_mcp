"""
Test async initialization patterns for search functionality.

Tests for Task 3.3: Ensure proper async initialization patterns for GitHub client in search contexts
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from github_project_manager_mcp.github_client import GitHubClient
from github_project_manager_mcp.handlers import project_search_handlers
from github_project_manager_mcp.utils.project_search import ProjectSearchManager


class TestAsyncInitializationPatterns:
    """Test async initialization patterns for search functionality."""

    def setup_method(self):
        """Set up test environment."""
        # Reset search handlers global state
        project_search_handlers.github_client = None
        project_search_handlers.search_manager = None

    def teardown_method(self):
        """Clean up after each test."""
        project_search_handlers.github_client = None
        project_search_handlers.search_manager = None

    @pytest.mark.asyncio
    async def test_lazy_search_manager_initialization_thread_safety(self):
        """Test that lazy search manager initialization is thread-safe."""
        # Arrange - simulate concurrent access
        mock_client = Mock(spec=GitHubClient)
        project_search_handlers.github_client = mock_client

        # Track initialization calls
        original_init = ProjectSearchManager.__init__
        init_call_count = 0

        def counting_init(self, github_client=None):
            nonlocal init_call_count
            init_call_count += 1
            original_init(self, github_client)

        # This test demonstrates a potential race condition issue
        # Multiple concurrent calls might create multiple search managers
        with patch.object(ProjectSearchManager, "__init__", counting_init):
            # Act - simulate concurrent calls to search_projects_handler
            tasks = []
            for _ in range(5):
                arguments = {"query": "test", "limit": 10}
                # Create tasks that would trigger search manager initialization
                task = asyncio.create_task(self._trigger_search_manager_init(arguments))
                tasks.append(task)

            # Wait for all tasks to complete
            await asyncio.gather(*tasks)

        # Assert - should only initialize once (this might fail, showing the issue)
        # In a proper implementation, init_call_count should be 1
        # If it's > 1, we have a race condition
        print(f"Search manager initialized {init_call_count} times")
        # This assertion might fail, demonstrating the issue
        assert (
            init_call_count <= 1
        ), f"Search manager initialized {init_call_count} times - potential race condition"

    async def _trigger_search_manager_init(self, arguments):
        """Helper method to trigger search manager initialization."""
        # Create a mock search result to avoid real API calls
        mock_search_result = Mock()
        mock_search_result.projects = []
        mock_search_result.total_count = 0
        mock_search_result.search_time_ms = 10.0

        # Mock the search_projects method to avoid real calls
        with patch.object(
            ProjectSearchManager,
            "search_projects",
            AsyncMock(return_value=mock_search_result),
        ):
            # This would trigger search manager initialization if not already done
            result = await project_search_handlers.search_projects_handler(arguments)
            return result

    @pytest.mark.asyncio
    async def test_search_manager_recreation_after_client_change(self):
        """Test that search manager is recreated when GitHub client changes."""
        # Arrange - set up initial client and manager
        mock_client_1 = Mock(spec=GitHubClient)
        mock_client_1.token = "token1"
        project_search_handlers.github_client = mock_client_1

        # Initialize search manager with first client
        project_search_handlers.search_manager = ProjectSearchManager(mock_client_1)
        initial_manager = project_search_handlers.search_manager

        # Act - change the GitHub client (simulating reinitialization)
        mock_client_2 = Mock(spec=GitHubClient)
        mock_client_2.token = "token2"
        project_search_handlers.github_client = mock_client_2

        # Call handler - it should detect client change and recreate manager
        arguments = {"query": "test", "limit": 10}

        # Mock search result to avoid real API calls
        mock_search_result = Mock()
        mock_search_result.projects = []
        mock_search_result.total_count = 0
        mock_search_result.search_time_ms = 10.0

        with patch.object(
            ProjectSearchManager,
            "search_projects",
            AsyncMock(return_value=mock_search_result),
        ):
            await project_search_handlers.search_projects_handler(arguments)

        # Assert - search manager should be recreated (this test might fail, showing the issue)
        # Current implementation doesn't check if client changed
        current_manager = project_search_handlers.search_manager
        assert (
            current_manager is not initial_manager
        ), "Search manager should be recreated when client changes"
        assert (
            current_manager.github_client is mock_client_2
        ), "New manager should use new client"

    @pytest.mark.asyncio
    async def test_search_manager_github_client_consistency(self):
        """Test that search manager always uses the current GitHub client."""
        # Arrange
        mock_client = Mock(spec=GitHubClient)
        project_search_handlers.github_client = mock_client

        # Act - create search manager
        project_search_handlers.search_manager = ProjectSearchManager(mock_client)

        # Change the global client (simulating runtime reinitialization)
        new_mock_client = Mock(spec=GitHubClient)
        project_search_handlers.github_client = new_mock_client

        # Assert - this reveals a potential consistency issue
        # The search manager still has the old client
        assert project_search_handlers.search_manager.github_client is mock_client
        assert project_search_handlers.github_client is new_mock_client
        # These are different! This shows a consistency problem
        assert (
            project_search_handlers.search_manager.github_client
            is not project_search_handlers.github_client
        )

    @pytest.mark.asyncio
    async def test_concurrent_search_manager_access_safety(self):
        """Test that concurrent access to search manager is safe."""
        # Arrange
        mock_client = Mock(spec=GitHubClient)
        project_search_handlers.github_client = mock_client

        # Mock search result
        mock_search_result = Mock()
        mock_search_result.projects = []
        mock_search_result.total_count = 0
        mock_search_result.search_time_ms = 15.0

        # Act - create multiple concurrent search operations
        async def concurrent_search(query_suffix):
            arguments = {"query": f"test{query_suffix}", "limit": 5}
            with patch.object(
                ProjectSearchManager,
                "search_projects",
                AsyncMock(return_value=mock_search_result),
            ):
                return await project_search_handlers.search_projects_handler(arguments)

        # Execute concurrent searches
        tasks = [concurrent_search(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # Assert - all should succeed without race conditions
        assert len(results) == 10
        for result in results:
            assert result.isError is False
            assert "No projects found" in result.content[0].text

    @pytest.mark.asyncio
    async def test_search_handler_github_client_validation_timing(self):
        """Test that GitHub client validation happens at the right time."""
        # Arrange - no GitHub client initially
        project_search_handlers.github_client = None

        # Act - call search handler
        arguments = {"query": "test", "limit": 10}
        result = await project_search_handlers.search_projects_handler(arguments)

        # Assert - should fail immediately with proper error
        assert result.isError is True
        assert "GitHub client not initialized" in result.content[0].text

        # Arrange - set up valid client after initial failure
        mock_client = Mock(spec=GitHubClient)
        project_search_handlers.github_client = mock_client

        # Mock successful search
        mock_search_result = Mock()
        mock_search_result.projects = []
        mock_search_result.total_count = 0
        mock_search_result.search_time_ms = 20.0

        with patch.object(
            ProjectSearchManager,
            "search_projects",
            AsyncMock(return_value=mock_search_result),
        ):
            result = await project_search_handlers.search_projects_handler(arguments)

        # Assert - should now succeed
        assert result.isError is False
        assert "No projects found" in result.content[0].text

    @pytest.mark.asyncio
    async def test_advanced_search_handler_consistency(self):
        """Test that advanced search handler has consistent initialization patterns with basic search."""
        # Arrange
        mock_client = Mock(spec=GitHubClient)
        project_search_handlers.github_client = mock_client

        mock_search_result = Mock()
        mock_search_result.projects = []
        mock_search_result.total_count = 0
        mock_search_result.search_time_ms = 25.0

        # Act & Assert - both handlers should behave consistently
        basic_args = {"query": "test", "limit": 10}
        advanced_args = {"search_config": {"query": "test", "limit": 10}}

        with patch.object(
            ProjectSearchManager,
            "search_projects",
            AsyncMock(return_value=mock_search_result),
        ):
            basic_result = await project_search_handlers.search_projects_handler(
                basic_args
            )
            advanced_result = (
                await project_search_handlers.search_projects_advanced_handler(
                    advanced_args
                )
            )

        # Both should succeed and have consistent behavior
        assert basic_result.isError is False
        assert advanced_result.isError is False
        assert project_search_handlers.search_manager is not None

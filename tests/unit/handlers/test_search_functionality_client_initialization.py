"""
Unit tests for search functionality with proper GitHub client initialization.

These tests verify that the search functionality works correctly when the GitHub client
is properly initialized, including various search scenarios, parameter validation,
and edge cases.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from github_project_manager_mcp.handlers import project_search_handlers
from github_project_manager_mcp.utils.project_search import (
    ProjectSearchFilter,
    ProjectSearchResult,
)


class TestSearchFunctionalityClientInitialization:
    """Test search functionality with proper client initialization."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Reset global state before each test."""
        project_search_handlers.github_client = None
        project_search_handlers.search_manager = None
        project_search_handlers._search_manager_client_id = None

    @pytest.fixture
    def mock_github_client(self):
        """Create a mock GitHub client."""
        mock_client = MagicMock()
        mock_client.token = "test_token"
        return mock_client

    @pytest.fixture
    def mock_search_manager(self):
        """Create a mock search manager."""
        mock_manager = AsyncMock()
        return mock_manager

    @pytest.fixture
    def sample_search_result(self):
        """Create a sample search result for testing."""
        return ProjectSearchResult(
            projects=[
                {
                    "id": "PVTI_123",
                    "title": "Test Project 1",
                    "shortDescription": "Test description 1",
                    "public": True,
                    "owner": "testuser",
                    "createdAt": "2024-01-01T00:00:00Z",
                    "updatedAt": "2024-01-02T00:00:00Z",
                },
                {
                    "id": "PVTI_456",
                    "title": "Test Project 2",
                    "shortDescription": "Test description 2",
                    "public": False,
                    "owner": "testuser",
                    "createdAt": "2024-01-01T00:00:00Z",
                    "updatedAt": "2024-01-02T00:00:00Z",
                },
            ],
            total_count=2,
            search_time_ms=50.5,
            has_next_page=False,
        )

    async def test_search_projects_handler_successful_search_with_initialized_client(
        self, mock_github_client, mock_search_manager, sample_search_result
    ):
        """Test successful search with properly initialized client."""
        # Arrange
        project_search_handlers.github_client = mock_github_client

        with patch(
            "github_project_manager_mcp.handlers.project_search_handlers.ProjectSearchManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_search_manager
            mock_search_manager.search_projects.return_value = sample_search_result

            arguments = {
                "query": "test project",
                "limit": 10,
                "sort_by": "updated",
                "sort_order": "desc",
            }

            # Act
            result = await project_search_handlers.search_projects_handler(arguments)

            # Assert
            assert not result.isError
            content_text = result.content[0].text
            assert "Found 2 project(s)" in content_text
            assert "Test Project 1" in content_text
            assert "Test Project 2" in content_text
            assert "ID: `PVTI_123`" in content_text
            assert "ID: `PVTI_456`" in content_text
            assert "searched in 50.5ms" in content_text

    async def test_search_projects_handler_with_all_parameters(
        self, mock_github_client, mock_search_manager, sample_search_result
    ):
        """Test search with all possible parameters."""
        # Arrange
        project_search_handlers.github_client = mock_github_client

        with patch(
            "github_project_manager_mcp.handlers.project_search_handlers.ProjectSearchManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_search_manager
            mock_search_manager.search_projects.return_value = sample_search_result

            arguments = {
                "query": "test",
                "visibility": "public",
                "owner": "testuser",
                "created_after": "2024-01-01",
                "created_before": "2024-12-31",
                "updated_after": "2024-01-01T00:00:00Z",
                "updated_before": "2024-12-31T23:59:59Z",
                "limit": 50,
                "sort_by": "name",
                "sort_order": "asc",
            }

            # Act
            result = await project_search_handlers.search_projects_handler(arguments)

            # Assert
            assert not result.isError
            # Verify that ProjectSearchFilter was called with correct parameters
            mock_search_manager.search_projects.assert_called_once()
            call_args = mock_search_manager.search_projects.call_args[0][0]
            assert isinstance(call_args, ProjectSearchFilter)
            assert call_args.query == "test"
            assert call_args.visibility == "public"
            assert call_args.owner == "testuser"
            assert call_args.limit == 50
            assert call_args.sort_by == "name"
            assert call_args.sort_order == "asc"

    async def test_search_projects_handler_empty_results(
        self, mock_github_client, mock_search_manager
    ):
        """Test search that returns no results."""
        # Arrange
        project_search_handlers.github_client = mock_github_client

        empty_result = ProjectSearchResult(
            projects=[],
            total_count=0,
            search_time_ms=25.3,
            has_next_page=False,
        )

        with patch(
            "github_project_manager_mcp.handlers.project_search_handlers.ProjectSearchManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_search_manager
            mock_search_manager.search_projects.return_value = empty_result

            arguments = {"query": "nonexistent"}

            # Act
            result = await project_search_handlers.search_projects_handler(arguments)

            # Assert
            assert not result.isError
            content_text = result.content[0].text
            assert "No projects found" in content_text
            assert "searched in 25.3ms" in content_text

    async def test_search_projects_handler_pagination_info(
        self, mock_github_client, mock_search_manager
    ):
        """Test search with pagination information."""
        # Arrange
        project_search_handlers.github_client = mock_github_client

        paginated_result = ProjectSearchResult(
            projects=[
                {
                    "id": "PVTI_123",
                    "title": "Test Project 1",
                    "shortDescription": "Test description 1",
                    "public": True,
                    "owner": "testuser",
                    "createdAt": "2024-01-01T00:00:00Z",
                    "updatedAt": "2024-01-02T00:00:00Z",
                }
            ],
            total_count=50,
            search_time_ms=100.7,
            has_next_page=True,
        )

        with patch(
            "github_project_manager_mcp.handlers.project_search_handlers.ProjectSearchManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_search_manager
            mock_search_manager.search_projects.return_value = paginated_result

            arguments = {"limit": 1}

            # Act
            result = await project_search_handlers.search_projects_handler(arguments)

            # Assert
            assert not result.isError
            content_text = result.content[0].text
            assert "Found 50 project(s)" in content_text
            assert "Showing first 1 of 50 results" in content_text
            assert "Use pagination parameters to see more results" in content_text

    async def test_search_projects_handler_parameter_validation_errors(
        self, mock_github_client, mock_search_manager
    ):
        """Test parameter validation errors."""
        # Arrange
        project_search_handlers.github_client = mock_github_client

        test_cases = [
            ({"limit": 0}, "must be between 1 and 100"),
            ({"limit": 101}, "must be between 1 and 100"),
            ({"limit": "invalid"}, "must be a valid integer"),
            ({"created_after": "invalid-date"}, "Invalid date format"),
            ({"updated_before": "not-a-date"}, "Invalid date format"),
        ]

        for arguments, expected_error in test_cases:
            # Act
            result = await project_search_handlers.search_projects_handler(arguments)

            # Assert
            assert result.isError
            assert expected_error in result.content[0].text

    async def test_search_projects_advanced_handler_successful_search(
        self, mock_github_client, mock_search_manager, sample_search_result
    ):
        """Test advanced search handler with successful search."""
        # Arrange
        project_search_handlers.github_client = mock_github_client

        with patch(
            "github_project_manager_mcp.handlers.project_search_handlers.ProjectSearchManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_search_manager
            mock_search_manager.search_projects.return_value = sample_search_result

            arguments = {
                "search_config": {
                    "query": "test project",
                    "public": True,
                    "owner": "testuser",
                    "limit": 25,
                    "sort": {"by": "created", "ascending": False},
                }
            }

            # Act
            result = await project_search_handlers.search_projects_advanced_handler(
                arguments
            )

            # Assert
            assert not result.isError
            content_text = result.content[0].text
            assert "Found 2 project(s)" in content_text
            assert "Test Project 1" in content_text
            assert "Test Project 2" in content_text

    async def test_search_projects_advanced_handler_with_date_filters(
        self, mock_github_client, mock_search_manager, sample_search_result
    ):
        """Test advanced search handler with date filters."""
        # Arrange
        project_search_handlers.github_client = mock_github_client

        with patch(
            "github_project_manager_mcp.handlers.project_search_handlers.ProjectSearchManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_search_manager
            mock_search_manager.search_projects.return_value = sample_search_result

            arguments = {
                "search_config": {
                    "created_after": "2024-01-01T00:00:00Z",
                    "created_before": "2024-12-31T23:59:59Z",
                    "updated_after": "2024-01-01T00:00:00Z",
                    "updated_before": "2024-12-31T23:59:59Z",
                }
            }

            # Act
            result = await project_search_handlers.search_projects_advanced_handler(
                arguments
            )

            # Assert
            assert not result.isError
            mock_search_manager.search_projects.assert_called_once()

    async def test_search_manager_lazy_initialization(
        self, mock_github_client, mock_search_manager
    ):
        """Test that search manager is lazily initialized."""
        # Arrange
        project_search_handlers.github_client = mock_github_client

        with patch(
            "github_project_manager_mcp.handlers.project_search_handlers.ProjectSearchManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_search_manager
            mock_search_manager.search_projects.return_value = ProjectSearchResult(
                projects=[], total_count=0, search_time_ms=10.0, has_next_page=False
            )

            # Initially no search manager
            assert project_search_handlers.search_manager is None

            arguments = {"query": "test"}

            # Act
            await project_search_handlers.search_projects_handler(arguments)

            # Assert
            # Search manager should now be initialized
            assert project_search_handlers.search_manager is not None
            mock_manager_class.assert_called_once_with(mock_github_client)

    async def test_search_manager_reinitialization_on_client_change(
        self, mock_search_manager
    ):
        """Test that search manager is reinitialized when client changes."""
        # Arrange
        client1 = MagicMock()
        client1.token = "token1"
        client2 = MagicMock()
        client2.token = "token2"

        with patch(
            "github_project_manager_mcp.handlers.project_search_handlers.ProjectSearchManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_search_manager
            mock_search_manager.search_projects.return_value = ProjectSearchResult(
                projects=[], total_count=0, search_time_ms=10.0, has_next_page=False
            )

            # First client
            project_search_handlers.github_client = client1
            arguments = {"query": "test"}
            await project_search_handlers.search_projects_handler(arguments)

            first_manager_id = project_search_handlers._search_manager_client_id
            assert first_manager_id == id(client1)

            # Change client
            project_search_handlers.github_client = client2
            await project_search_handlers.search_projects_handler(arguments)

            # Assert
            # Should have been called twice (once for each client)
            assert mock_manager_class.call_count == 2
            # Client ID should have changed
            assert project_search_handlers._search_manager_client_id == id(client2)
            assert project_search_handlers._search_manager_client_id != first_manager_id

    async def test_search_functionality_preserves_project_data_fields(
        self, mock_github_client, mock_search_manager
    ):
        """Test that search functionality preserves all project data fields."""
        # Arrange
        project_search_handlers.github_client = mock_github_client

        complete_project_data = ProjectSearchResult(
            projects=[
                {
                    "id": "PVTI_789",
                    "title": "Complete Project",
                    "shortDescription": "Complete project with all fields",
                    "public": False,
                    "owner": "testowner",
                    "createdAt": "2024-03-15T10:30:00Z",
                    "updatedAt": "2024-03-20T14:45:00Z",
                }
            ],
            total_count=1,
            search_time_ms=75.2,
            has_next_page=False,
        )

        with patch(
            "github_project_manager_mcp.handlers.project_search_handlers.ProjectSearchManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_search_manager
            mock_search_manager.search_projects.return_value = complete_project_data

            arguments = {"query": "complete"}

            # Act
            result = await project_search_handlers.search_projects_handler(arguments)

            # Assert
            assert not result.isError
            content_text = result.content[0].text

            # Verify all fields are included
            assert "Complete Project" in content_text
            assert "ID: `PVTI_789`" in content_text
            assert "Description: Complete project with all fields" in content_text
            assert "Visibility: Private" in content_text
            assert "Owner: testowner" in content_text
            assert "Created: 2024-03-15" in content_text
            assert "Updated: 2024-03-20" in content_text

    async def test_search_functionality_handles_missing_optional_fields(
        self, mock_github_client, mock_search_manager
    ):
        """Test that search functionality handles projects with missing optional fields."""
        # Arrange
        project_search_handlers.github_client = mock_github_client

        minimal_project_data = ProjectSearchResult(
            projects=[
                {
                    "id": "PVTI_MIN",
                    "title": "Minimal Project",
                    # Missing: shortDescription, owner, createdAt, updatedAt
                    "public": True,
                }
            ],
            total_count=1,
            search_time_ms=30.1,
            has_next_page=False,
        )

        with patch(
            "github_project_manager_mcp.handlers.project_search_handlers.ProjectSearchManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_search_manager
            mock_search_manager.search_projects.return_value = minimal_project_data

            arguments = {"query": "minimal"}

            # Act
            result = await project_search_handlers.search_projects_handler(arguments)

            # Assert
            assert not result.isError
            content_text = result.content[0].text

            # Verify required fields are included
            assert "Minimal Project" in content_text
            assert "ID: `PVTI_MIN`" in content_text
            assert "Visibility: Public" in content_text

            # Verify optional fields are gracefully omitted
            assert "Description:" not in content_text
            assert "Owner:" not in content_text
            assert "Created:" not in content_text
            assert "Updated:" not in content_text

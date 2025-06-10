"""
Unit tests for project search and filtering functionality.

Tests comprehensive search capabilities including:
- Text-based search across project titles and descriptions
- Filtering by visibility (public/private)
- Filtering by creation/update date ranges
- Combined search criteria
- Pagination with search results
- Search result ranking and relevance
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.github_project_manager_mcp.utils.project_search import (
    ProjectSearchFilter,
    ProjectSearchManager,
    ProjectSearchResult,
)


class TestProjectSearchFilter:
    """Test project search filter functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.search_filter = ProjectSearchFilter()

    def test_project_search_filter_creation_default(self):
        """Test creating a project search filter with default values."""
        filter_obj = ProjectSearchFilter()

        assert filter_obj.query == ""
        assert filter_obj.visibility is None
        assert filter_obj.created_after is None
        assert filter_obj.created_before is None
        assert filter_obj.updated_after is None
        assert filter_obj.updated_before is None
        assert filter_obj.owner is None
        assert filter_obj.limit == 25
        assert filter_obj.sort_by == "updated"
        assert filter_obj.sort_order == "desc"

    def test_project_search_filter_creation_with_parameters(self):
        """Test creating a project search filter with specific parameters."""
        created_after = datetime(2024, 1, 1, tzinfo=timezone.utc)
        updated_before = datetime(2024, 12, 31, tzinfo=timezone.utc)

        filter_obj = ProjectSearchFilter(
            query="test project",
            visibility="public",
            created_after=created_after,
            updated_before=updated_before,
            owner="octocat",
            limit=50,
            sort_by="created",
            sort_order="asc",
        )

        assert filter_obj.query == "test project"
        assert filter_obj.visibility == "public"
        assert filter_obj.created_after == created_after
        assert filter_obj.updated_before == updated_before
        assert filter_obj.owner == "octocat"
        assert filter_obj.limit == 50
        assert filter_obj.sort_by == "created"
        assert filter_obj.sort_order == "asc"

    def test_project_search_filter_validation_invalid_visibility(self):
        """Test project search filter validation with invalid visibility."""
        with pytest.raises(
            ValueError, match="visibility must be 'public' or 'private'"
        ):
            ProjectSearchFilter(visibility="invalid")

    def test_project_search_filter_validation_invalid_limit(self):
        """Test project search filter validation with invalid limit."""
        with pytest.raises(ValueError, match="limit must be between 1 and 100"):
            ProjectSearchFilter(limit=0)

        with pytest.raises(ValueError, match="limit must be between 1 and 100"):
            ProjectSearchFilter(limit=101)

    def test_project_search_filter_validation_invalid_sort_by(self):
        """Test project search filter validation with invalid sort_by."""
        with pytest.raises(
            ValueError, match="sort_by must be 'created', 'updated', or 'name'"
        ):
            ProjectSearchFilter(sort_by="invalid")

    def test_project_search_filter_validation_invalid_sort_order(self):
        """Test project search filter validation with invalid sort_order."""
        with pytest.raises(ValueError, match="sort_order must be 'asc' or 'desc'"):
            ProjectSearchFilter(sort_order="invalid")

    def test_project_search_filter_to_dict(self):
        """Test converting project search filter to dictionary."""
        created_after = datetime(2024, 1, 1, tzinfo=timezone.utc)

        filter_obj = ProjectSearchFilter(
            query="test",
            visibility="public",
            created_after=created_after,
            owner="octocat",
        )

        result = filter_obj.to_dict()

        assert result["query"] == "test"
        assert result["visibility"] == "public"
        assert result["created_after"] == created_after.isoformat()
        assert result["owner"] == "octocat"
        assert "created_before" not in result  # None values excluded


class TestProjectSearchResult:
    """Test project search result functionality."""

    def test_project_search_result_creation(self):
        """Test creating a project search result."""
        projects = [
            {"id": "proj1", "title": "Project 1"},
            {"id": "proj2", "title": "Project 2"},
        ]

        result = ProjectSearchResult(
            projects=projects, total_count=2, has_next_page=False, search_time_ms=150.5
        )

        assert result.projects == projects
        assert result.total_count == 2
        assert result.has_next_page is False
        assert result.search_time_ms == 150.5

    def test_project_search_result_to_dict(self):
        """Test converting project search result to dictionary."""
        projects = [{"id": "proj1", "title": "Project 1"}]

        result = ProjectSearchResult(
            projects=projects, total_count=1, has_next_page=True, search_time_ms=75.25
        )

        result_dict = result.to_dict()

        assert result_dict["projects"] == projects
        assert result_dict["total_count"] == 1
        assert result_dict["has_next_page"] is True
        assert result_dict["search_time_ms"] == 75.25


class TestProjectSearchManager:
    """Test project search manager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_github_client = AsyncMock()
        self.search_manager = ProjectSearchManager(self.mock_github_client)

    @pytest.mark.asyncio
    async def test_search_projects_by_query_success(self):
        """Test successful project search by query."""
        # Mock response from GitHub API (already unwrapped by GitHub client)
        mock_response = {
            "viewer": {
                "projectsV2": {
                    "totalCount": 2,
                    "pageInfo": {"hasNextPage": False, "endCursor": "cursor123"},
                    "nodes": [
                        {
                            "id": "PVT_kwDOBQfyVc0Fo",
                            "title": "Test Project 1",
                            "shortDescription": "A test project for search",
                            "public": True,
                            "createdAt": "2024-01-15T10:00:00Z",
                            "updatedAt": "2024-01-20T15:30:00Z",
                            "owner": {"login": "octocat"},
                        },
                        {
                            "id": "PVT_kwDOBQfyVc0FoR",
                            "title": "Test Project 2",
                            "shortDescription": "Another test project",
                            "public": False,
                            "createdAt": "2024-01-10T08:00:00Z",
                            "updatedAt": "2024-01-18T12:00:00Z",
                            "owner": {"login": "octocat"},
                        },
                    ],
                }
            }
        }

        self.mock_github_client.query.return_value = mock_response

        search_filter = ProjectSearchFilter(query="test")
        result = await self.search_manager.search_projects(search_filter)

        assert isinstance(result, ProjectSearchResult)
        assert len(result.projects) == 2  # Both projects match "test"
        assert result.total_count == 2
        assert result.has_next_page is False
        assert result.projects[0]["title"] == "Test Project 1"
        assert result.projects[1]["title"] == "Test Project 2"

    @pytest.mark.asyncio
    async def test_search_projects_with_visibility_filter(self):
        """Test project search with visibility filter."""
        mock_response = {
            "viewer": {
                "projectsV2": {
                    "totalCount": 1,
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "id": "PVT_kwDOBQfyVc0FoQ",
                            "title": "Public Project",
                            "shortDescription": "A public project",
                            "public": True,
                            "createdAt": "2024-01-15T10:00:00Z",
                            "updatedAt": "2024-01-20T15:30:00Z",
                            "owner": {"login": "octocat"},
                        }
                    ],
                }
            }
        }

        self.mock_github_client.query.return_value = mock_response

        search_filter = ProjectSearchFilter(visibility="public")
        result = await self.search_manager.search_projects(search_filter)

        assert len(result.projects) == 1
        assert result.projects[0]["public"] is True

        # Verify the GraphQL query was called
        self.mock_github_client.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_projects_with_date_range_filter(self):
        """Test project search with date range filter."""
        mock_response = {
            "viewer": {
                "projectsV2": {
                    "totalCount": 1,
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "id": "PVT_kwDOBQfyVc0FoQ",
                            "title": "Recent Project",
                            "shortDescription": "A recently created project",
                            "public": True,
                            "createdAt": "2024-01-15T10:00:00Z",
                            "updatedAt": "2024-01-20T15:30:00Z",
                            "owner": {"login": "octocat"},
                        }
                    ],
                }
            }
        }

        self.mock_github_client.query.return_value = mock_response

        created_after = datetime(2024, 1, 1, tzinfo=timezone.utc)
        search_filter = ProjectSearchFilter(created_after=created_after)
        result = await self.search_manager.search_projects(search_filter)

        assert len(result.projects) == 1

        # Verify the GraphQL query was called
        self.mock_github_client.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_projects_with_owner_filter(self):
        """Test project search with owner filter."""
        mock_response = {
            "user": {
                "projectsV2": {
                    "totalCount": 1,
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "id": "PVT_kwDOBQfyVc0FoQ",
                            "title": "Owner Project",
                            "shortDescription": "A project by specific owner",
                            "public": True,
                            "createdAt": "2024-01-15T10:00:00Z",
                            "updatedAt": "2024-01-20T15:30:00Z",
                            "owner": {"login": "specific-user"},
                        }
                    ],
                }
            }
        }

        self.mock_github_client.query.return_value = mock_response

        search_filter = ProjectSearchFilter(owner="specific-user")
        result = await self.search_manager.search_projects(search_filter)

        assert len(result.projects) == 1
        assert result.projects[0]["owner"] == "specific-user"

        # Verify the GraphQL query was called
        self.mock_github_client.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_projects_with_combined_filters(self):
        """Test project search with multiple combined filters."""
        mock_response = {
            "user": {
                "projectsV2": {
                    "totalCount": 1,
                    "pageInfo": {"hasNextPage": True, "endCursor": "cursor123"},
                    "nodes": [
                        {
                            "id": "PVT_kwDOBQfyVc0FoQ",
                            "title": "Advanced Test Project",
                            "shortDescription": "A complex test case",
                            "public": False,
                            "createdAt": "2024-01-15T10:00:00Z",
                            "updatedAt": "2024-01-20T15:30:00Z",
                            "owner": {"login": "test-user"},
                        }
                    ],
                }
            }
        }

        self.mock_github_client.query.return_value = mock_response

        created_after = datetime(2024, 1, 1, tzinfo=timezone.utc)
        search_filter = ProjectSearchFilter(
            query="test",
            visibility="private",
            created_after=created_after,
            owner="test-user",
            limit=10,
            sort_by="created",
            sort_order="asc",
        )

        result = await self.search_manager.search_projects(search_filter)

        assert len(result.projects) == 1
        assert result.has_next_page is True

        # Verify the GraphQL query was called
        self.mock_github_client.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_projects_empty_results(self):
        """Test project search with no matching results."""
        mock_response = {
            "viewer": {
                "projectsV2": {
                    "totalCount": 0,
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [],
                }
            }
        }

        self.mock_github_client.query.return_value = mock_response

        search_filter = ProjectSearchFilter(query="nonexistent project")
        result = await self.search_manager.search_projects(search_filter)

        assert len(result.projects) == 0
        assert result.total_count == 0
        assert result.has_next_page is False

    @pytest.mark.asyncio
    async def test_search_projects_graphql_error(self):
        """Test project search with GraphQL errors."""
        mock_response = {
            "errors": [
                {"message": "Search rate limit exceeded"},
                {"message": "Invalid search syntax"},
            ]
        }

        self.mock_github_client.query.return_value = mock_response

        search_filter = ProjectSearchFilter(query="test")

        with pytest.raises(Exception, match="Search rate limit exceeded"):
            await self.search_manager.search_projects(search_filter)

    @pytest.mark.asyncio
    async def test_search_projects_api_exception(self):
        """Test project search with API exception."""
        self.mock_github_client.query.side_effect = Exception("API connection failed")

        search_filter = ProjectSearchFilter(query="test")

        with pytest.raises(Exception, match="API connection failed"):
            await self.search_manager.search_projects(search_filter)

    @pytest.mark.asyncio
    async def test_search_projects_no_github_client(self):
        """Test project search with no GitHub client."""
        search_manager = ProjectSearchManager(None)
        search_filter = ProjectSearchFilter(query="test")

        with pytest.raises(ValueError, match="GitHub client not initialized"):
            await search_manager.search_projects(search_filter)

    def test_build_search_query_basic(self):
        """Test building basic search query."""
        search_filter = ProjectSearchFilter(query="test project")
        query = self.search_manager._build_search_query(search_filter)

        assert "test project" in query
        assert "type:projectv2" in query

    def test_build_search_query_with_filters(self):
        """Test building search query with multiple filters."""
        created_after = datetime(2024, 1, 1, tzinfo=timezone.utc)
        search_filter = ProjectSearchFilter(
            query="test",
            visibility="public",
            created_after=created_after,
            owner="octocat",
        )

        query = self.search_manager._build_search_query(search_filter)

        assert "test" in query
        assert "is:public" in query
        assert "created:>2024-01-01" in query
        assert "user:octocat" in query
        assert "type:projectv2" in query

    def test_format_project_from_search_result(self):
        """Test formatting project from search result."""
        search_node = {
            "id": "PVT_kwDOBQfyVc0FoQ",
            "title": "Test Project",
            "shortDescription": "A test project",
            "public": True,
            "createdAt": "2024-01-15T10:00:00Z",
            "updatedAt": "2024-01-20T15:30:00Z",
            "owner": {"login": "octocat"},
        }

        formatted = self.search_manager._format_project_from_search_result(search_node)

        assert formatted["id"] == "PVT_kwDOBQfyVc0FoQ"
        assert formatted["title"] == "Test Project"
        assert formatted["shortDescription"] == "A test project"
        assert formatted["public"] is True
        assert formatted["createdAt"] == "2024-01-15T10:00:00Z"
        assert formatted["updatedAt"] == "2024-01-20T15:30:00Z"
        assert formatted["owner"] == "octocat"

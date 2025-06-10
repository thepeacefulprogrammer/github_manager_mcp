"""
Integration tests for search functionality with real GitHub API calls.

These tests verify that the search functionality works correctly with the actual GitHub API,
ensuring proper project discovery, filtering, and data retrieval.
"""

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from github_project_manager_mcp.github_client import GitHubClient
from github_project_manager_mcp.handlers import project_search_handlers


class TestSearchFunctionalityRealAPI:
    """Integration tests for search functionality with real GitHub API."""

    @pytest.fixture(scope="class")
    def github_token(self):
        """Get GitHub token from environment."""
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            pytest.skip("GITHUB_TOKEN environment variable not set")
        return token

    @pytest.fixture(scope="class")
    def initialized_client(self, github_token):
        """Initialize the GitHub client for testing."""
        project_search_handlers.initialize_github_client(github_token)
        return project_search_handlers.github_client

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """Reset global state before each test."""
        project_search_handlers.search_manager = None
        project_search_handlers._search_manager_client_id = None

    @pytest.mark.integration
    async def test_search_projects_basic_functionality_real_api(
        self, initialized_client
    ):
        """Test basic search functionality with real GitHub API."""
        # Arrange
        arguments = {
            "query": "test",
            "limit": 5,
            "sort_by": "updated",
            "sort_order": "desc",
        }

        # Act
        result = await project_search_handlers.search_projects_handler(arguments)

        # Assert
        assert not result.isError, f"Search failed: {result.content[0].text}"
        content_text = result.content[0].text

        # Should either find projects or indicate no results
        assert (
            "Found" in content_text and "project(s)" in content_text
        ) or "No projects found" in content_text

        # Should include search timing
        assert "searched in" in content_text and (
            "ms" in content_text or "s" in content_text
        )

    @pytest.mark.integration
    async def test_search_projects_with_visibility_filter_real_api(
        self, initialized_client
    ):
        """Test search with visibility filter using real GitHub API."""
        # Arrange - search for public projects which are more likely to exist
        arguments = {
            "query": "github",
            "visibility": "public",
            "limit": 3,
        }

        # Act
        result = await project_search_handlers.search_projects_handler(arguments)

        # Assert
        assert not result.isError, f"Search failed: {result.content[0].text}"
        content_text = result.content[0].text

        # If projects are found, verify visibility is indicated
        if "Found" in content_text:
            # Should show visibility information for found projects
            assert "Visibility:" in content_text

    @pytest.mark.integration
    async def test_search_projects_with_date_filters_real_api(self, initialized_client):
        """Test search with date filters using real GitHub API."""
        # Arrange - search for projects created in the last year
        one_year_ago = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()

        arguments = {
            "query": "project",
            "created_after": one_year_ago,
            "limit": 3,
        }

        # Act
        result = await project_search_handlers.search_projects_handler(arguments)

        # Assert
        assert not result.isError, f"Search failed: {result.content[0].text}"
        content_text = result.content[0].text

        # Should complete successfully (may or may not find results)
        assert ("Found" in content_text) or ("No projects found" in content_text)

    @pytest.mark.integration
    async def test_search_projects_advanced_handler_real_api(self, initialized_client):
        """Test advanced search handler with real GitHub API."""
        # Arrange
        arguments = {
            "search_config": {
                "query": "demo",
                "public": True,
                "limit": 3,
                "sort": {"by": "updated", "ascending": False},
            }
        }

        # Act
        result = await project_search_handlers.search_projects_advanced_handler(
            arguments
        )

        # Assert
        assert not result.isError, f"Advanced search failed: {result.content[0].text}"
        content_text = result.content[0].text

        # Should complete successfully
        assert ("Found" in content_text) or ("No projects found" in content_text)
        assert "searched in" in content_text

    @pytest.mark.integration
    async def test_search_projects_parameter_validation_real_api(
        self, initialized_client
    ):
        """Test parameter validation with real GitHub API."""
        # Arrange - invalid limit
        arguments = {
            "query": "test",
            "limit": 150,  # Over the limit
        }

        # Act
        result = await project_search_handlers.search_projects_handler(arguments)

        # Assert
        assert result.isError
        assert "must be between 1 and 100" in result.content[0].text

    @pytest.mark.integration
    async def test_search_projects_empty_query_real_api(self, initialized_client):
        """Test search with empty query using real GitHub API."""
        # Arrange
        arguments = {
            "limit": 2,
        }

        # Act
        result = await project_search_handlers.search_projects_handler(arguments)

        # Assert
        assert not result.isError, f"Search failed: {result.content[0].text}"
        # Should handle empty query gracefully

    @pytest.mark.integration
    async def test_search_projects_nonexistent_query_real_api(self, initialized_client):
        """Test search with query that should return no results."""
        # Arrange - use a very specific query unlikely to match
        arguments = {
            "query": "veryunlikelyprojectname12345abcdef",
            "limit": 5,
        }

        # Act
        result = await project_search_handlers.search_projects_handler(arguments)

        # Assert
        assert not result.isError, f"Search failed: {result.content[0].text}"
        content_text = result.content[0].text

        # Should indicate no results found
        assert "No projects found" in content_text
        assert "searched in" in content_text

    @pytest.mark.integration
    async def test_search_manager_initialization_real_api(self, initialized_client):
        """Test that search manager is properly initialized with real API."""
        # Arrange
        assert project_search_handlers.search_manager is None

        arguments = {"query": "test", "limit": 1}

        # Act
        result = await project_search_handlers.search_projects_handler(arguments)

        # Assert
        assert not result.isError, f"Search failed: {result.content[0].text}"
        # Search manager should now be initialized
        assert project_search_handlers.search_manager is not None
        assert project_search_handlers._search_manager_client_id is not None

    @pytest.mark.integration
    async def test_search_projects_response_format_real_api(self, initialized_client):
        """Test that search response format is correct with real API."""
        # Arrange
        arguments = {
            "query": "github",
            "limit": 2,
        }

        # Act
        result = await project_search_handlers.search_projects_handler(arguments)

        # Assert
        assert not result.isError, f"Search failed: {result.content[0].text}"
        content_text = result.content[0].text

        # Check response format
        if "Found" in content_text:
            # Should have project information format
            assert "•" in content_text  # Bullet points for project details
            assert "ID:" in content_text  # Project ID
            assert "Visibility:" in content_text  # Visibility info

    @pytest.mark.integration
    async def test_search_projects_pagination_real_api(self, initialized_client):
        """Test pagination behavior with real API."""
        # Arrange - use a common query likely to have many results
        arguments = {
            "query": "project",
            "limit": 1,  # Small limit to test pagination
        }

        # Act
        result = await project_search_handlers.search_projects_handler(arguments)

        # Assert
        assert not result.isError, f"Search failed: {result.content[0].text}"
        content_text = result.content[0].text

        # If results are found and there are more pages, should show pagination info
        if "Found" in content_text and "Showing first" in content_text:
            assert "results" in content_text
            assert "Use pagination parameters" in content_text

    @pytest.mark.integration
    async def test_search_projects_error_recovery_real_api(self, initialized_client):
        """Test error recovery with invalid date format but valid API."""
        # Arrange - invalid date format
        arguments = {
            "query": "test",
            "created_after": "invalid-date-format",
        }

        # Act
        result = await project_search_handlers.search_projects_handler(arguments)

        # Assert
        assert result.isError
        assert "Invalid date format" in result.content[0].text

    @pytest.mark.integration
    async def test_search_projects_rate_limit_awareness_real_api(
        self, initialized_client
    ):
        """Test that search functionality is aware of rate limits."""
        # Arrange - multiple searches to test rate limit handling
        arguments = {"query": "test", "limit": 1}

        # Act - perform multiple searches
        results = []
        for i in range(3):
            result = await project_search_handlers.search_projects_handler(arguments)
            results.append(result)

        # Assert - all should succeed or handle rate limits gracefully
        for i, result in enumerate(results):
            if result.isError:
                # If there's an error, it should be a meaningful one
                error_text = result.content[0].text.lower()
                # Should not be a generic error
                assert any(
                    keyword in error_text
                    for keyword in ["rate limit", "authentication", "network", "token"]
                ), f"Unexpected error in search {i}: {result.content[0].text}"
            else:
                # If successful, should have proper format
                assert ("Found" in result.content[0].text) or (
                    "No projects found" in result.content[0].text
                )

    @pytest.mark.integration
    async def test_search_projects_real_api_data_consistency(self, initialized_client):
        """Test that search returns consistent data format with real API."""
        # Arrange
        arguments = {
            "query": "test",
            "limit": 1,
        }

        # Act
        result = await project_search_handlers.search_projects_handler(arguments)

        # Assert
        assert not result.isError, f"Search failed: {result.content[0].text}"
        content_text = result.content[0].text

        # Check for consistent data format
        if "Found" in content_text and "project(s)" in content_text:
            # Should have timing information
            assert "searched in" in content_text
            # Should have project details format
            assert "ID:" in content_text or "No projects found" in content_text

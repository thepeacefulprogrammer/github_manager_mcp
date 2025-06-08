"""
Unit tests for GitHub GraphQL query builder utilities.
"""

import pytest


class TestProjectQueryBuilder:
    """Test suite for GitHub Projects v2 GraphQL query builder."""

    def test_build_list_projects_query_basic(self):
        """Test building basic list projects query."""
        from src.github_project_manager_mcp.utils.query_builder import (
            ProjectQueryBuilder,
        )

        builder = ProjectQueryBuilder()
        query = builder.list_projects("testuser")

        assert "query" in query
        assert "testuser" in query
        assert "projectsV2" in query
        assert "nodes" in query

    def test_build_list_projects_query_with_pagination(self):
        """Test building list projects query with pagination."""
        from src.github_project_manager_mcp.utils.query_builder import (
            ProjectQueryBuilder,
        )

        builder = ProjectQueryBuilder()
        query = builder.list_projects("testuser", first=10, after="cursor123")

        assert "first: 10" in query
        assert 'after: "cursor123"' in query
        assert "pageInfo" in query
        assert "hasNextPage" in query
        assert "endCursor" in query

    def test_build_list_projects_query_with_custom_fields(self):
        """Test building list projects query with custom field selection."""
        from src.github_project_manager_mcp.utils.query_builder import (
            ProjectQueryBuilder,
        )

        builder = ProjectQueryBuilder()
        fields = ["id", "title", "description", "createdAt"]
        query = builder.list_projects("testuser", fields=fields)

        for field in fields:
            assert field in query
        assert "updatedAt" not in query  # Should not include fields not requested

    def test_build_get_project_query(self):
        """Test building get single project query."""
        from src.github_project_manager_mcp.utils.query_builder import (
            ProjectQueryBuilder,
        )

        builder = ProjectQueryBuilder()
        query = builder.get_project("project123")

        assert "query" in query
        assert "node" in query
        assert 'id: "project123"' in query
        assert "... on ProjectV2" in query

    def test_build_get_project_query_with_custom_fields(self):
        """Test building get project query with custom fields."""
        from src.github_project_manager_mcp.utils.query_builder import (
            ProjectQueryBuilder,
        )

        builder = ProjectQueryBuilder()
        fields = ["id", "title", "url", "viewerCanUpdate"]
        query = builder.get_project("project123", fields=fields)

        for field in fields:
            assert field in query

    def test_build_project_items_query(self):
        """Test building query for project items."""
        from src.github_project_manager_mcp.utils.query_builder import (
            ProjectQueryBuilder,
        )

        builder = ProjectQueryBuilder()
        query = builder.get_project_items("project123")

        assert "query" in query
        assert 'id: "project123"' in query
        assert "items" in query
        assert "content" in query

    def test_build_project_items_query_with_pagination(self):
        """Test building project items query with pagination."""
        from src.github_project_manager_mcp.utils.query_builder import (
            ProjectQueryBuilder,
        )

        builder = ProjectQueryBuilder()
        query = builder.get_project_items("project123", first=20, after="item_cursor")

        assert "first: 20" in query
        assert 'after: "item_cursor"' in query

    def test_build_search_projects_query(self):
        """Test building search projects query."""
        from src.github_project_manager_mcp.utils.query_builder import (
            ProjectQueryBuilder,
        )

        builder = ProjectQueryBuilder()
        query = builder.search_projects("testuser", search_term="web app")

        assert "projectsV2" in query
        assert "testuser" in query
        # Note: GitHub's Projects v2 API doesn't have direct search,
        # so this would be client-side filtering

    def test_build_create_project_mutation(self):
        """Test building create project mutation."""
        from src.github_project_manager_mcp.utils.query_builder import (
            ProjectQueryBuilder,
        )

        builder = ProjectQueryBuilder()
        mutation = builder.create_project(
            "owner123", "My New Project", "Project description"
        )

        assert "mutation" in mutation
        assert "createProjectV2" in mutation
        assert "ownerId" in mutation
        assert "title" in mutation
        assert "My New Project" in mutation
        assert "Project description" in mutation

    def test_build_update_project_mutation(self):
        """Test building update project mutation."""
        from src.github_project_manager_mcp.utils.query_builder import (
            ProjectQueryBuilder,
        )

        builder = ProjectQueryBuilder()
        mutation = builder.update_project(
            "project123", title="Updated Title", description="New description"
        )

        assert "mutation" in mutation
        assert "updateProjectV2" in mutation
        assert "projectId" in mutation
        assert "Updated Title" in mutation
        assert "New description" in mutation

    def test_build_delete_project_mutation(self):
        """Test building delete project mutation."""
        from src.github_project_manager_mcp.utils.query_builder import (
            ProjectQueryBuilder,
        )

        builder = ProjectQueryBuilder()
        mutation = builder.delete_project("project123")

        assert "mutation" in mutation
        assert "deleteProjectV2" in mutation
        assert 'projectId: "project123"' in mutation

    def test_build_add_item_to_project_mutation(self):
        """Test building add item to project mutation."""
        from src.github_project_manager_mcp.utils.query_builder import (
            ProjectQueryBuilder,
        )

        builder = ProjectQueryBuilder()
        mutation = builder.add_item_to_project("project123", "content123")

        assert "mutation" in mutation
        assert "addProjectV2ItemById" in mutation
        assert "projectId" in mutation
        assert "contentId" in mutation

    def test_query_builder_validates_parameters(self):
        """Test that query builder validates required parameters."""
        from src.github_project_manager_mcp.utils.query_builder import (
            ProjectQueryBuilder,
        )

        builder = ProjectQueryBuilder()

        with pytest.raises(ValueError, match="Owner is required"):
            builder.list_projects("")

        with pytest.raises(ValueError, match="Project ID is required"):
            builder.get_project("")

    def test_query_builder_handles_pagination_parameters(self):
        """Test that query builder handles pagination parameters correctly."""
        from src.github_project_manager_mcp.utils.query_builder import (
            ProjectQueryBuilder,
        )

        builder = ProjectQueryBuilder()

        # Test with only 'first' parameter
        query1 = builder.list_projects("testuser", first=5)
        assert "first: 5" in query1
        assert "after:" not in query1

        # Test with both 'first' and 'after' parameters
        query2 = builder.list_projects("testuser", first=5, after="cursor")
        assert "first: 5" in query2
        assert 'after: "cursor"' in query2

    def test_query_builder_escapes_strings_properly(self):
        """Test that query builder properly escapes strings in queries."""
        from src.github_project_manager_mcp.utils.query_builder import (
            ProjectQueryBuilder,
        )

        builder = ProjectQueryBuilder()

        # Test with special characters that need escaping
        title_with_quotes = 'Project "with quotes"'
        mutation = builder.create_project("owner123", title_with_quotes)

        # Should properly escape quotes
        assert '\\"' in mutation or "'" in mutation  # Either escaped or single quotes

    def test_query_builder_default_fields(self):
        """Test that query builder includes sensible default fields."""
        from src.github_project_manager_mcp.utils.query_builder import (
            ProjectQueryBuilder,
        )

        builder = ProjectQueryBuilder()
        query = builder.list_projects("testuser")

        # Should include essential fields by default
        essential_fields = ["id", "title", "description", "url", "createdAt"]
        for field in essential_fields:
            assert field in query

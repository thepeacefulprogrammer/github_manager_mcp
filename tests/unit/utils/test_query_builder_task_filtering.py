"""
Unit tests for GraphQL query builder task filtering functionality.

This test file focuses on testing the GraphQL query structure for task filtering
and ensuring efficient querying when filtering by parent PRD.
"""

import pytest
from github_project_manager_mcp.utils.query_builder import ProjectQueryBuilder


class TestQueryBuilderTaskFiltering:
    """Test GraphQL query building for task filtering scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.query_builder = ProjectQueryBuilder()

    def test_list_tasks_query_structure_without_filtering(self):
        """Test that list_tasks query has proper structure without PRD filtering."""
        query = self.query_builder.list_tasks_in_project(
            project_id="PVT_test123", first=25
        )

        # Verify query contains expected GraphQL structure
        assert 'node(id: "PVT_test123")' in query
        assert "ProjectV2" in query
        assert "items(first: 25)" in query
        assert "fieldValues(first: 10)" in query
        assert "DraftIssue" in query
        assert "Issue" in query

        # Verify pagination info is included
        assert "pageInfo" in query
        assert "hasNextPage" in query
        assert "totalCount" in query

    def test_list_tasks_query_structure_with_prd_filtering(self):
        """Test that list_tasks query structure is same regardless of PRD filter parameter."""
        query_without_filter = self.query_builder.list_tasks_in_project(
            project_id="PVT_test123", first=25
        )

        query_with_filter = self.query_builder.list_tasks_in_project(
            project_id="PVT_test123", parent_prd_id="PVTI_prd123", first=25
        )

        # Currently, both queries should be identical since filtering happens in Python
        assert query_without_filter == query_with_filter

        # This demonstrates the current limitation - GraphQL query doesn't change
        # based on parent_prd_id parameter

    def test_list_tasks_query_includes_necessary_fields_for_filtering(self):
        """Test that the query includes all fields necessary for PRD filtering."""
        query = self.query_builder.list_tasks_in_project(
            project_id="PVT_test123", parent_prd_id="PVTI_prd123"
        )

        # Verify the query includes content body for description parsing
        assert "body" in query

        # Verify the query includes field values for field-based filtering
        assert "fieldValues" in query
        assert "ProjectV2ItemFieldTextValue" in query
        assert "ProjectV2ItemFieldSingleSelectValue" in query

        # Verify field structure for accessing field names
        assert "field {" in query
        assert "name" in query

    def test_list_tasks_query_pagination_args(self):
        """Test that pagination arguments are properly handled."""
        query_with_pagination = self.query_builder.list_tasks_in_project(
            project_id="PVT_test123", first=50, after="cursor123"
        )

        assert 'items(first: 50, after: "cursor123")' in query_with_pagination

        query_minimal = self.query_builder.list_tasks_in_project(
            project_id="PVT_test123"
        )

        # Default case should not include pagination args
        assert "items {" in query_minimal or "items(" not in query_minimal

    def test_list_tasks_query_escapes_project_id(self):
        """Test that project IDs are properly escaped in GraphQL."""
        query = self.query_builder.list_tasks_in_project(
            project_id='PVT_test"123'  # ID with quote to test escaping
        )

        # Should properly escape the quote
        assert '"PVT_test\\"123"' in query or 'PVT_test\\"123' in query

    def test_list_tasks_query_parameter_validation(self):
        """Test that query builder validates required parameters."""
        with pytest.raises(ValueError, match="Project ID is required"):
            self.query_builder.list_tasks_in_project(project_id="")

        with pytest.raises(ValueError, match="Project ID is required"):
            self.query_builder.list_tasks_in_project(project_id=None)

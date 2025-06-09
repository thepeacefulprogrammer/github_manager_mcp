"""
Unit tests for Project data model.

This module tests the Project data model which represents a GitHub Projects v2 project.
Following TDD principles - these tests define the expected behavior before implementation.
"""

from datetime import datetime

import pytest

from github_project_manager_mcp.models.project import (
    Project,
    ProjectField,
    ProjectFieldConfiguration,
    ProjectFieldIteration,
    ProjectFieldOption,
    ProjectVisibility,
)


class TestProjectModel:
    """Test cases for Project data model."""

    def test_project_creation_with_required_fields(self):
        """Test creating a Project with only required fields."""
        project_data = {
            "id": "PVT_kwDOBQfyVc0FoQ",
            "number": 1,
            "title": "My Test Project",
            "url": "https://github.com/orgs/test-org/projects/1",
            "owner_login": "test-org",
        }

        project = Project(**project_data)

        assert project.id == "PVT_kwDOBQfyVc0FoQ"
        assert project.number == 1
        assert project.title == "My Test Project"
        assert project.url == "https://github.com/orgs/test-org/projects/1"
        assert project.owner_login == "test-org"

        # Optional fields should be None
        assert project.description is None
        assert project.visibility is None
        assert project.public is None

    def test_project_creation_with_all_fields(self):
        """Test creating a Project with all available fields."""
        project_data = {
            "id": "PVT_kwDOBQfyVc0FoQ",
            "number": 1,
            "title": "My Test Project",
            "url": "https://github.com/orgs/test-org/projects/1",
            "owner_login": "test-org",
            "description": "A comprehensive test project",
            "visibility": "PRIVATE",
            "public": False,
            "closed": False,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
            "creator_login": "test-user",
            "short_description": "Test project",
            "readme": "## Project README\nThis is a test project.",
        }

        project = Project(**project_data)

        assert project.id == "PVT_kwDOBQfyVc0FoQ"
        assert project.description == "A comprehensive test project"
        assert project.visibility == "PRIVATE"
        assert project.public is False
        assert project.closed is False
        assert project.creator_login == "test-user"
        assert project.readme == "## Project README\nThis is a test project."

    def test_project_validation_missing_required_fields(self):
        """Test that Project creation fails with missing required fields."""
        incomplete_data = {
            "title": "My Test Project",
            # Missing id, number, url, owner_login
        }

        with pytest.raises(TypeError):
            Project(**incomplete_data)

    def test_project_validation_invalid_visibility(self):
        """Test that Project creation fails with invalid visibility value."""
        project_data = {
            "id": "PVT_kwDOBQfyVc0FoQ",
            "number": 1,
            "title": "My Test Project",
            "url": "https://github.com/orgs/test-org/projects/1",
            "owner_login": "test-org",
            "visibility": "INVALID_VISIBILITY",  # Invalid value
        }

        with pytest.raises(ValueError, match="Invalid visibility"):
            Project(**project_data)

    def test_project_to_dict(self):
        """Test converting Project to dictionary."""
        project_data = {
            "id": "PVT_kwDOBQfyVc0FoQ",
            "number": 1,
            "title": "My Test Project",
            "url": "https://github.com/orgs/test-org/projects/1",
            "owner_login": "test-org",
        }

        project = Project(**project_data)
        result_dict = project.to_dict()

        # Should contain all the original data
        for key, value in project_data.items():
            assert result_dict[key] == value

    def test_project_from_graphql_response(self):
        """Test creating Project from GitHub GraphQL API response."""
        graphql_response = {
            "id": "PVT_kwDOBQfyVc0FoQ",
            "number": 1,
            "title": "My Test Project",
            "url": "https://github.com/orgs/test-org/projects/1",
            "owner": {"login": "test-org"},
            "description": "A test project",
            "visibility": "PRIVATE",
            "public": False,
            "closed": False,
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-02T00:00:00Z",
            "creator": {"login": "test-user"},
            "shortDescription": "Test project",
            "readme": "## Project README",
        }

        project = Project.from_graphql(graphql_response)

        assert project.id == "PVT_kwDOBQfyVc0FoQ"
        assert project.owner_login == "test-org"  # Extracted from nested owner.login
        assert (
            project.creator_login == "test-user"
        )  # Extracted from nested creator.login
        assert project.created_at == "2024-01-01T00:00:00Z"  # Converted from createdAt
        assert project.updated_at == "2024-01-02T00:00:00Z"  # Converted from updatedAt
        assert (
            project.short_description == "Test project"
        )  # Converted from shortDescription

    def test_project_equality(self):
        """Test Project equality comparison."""
        project_data = {
            "id": "PVT_kwDOBQfyVc0FoQ",
            "number": 1,
            "title": "My Test Project",
            "url": "https://github.com/orgs/test-org/projects/1",
            "owner_login": "test-org",
        }

        project1 = Project(**project_data)
        project2 = Project(**project_data)
        project3 = Project(**{**project_data, "id": "different_id"})

        assert project1 == project2
        assert project1 != project3

    def test_project_str_representation(self):
        """Test Project string representation."""
        project_data = {
            "id": "PVT_kwDOBQfyVc0FoQ",
            "number": 1,
            "title": "My Test Project",
            "url": "https://github.com/orgs/test-org/projects/1",
            "owner_login": "test-org",
        }

        project = Project(**project_data)
        str_repr = str(project)

        assert "My Test Project" in str_repr
        assert "test-org" in str_repr
        assert "#1" in str_repr  # Project number


class TestProjectField:
    """Test cases for ProjectField data model."""

    def test_project_field_creation(self):
        """Test creating a ProjectField."""
        field_data = {
            "id": "PVTF_lQDOBQfyVc0FoQ",
            "name": "Status",
            "data_type": "SINGLE_SELECT",
            "options": [
                ProjectFieldOption(id="PVTSO_lQDOBQfyVc0FoQ1", name="Todo"),
                ProjectFieldOption(id="PVTSO_lQDOBQfyVc0FoQ2", name="In Progress"),
                ProjectFieldOption(id="PVTSO_lQDOBQfyVc0FoQ3", name="Done"),
            ],
        }

        field = ProjectField(**field_data)

        assert field.id == "PVTF_lQDOBQfyVc0FoQ"
        assert field.name == "Status"
        assert field.data_type == "SINGLE_SELECT"
        assert len(field.options) == 3

    def test_project_field_text_type(self):
        """Test creating a text type ProjectField."""
        field_data = {
            "id": "PVTF_lQDOBQfyVc0FoQ",
            "name": "Description",
            "data_type": "TEXT",
        }

        field = ProjectField(**field_data)

        assert field.id == "PVTF_lQDOBQfyVc0FoQ"
        assert field.name == "Description"
        assert field.data_type == "TEXT"
        assert field.options is None  # No options for text fields

    def test_project_field_number_type(self):
        """Test creating a number type ProjectField."""
        field_data = {
            "id": "PVTF_lQDOBQfyVc0FoQ",
            "name": "Estimate",
            "data_type": "NUMBER",
        }

        field = ProjectField(**field_data)

        assert field.data_type == "NUMBER"

    def test_project_field_iteration_type(self):
        """Test creating an iteration type ProjectField."""
        field_data = {
            "id": "PVTF_lQDOBQfyVc0FoQ",
            "name": "Sprint",
            "data_type": "ITERATION",
            "configuration": ProjectFieldConfiguration(
                iterations=[
                    ProjectFieldIteration(
                        id="PVTI_lQDOBQfyVc0FoQ1",
                        title="Sprint 1",
                        start_date="2024-01-01",
                        duration=14,
                    ),
                    ProjectFieldIteration(
                        id="PVTI_lQDOBQfyVc0FoQ2",
                        title="Sprint 2",
                        start_date="2024-01-15",
                        duration=14,
                    ),
                ]
            ),
        }

        field = ProjectField(**field_data)

        assert field.data_type == "ITERATION"
        assert field.configuration is not None
        assert len(field.configuration.iterations) == 2

    def test_project_field_invalid_data_type(self):
        """Test that ProjectField creation fails with invalid data type."""
        field_data = {
            "id": "PVTF_lQDOBQfyVc0FoQ",
            "name": "Invalid Field",
            "data_type": "INVALID_TYPE",
        }

        with pytest.raises(ValueError, match="Invalid data_type"):
            ProjectField(**field_data)

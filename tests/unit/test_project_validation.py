"""
Unit tests for project validation logic.

Tests comprehensive validation for project operations including:
- Parameter validation for required fields and constraints
- Business rule validation
- Repository format validation
- Project metadata validation
"""

from unittest.mock import AsyncMock, Mock

import pytest

from src.github_project_manager_mcp.utils.validation import (
    ProjectValidator,
    ValidationError,
    ValidationResult,
)


class TestProjectValidator:
    """Test project validation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ProjectValidator()

    def test_validate_project_creation_success_all_fields(self):
        """Test successful project creation validation with all fields."""
        project_data = {
            "name": "GitHub Manager MCP",
            "description": "A comprehensive project management solution for GitHub Projects v2 integration",
            "repository": "octocat/Hello-World",
            "visibility": "PRIVATE",
        }

        result = self.validator.validate_project_creation(project_data)

        assert result.is_valid
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_validate_project_creation_success_minimal_fields(self):
        """Test successful project creation validation with minimal required fields."""
        project_data = {"name": "Test Project", "repository": "octocat/Hello-World"}

        result = self.validator.validate_project_creation(project_data)

        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_project_creation_missing_name(self):
        """Test project creation validation failure with missing name."""
        project_data = {"repository": "octocat/Hello-World"}

        result = self.validator.validate_project_creation(project_data)

        assert not result.is_valid
        assert "name is required" in result.errors

    def test_validate_project_creation_empty_name(self):
        """Test project creation validation failure with empty name."""
        project_data = {"name": "", "repository": "octocat/Hello-World"}

        result = self.validator.validate_project_creation(project_data)

        assert not result.is_valid
        assert "name cannot be empty" in result.errors

    def test_validate_project_creation_name_too_short(self):
        """Test project creation validation with name too short (warning)."""
        project_data = {"name": "Hi", "repository": "octocat/Hello-World"}

        result = self.validator.validate_project_creation(project_data)

        assert result.is_valid
        assert len(result.warnings) > 0
        assert any("at least 3 characters" in warning for warning in result.warnings)

    def test_validate_project_creation_name_too_long(self):
        """Test project creation validation failure with name too long."""
        project_data = {
            "name": "A" * 101,  # 101 characters
            "repository": "octocat/Hello-World",
        }

        result = self.validator.validate_project_creation(project_data)

        assert not result.is_valid
        assert "cannot exceed 100 characters" in str(result.errors)

    def test_validate_project_creation_missing_repository(self):
        """Test project creation validation failure with missing repository."""
        project_data = {"name": "Test Project"}

        result = self.validator.validate_project_creation(project_data)

        assert not result.is_valid
        assert "repository is required" in result.errors

    def test_validate_project_creation_invalid_repository_format(self):
        """Test project creation validation failure with invalid repository format."""
        project_data = {"name": "Test Project", "repository": "invalid-repo-format"}

        result = self.validator.validate_project_creation(project_data)

        assert not result.is_valid
        assert "Invalid repository format" in str(result.errors)

    def test_validate_project_creation_invalid_visibility(self):
        """Test project creation validation failure with invalid visibility."""
        project_data = {
            "name": "Test Project",
            "repository": "octocat/Hello-World",
            "visibility": "INVALID",
        }

        result = self.validator.validate_project_creation(project_data)

        assert not result.is_valid
        assert "visibility must be one of: PUBLIC, PRIVATE" in str(result.errors)

    def test_validate_project_creation_description_too_long(self):
        """Test project creation validation failure with description too long."""
        project_data = {
            "name": "Test Project",
            "repository": "octocat/Hello-World",
            "description": "A" * 501,  # 501 characters
        }

        result = self.validator.validate_project_creation(project_data)

        assert not result.is_valid
        assert "cannot exceed 500 characters" in str(result.errors)

    def test_validate_project_update_success_all_fields(self):
        """Test successful project update validation with all fields."""
        update_data = {
            "title": "Updated Project Name",
            "short_description": "Updated description",
            "readme": "# Updated README\n\nThis is the updated project documentation.",
            "public": True,
        }

        result = self.validator.validate_project_update(update_data)

        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_project_update_success_single_field(self):
        """Test successful project update validation with single field."""
        update_data = {"title": "Updated Project Name"}

        result = self.validator.validate_project_update(update_data)

        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_project_update_no_fields(self):
        """Test project update validation failure with no fields to update."""
        update_data = {}

        result = self.validator.validate_project_update(update_data)

        assert not result.is_valid
        assert "At least one field must be updated" in result.errors

    def test_validate_project_update_invalid_title(self):
        """Test project update validation failure with invalid title."""
        update_data = {"title": ""}  # Empty title

        result = self.validator.validate_project_update(update_data)

        assert not result.is_valid
        # Empty string is filtered out, so this becomes "no updates provided"
        assert "At least one field must be updated" in result.errors

    def test_validate_project_update_title_too_long(self):
        """Test project update validation failure with title too long."""
        update_data = {"title": "A" * 101}  # 101 characters

        result = self.validator.validate_project_update(update_data)

        assert not result.is_valid
        assert "cannot exceed 100 characters" in str(result.errors)

    def test_validate_project_update_description_too_long(self):
        """Test project update validation failure with description too long."""
        update_data = {"short_description": "A" * 501}  # 501 characters

        result = self.validator.validate_project_update(update_data)

        assert not result.is_valid
        assert "cannot exceed 500 characters" in str(result.errors)

    def test_validate_project_update_readme_too_long(self):
        """Test project update validation failure with README too long."""
        update_data = {"readme": "A" * 32769}  # 32769 characters (max is 32768)

        result = self.validator.validate_project_update(update_data)

        assert not result.is_valid
        assert "cannot exceed 32768 characters" in str(result.errors)

    def test_validate_repository_format_valid_formats(self):
        """Test repository format validation with valid formats."""
        valid_repos = [
            "octocat/Hello-World",
            "microsoft/TypeScript",
            "facebook/react",
            "user123/my-awesome-project",
            "org_name/project_name",
        ]

        for repo in valid_repos:
            result = self.validator.validate_repository_format(repo)
            assert result.is_valid, f"Repository {repo} should be valid"

    def test_validate_repository_format_invalid_formats(self):
        """Test repository format validation with invalid formats."""
        invalid_repos = [
            "just-a-name",
            "owner/",
            "/repo",
            "owner/repo/extra",
            "",
            None,
            "owner repo",
            "owner//repo",
        ]

        for repo in invalid_repos:
            result = self.validator.validate_repository_format(repo)
            assert not result.is_valid, f"Repository {repo} should be invalid"

    def test_validate_project_constraints_business_rules(self):
        """Test project validation business rules and constraints."""
        # Test: Name and description similarity warning
        project_data = {
            "name": "Test Project",
            "description": "Test Project description",
            "repository": "octocat/Hello-World",
        }

        result = self.validator.validate_project_creation(project_data)

        assert result.is_valid
        assert len(result.warnings) > 0
        assert any("similar to" in warning for warning in result.warnings)

    def test_validate_multiple_errors(self):
        """Test validation with multiple errors."""
        project_data = {
            "name": "",  # Empty name
            "repository": "invalid-format",  # Invalid repository
            "visibility": "INVALID",  # Invalid visibility
            "description": "A" * 501,  # Too long description
        }

        result = self.validator.validate_project_creation(project_data)

        assert not result.is_valid
        assert len(result.errors) >= 3  # Should have multiple errors

"""
Unit tests for validation utilities.

Tests comprehensive validation logic for PRD, task, and subtask operations
including parameter validation, field constraints, business rules, and
data integrity checks.
"""

import pytest


class TestValidationResult:
    """Test ValidationResult class."""

    def test_validation_result_success(self):
        """Test creating a successful validation result."""
        from src.github_project_manager_mcp.utils.validation import ValidationResult

        result = ValidationResult(is_valid=True)

        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_validation_result_with_errors(self):
        """Test creating a validation result with errors."""
        from src.github_project_manager_mcp.utils.validation import ValidationResult

        errors = ["Field 'title' is required", "Invalid status value"]
        result = ValidationResult(is_valid=False, errors=errors)

        assert result.is_valid is False
        assert result.errors == errors
        assert result.warnings == []


class TestParameterValidator:
    """Test ParameterValidator class."""

    def test_validate_required_string_success(self):
        """Test validating required string parameter successfully."""
        from src.github_project_manager_mcp.utils.validation import ParameterValidator

        validator = ParameterValidator()
        result = validator.validate_required_string("project_id", "PVT_test123")

        assert result.is_valid is True
        assert result.errors == []

    def test_validate_required_string_missing(self):
        """Test validating required string parameter when missing."""
        from src.github_project_manager_mcp.utils.validation import ParameterValidator

        validator = ParameterValidator()
        result = validator.validate_required_string("project_id", None)

        assert result.is_valid is False
        assert "project_id is required" in result.errors[0]

    def test_validate_enum_value_success(self):
        """Test validating enum value successfully."""
        from src.github_project_manager_mcp.utils.validation import ParameterValidator

        validator = ParameterValidator()
        valid_values = ["Backlog", "In Progress", "Done"]
        result = validator.validate_enum_value("status", "In Progress", valid_values)

        assert result.is_valid is True
        assert result.errors == []

    def test_validate_enum_value_invalid(self):
        """Test validating enum value with invalid option."""
        from src.github_project_manager_mcp.utils.validation import ParameterValidator

        validator = ParameterValidator()
        valid_values = ["Backlog", "In Progress", "Done"]
        result = validator.validate_enum_value("status", "Invalid", valid_values)

        assert result.is_valid is False
        assert "status must be one of" in result.errors[0]


class TestPRDValidator:
    """Test PRDValidator class."""

    def test_validate_prd_creation_success(self):
        """Test validating PRD creation successfully."""
        from src.github_project_manager_mcp.utils.validation import PRDValidator

        validator = PRDValidator()
        prd_data = {
            "title": "User Authentication System",
            "description": "Implement secure user authentication",
            "priority": "High",
            "status": "Backlog",
        }

        result = validator.validate_prd_creation(prd_data)

        assert result.is_valid is True
        assert result.errors == []

    def test_validate_prd_creation_missing_title(self):
        """Test validating PRD creation with missing title."""
        from src.github_project_manager_mcp.utils.validation import PRDValidator

        validator = PRDValidator()
        prd_data = {
            "description": "Implement secure user authentication",
            "priority": "High",
        }

        result = validator.validate_prd_creation(prd_data)

        assert result.is_valid is False
        assert any("title is required" in error for error in result.errors)


class TestTaskValidator:
    """Test TaskValidator class."""

    def test_validate_task_creation_success(self):
        """Test validating task creation successfully."""
        from src.github_project_manager_mcp.utils.validation import TaskValidator

        validator = TaskValidator()
        task_data = {
            "title": "Implement OAuth provider",
            "parent_prd_id": "PVTI_test123",
            "priority": "Medium",
        }

        result = validator.validate_task_creation(task_data)

        assert result.is_valid is True
        assert result.errors == []

    def test_validate_task_creation_missing_parent_prd(self):
        """Test validating task creation with missing parent PRD."""
        from src.github_project_manager_mcp.utils.validation import TaskValidator

        validator = TaskValidator()
        task_data = {"title": "Implement OAuth provider", "priority": "Medium"}

        result = validator.validate_task_creation(task_data)

        assert result.is_valid is False
        assert any("parent_prd_id is required" in error for error in result.errors)


class TestSubtaskValidator:
    """Test SubtaskValidator class."""

    def test_validate_subtask_creation_success(self):
        """Test validating subtask creation successfully."""
        from src.github_project_manager_mcp.utils.validation import SubtaskValidator

        validator = SubtaskValidator()
        subtask_data = {
            "title": "Write OAuth unit tests",
            "parent_task_id": "PVTI_test123",
            "order": 1,
        }

        result = validator.validate_subtask_creation(subtask_data)

        assert result.is_valid is True
        assert result.errors == []

    def test_validate_subtask_creation_missing_parent_task(self):
        """Test validating subtask creation with missing parent task."""
        from src.github_project_manager_mcp.utils.validation import SubtaskValidator

        validator = SubtaskValidator()
        subtask_data = {"title": "Write OAuth unit tests", "order": 1}

        result = validator.validate_subtask_creation(subtask_data)

        assert result.is_valid is False
        assert any("parent_task_id is required" in error for error in result.errors)

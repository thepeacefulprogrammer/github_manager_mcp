"""
Validation utilities for GitHub Project Manager MCP.

Provides comprehensive validation logic for PRD, task, and subtask operations
including parameter validation, field constraints, business rules, and
data integrity checks.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""

    def __init__(
        self, message: str, validation_result: Optional["ValidationResult"] = None
    ):
        self.message = message
        self.validation_result = validation_result
        super().__init__(message)


class ValidationResult:
    """Result of a validation operation."""

    def __init__(
        self,
        is_valid: bool,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

    def __str__(self) -> str:
        if self.is_valid:
            return "Validation passed"
        return f"Validation failed: {', '.join(self.errors)}"

    def add_error(self, error: str):
        """Add an error to the validation result."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str):
        """Add a warning to the validation result."""
        self.warnings.append(warning)

    def merge(self, other: "ValidationResult"):
        """Merge another validation result into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        if not other.is_valid:
            self.is_valid = False


class ParameterValidator:
    """Base parameter validation utilities."""

    def validate_required_string(self, field_name: str, value: Any) -> ValidationResult:
        """Validate that a required string parameter is provided and not empty."""
        if value is None:
            return ValidationResult(False, [f"{field_name} is required"])

        if not isinstance(value, str):
            return ValidationResult(False, [f"{field_name} must be a string"])

        if not value.strip():
            return ValidationResult(False, [f"{field_name} cannot be empty"])

        return ValidationResult(True)

    def validate_optional_string(self, field_name: str, value: Any) -> ValidationResult:
        """Validate an optional string parameter."""
        if value is None:
            return ValidationResult(True)

        if not isinstance(value, str):
            return ValidationResult(False, [f"{field_name} must be a string"])

        return ValidationResult(True)

    def validate_optional_integer(
        self, field_name: str, value: Any
    ) -> ValidationResult:
        """Validate an optional integer parameter."""
        if value is None:
            return ValidationResult(True)

        if not isinstance(value, int):
            return ValidationResult(False, [f"{field_name} must be an integer"])

        return ValidationResult(True)

    def validate_positive_integer(
        self, field_name: str, value: Any
    ) -> ValidationResult:
        """Validate that an integer parameter is positive."""
        result = self.validate_optional_integer(field_name, value)
        if not result.is_valid or value is None:
            return result

        if value <= 0:
            return ValidationResult(False, [f"{field_name} must be positive"])

        return ValidationResult(True)

    def validate_enum_value(
        self, field_name: str, value: Any, valid_values: List[str]
    ) -> ValidationResult:
        """Validate that a value is one of the allowed enum values."""
        if value is None:
            return ValidationResult(True)

        if not isinstance(value, str):
            return ValidationResult(False, [f"{field_name} must be a string"])

        if value not in valid_values:
            return ValidationResult(
                False, [f"{field_name} must be one of: {', '.join(valid_values)}"]
            )

        return ValidationResult(True)


class ProjectValidator(ParameterValidator):
    """Validation utilities for Project operations."""

    VALID_VISIBILITIES = ["PUBLIC", "PRIVATE"]

    # GitHub limits
    MAX_NAME_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 500
    MAX_README_LENGTH = 32768  # 32KB
    MIN_NAME_LENGTH = 3

    def validate_repository_format(self, repository: Any) -> ValidationResult:
        """Validate repository format as 'owner/repo'."""
        if repository is None:
            return ValidationResult(False, ["repository is required"])

        if not isinstance(repository, str):
            return ValidationResult(False, ["repository must be a string"])

        if not repository.strip():
            return ValidationResult(False, ["repository cannot be empty"])

        # Check for basic format: owner/repo
        if "/" not in repository:
            return ValidationResult(
                False, ["Invalid repository format. Expected 'owner/repo'"]
            )

        parts = repository.split("/")
        if len(parts) != 2:
            return ValidationResult(
                False, ["Invalid repository format. Expected 'owner/repo'"]
            )

        owner, repo = parts
        if not owner or not owner.strip():
            return ValidationResult(
                False, ["Invalid repository format. Owner cannot be empty"]
            )

        if not repo or not repo.strip():
            return ValidationResult(
                False, ["Invalid repository format. Repository name cannot be empty"]
            )

        # Check for valid characters (GitHub allows alphanumeric, hyphens, dots, underscores)
        valid_pattern = re.compile(r"^[a-zA-Z0-9._-]+$")
        if not valid_pattern.match(owner) or not valid_pattern.match(repo):
            return ValidationResult(
                False,
                [
                    "Invalid repository format. Only alphanumeric characters, dots, hyphens, and underscores allowed"
                ],
            )

        return ValidationResult(True)

    def validate_project_creation(
        self, project_data: Dict[str, Any]
    ) -> ValidationResult:
        """Validate project creation parameters."""
        result = ValidationResult(True)

        # Validate required fields
        name_result = self.validate_required_string("name", project_data.get("name"))
        result.merge(name_result)

        repository_result = self.validate_repository_format(
            project_data.get("repository")
        )
        result.merge(repository_result)

        # Validate optional fields
        description = project_data.get("description")
        if description is not None:
            description_result = self.validate_optional_string(
                "description", description
            )
            result.merge(description_result)

            if (
                isinstance(description, str)
                and len(description) > self.MAX_DESCRIPTION_LENGTH
            ):
                result.add_error(
                    f"description cannot exceed {self.MAX_DESCRIPTION_LENGTH} characters"
                )

        visibility = project_data.get("visibility")
        if visibility is not None:
            visibility_result = self.validate_enum_value(
                "visibility", visibility, self.VALID_VISIBILITIES
            )
            result.merge(visibility_result)

        # Validate name constraints
        name = project_data.get("name")
        if isinstance(name, str) and name.strip():
            if len(name) > self.MAX_NAME_LENGTH:
                result.add_error(
                    f"name cannot exceed {self.MAX_NAME_LENGTH} characters"
                )
            elif len(name) < self.MIN_NAME_LENGTH:
                result.add_warning(
                    f"Project name is recommended to be at least {self.MIN_NAME_LENGTH} characters"
                )

        # Business rule validations
        if isinstance(name, str) and isinstance(description, str):
            # Check if name and description are too similar
            if name.lower().strip() in description.lower().strip():
                result.add_warning(
                    "Project description appears to be very similar to the project name. Consider making the description more detailed."
                )

        return result

    def validate_project_update(self, update_data: Dict[str, Any]) -> ValidationResult:
        """Validate project update parameters."""
        result = ValidationResult(True)

        # Filter out None values and empty strings to check for actual updates
        # Special handling for boolean fields like 'public'
        actual_updates = {}
        for field, value in update_data.items():
            if field == "public":
                # Boolean field: include if it's not None
                if value is not None:
                    actual_updates[field] = value
            else:
                # String fields: include if not None and not empty
                if value is not None and value != "":
                    actual_updates[field] = value

        # At least one field must be provided for update
        updatable_fields = ["title", "short_description", "readme", "public"]

        has_updates = any(field in actual_updates for field in updatable_fields)
        if not has_updates:
            result.add_error("At least one field must be updated")
            return result

        # Validate each provided field (only non-None, non-empty values)
        if "title" in actual_updates:
            title_result = self.validate_required_string(
                "title", actual_updates["title"]
            )
            result.merge(title_result)

            title = actual_updates["title"]
            if isinstance(title, str) and len(title) > self.MAX_NAME_LENGTH:
                result.add_error(
                    f"title cannot exceed {self.MAX_NAME_LENGTH} characters"
                )

        if "short_description" in actual_updates:
            description_result = self.validate_optional_string(
                "short_description", actual_updates["short_description"]
            )
            result.merge(description_result)

            description = actual_updates["short_description"]
            if (
                isinstance(description, str)
                and len(description) > self.MAX_DESCRIPTION_LENGTH
            ):
                result.add_error(
                    f"short_description cannot exceed {self.MAX_DESCRIPTION_LENGTH} characters"
                )

        if "readme" in actual_updates:
            readme_result = self.validate_optional_string(
                "readme", actual_updates["readme"]
            )
            result.merge(readme_result)

            readme = actual_updates["readme"]
            if isinstance(readme, str) and len(readme) > self.MAX_README_LENGTH:
                result.add_error(
                    f"readme cannot exceed {self.MAX_README_LENGTH} characters"
                )

        # public field validation is handled by GitHub API (boolean type enforcement)

        return result


class PRDValidator(ParameterValidator):
    """Validation utilities for PRD operations."""

    VALID_STATUSES = [
        "Backlog",
        "This Sprint",
        "Up Next",
        "In Progress",
        "Done",
        "Cancelled",
    ]
    VALID_PRIORITIES = ["Low", "Medium", "High", "Critical"]

    def validate_prd_creation(self, prd_data: Dict[str, Any]) -> ValidationResult:
        """Validate PRD creation parameters."""
        result = ValidationResult(True)

        # Required fields
        title_result = self.validate_required_string("title", prd_data.get("title"))
        result.merge(title_result)

        # Optional fields with validation
        description_result = self.validate_optional_string(
            "description", prd_data.get("description")
        )
        result.merge(description_result)

        acceptance_criteria_result = self.validate_optional_string(
            "acceptance_criteria", prd_data.get("acceptance_criteria")
        )
        result.merge(acceptance_criteria_result)

        business_value_result = self.validate_optional_string(
            "business_value", prd_data.get("business_value")
        )
        result.merge(business_value_result)

        technical_requirements_result = self.validate_optional_string(
            "technical_requirements", prd_data.get("technical_requirements")
        )
        result.merge(technical_requirements_result)

        # Enum validations
        priority_result = self.validate_enum_value(
            "priority", prd_data.get("priority"), self.VALID_PRIORITIES
        )
        result.merge(priority_result)

        status_result = self.validate_enum_value(
            "status", prd_data.get("status"), self.VALID_STATUSES
        )
        result.merge(status_result)

        # Business rules
        if prd_data.get("description") and len(prd_data["description"]) < 10:
            result.add_warning(
                "PRD description is recommended to be at least 10 characters"
            )

        return result

    def validate_prd_update(self, update_data: Dict[str, Any]) -> ValidationResult:
        """Validate PRD update parameters."""
        result = ValidationResult(True)

        # At least one field must be provided for update
        updatable_fields = [
            "title",
            "description",
            "acceptance_criteria",
            "business_value",
            "technical_requirements",
            "priority",
            "status",
            "assignee_ids",
        ]

        has_updates = any(field in update_data for field in updatable_fields)
        if not has_updates:
            result.add_error("At least one field must be updated")
            return result

        # Validate each provided field
        if "title" in update_data:
            title_result = self.validate_required_string("title", update_data["title"])
            result.merge(title_result)

        if "description" in update_data:
            description_result = self.validate_optional_string(
                "description", update_data["description"]
            )
            result.merge(description_result)

        if "priority" in update_data:
            priority_result = self.validate_enum_value(
                "priority", update_data["priority"], self.VALID_PRIORITIES
            )
            result.merge(priority_result)

        if "status" in update_data:
            status_result = self.validate_enum_value(
                "status", update_data["status"], self.VALID_STATUSES
            )
            result.merge(status_result)

        return result


class TaskValidator(ParameterValidator):
    """Validation utilities for Task operations."""

    VALID_STATUSES = [
        "Backlog",
        "This Sprint",
        "Up Next",
        "In Progress",
        "Done",
        "Cancelled",
    ]
    VALID_PRIORITIES = ["Low", "Medium", "High", "Critical"]

    def validate_task_creation(self, task_data: Dict[str, Any]) -> ValidationResult:
        """Validate task creation parameters."""
        result = ValidationResult(True)

        # Required fields
        title_result = self.validate_required_string("title", task_data.get("title"))
        result.merge(title_result)

        parent_prd_result = self.validate_required_string(
            "parent_prd_id", task_data.get("parent_prd_id")
        )
        result.merge(parent_prd_result)

        # Optional fields with validation
        description_result = self.validate_optional_string(
            "description", task_data.get("description")
        )
        result.merge(description_result)

        # Enum validations
        priority_result = self.validate_enum_value(
            "priority", task_data.get("priority"), self.VALID_PRIORITIES
        )
        result.merge(priority_result)

        status_result = self.validate_enum_value(
            "status", task_data.get("status"), self.VALID_STATUSES
        )
        result.merge(status_result)

        # Integer validations
        estimated_hours_result = self.validate_positive_integer(
            "estimated_hours", task_data.get("estimated_hours")
        )
        result.merge(estimated_hours_result)

        actual_hours_result = self.validate_positive_integer(
            "actual_hours", task_data.get("actual_hours")
        )
        result.merge(actual_hours_result)

        return result

    def validate_task_update(self, update_data: Dict[str, Any]) -> ValidationResult:
        """Validate task update parameters."""
        result = ValidationResult(True)

        # At least one field must be provided for update
        updatable_fields = [
            "title",
            "description",
            "priority",
            "status",
            "estimated_hours",
            "actual_hours",
        ]

        has_updates = any(field in update_data for field in updatable_fields)
        if not has_updates:
            result.add_error("At least one field must be updated")
            return result

        # Validate each provided field
        if "title" in update_data:
            title_result = self.validate_required_string("title", update_data["title"])
            result.merge(title_result)

        if "description" in update_data:
            description_result = self.validate_optional_string(
                "description", update_data["description"]
            )
            result.merge(description_result)

        if "priority" in update_data:
            priority_result = self.validate_enum_value(
                "priority", update_data["priority"], self.VALID_PRIORITIES
            )
            result.merge(priority_result)

        if "status" in update_data:
            status_result = self.validate_enum_value(
                "status", update_data["status"], self.VALID_STATUSES
            )
            result.merge(status_result)

        if "estimated_hours" in update_data:
            estimated_hours_result = self.validate_positive_integer(
                "estimated_hours", update_data["estimated_hours"]
            )
            result.merge(estimated_hours_result)

        if "actual_hours" in update_data:
            actual_hours_result = self.validate_positive_integer(
                "actual_hours", update_data["actual_hours"]
            )
            result.merge(actual_hours_result)

        # Business rule: Check for significant variance between estimated and actual hours
        estimated = update_data.get("estimated_hours")
        actual = update_data.get("actual_hours")
        if estimated and actual and actual > estimated * 2:
            result.add_warning(
                f"Actual hours ({actual}) significantly exceed estimated hours ({estimated})"
            )

        return result


class SubtaskValidator(ParameterValidator):
    """Validation utilities for Subtask operations."""

    VALID_STATUSES = ["Incomplete", "Complete"]

    def validate_subtask_creation(
        self, subtask_data: Dict[str, Any]
    ) -> ValidationResult:
        """Validate subtask creation parameters."""
        result = ValidationResult(True)

        # Required fields
        title_result = self.validate_required_string("title", subtask_data.get("title"))
        result.merge(title_result)

        parent_task_result = self.validate_required_string(
            "parent_task_id", subtask_data.get("parent_task_id")
        )
        result.merge(parent_task_result)

        # Optional fields with validation
        description_result = self.validate_optional_string(
            "description", subtask_data.get("description")
        )
        result.merge(description_result)

        # Order validation
        order_result = self.validate_positive_integer(
            "order", subtask_data.get("order")
        )
        result.merge(order_result)

        # Status validation
        status_result = self.validate_enum_value(
            "status", subtask_data.get("status"), self.VALID_STATUSES
        )
        result.merge(status_result)

        return result

    def validate_subtask_update(self, update_data: Dict[str, Any]) -> ValidationResult:
        """Validate subtask update parameters."""
        result = ValidationResult(True)

        # At least one field must be provided for update
        updatable_fields = ["title", "description", "status", "order"]

        has_updates = any(field in update_data for field in updatable_fields)
        if not has_updates:
            result.add_error("At least one field must be updated")
            return result

        # Validate each provided field
        if "title" in update_data:
            title_result = self.validate_required_string("title", update_data["title"])
            result.merge(title_result)

        if "description" in update_data:
            description_result = self.validate_optional_string(
                "description", update_data["description"]
            )
            result.merge(description_result)

        if "status" in update_data:
            status_result = self.validate_enum_value(
                "status", update_data["status"], self.VALID_STATUSES
            )
            result.merge(status_result)

        if "order" in update_data:
            order_result = self.validate_positive_integer("order", update_data["order"])
            result.merge(order_result)

        return result


# Convenience functions for common validation patterns
def validate_project_id(project_id: str) -> ValidationResult:
    """Validate a GitHub project ID format."""
    validator = ParameterValidator()
    result = validator.validate_required_string("project_id", project_id)

    if result.is_valid and not project_id.startswith("PVT_"):
        result.add_error("project_id must start with 'PVT_'")

    return result


def validate_item_id(item_id: str, item_type: str = "item") -> ValidationResult:
    """Validate a GitHub project item ID format."""
    validator = ParameterValidator()
    result = validator.validate_required_string(f"{item_type}_id", item_id)

    if result.is_valid and not item_id.startswith("PVTI_"):
        result.add_error(f"{item_type}_id must start with 'PVTI_'")

    return result


def validate_pagination_params(
    first: Optional[int] = None, after: Optional[str] = None
) -> ValidationResult:
    """Validate pagination parameters."""
    validator = ParameterValidator()
    result = ValidationResult(True)

    if first is not None:
        if not isinstance(first, int) or first <= 0 or first > 100:
            result.add_error("'first' parameter must be an integer between 1 and 100")

    if after is not None:
        after_result = validator.validate_optional_string("after", after)
        result.merge(after_result)

    return result

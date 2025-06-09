"""
Status Column Data Models

This module contains data models for GitHub Projects v2 status columns,
which are implemented as single select fields with predefined options.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


@dataclass
class StatusColumnOption:
    """
    Represents an option within a status column (single select field).

    This model maps to GitHub GraphQL API ProjectV2SingleSelectFieldOption objects.
    """

    # Required fields
    id: str  # GitHub's global node ID for the option
    name: str  # Display name of the option

    def __post_init__(self):
        """Validate status column option data after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("Status column option name cannot be empty")

    @classmethod
    def from_github_option(cls, option_data: Dict[str, Any]) -> "StatusColumnOption":
        """
        Create a StatusColumnOption instance from GitHub GraphQL API response.

        Args:
            option_data: Raw GraphQL response data for a ProjectV2SingleSelectFieldOption

        Returns:
            StatusColumnOption instance
        """
        return cls(
            id=option_data["id"],
            name=option_data["name"],
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the status column option to a dictionary representation.

        Returns:
            Dictionary representation of the status column option
        """
        return {
            "id": self.id,
            "name": self.name,
        }


@dataclass
class StatusColumn:
    """
    Represents a status column in a GitHub Projects v2 project.

    Status columns are implemented as single select fields with predefined options
    that represent different states an item can be in (e.g., Todo, In Progress, Done).

    This model maps to GitHub GraphQL API ProjectV2SingleSelectField objects.
    """

    # Required fields
    id: str  # GitHub's global node ID for the field
    name: str  # Display name of the status column
    data_type: str  # Field data type (should always be "SINGLE_SELECT")

    # Options
    options: List[StatusColumnOption] = field(default_factory=list)

    # Metadata
    created_at: Optional[str] = None  # ISO 8601 datetime string
    updated_at: Optional[str] = None  # ISO 8601 datetime string

    def __post_init__(self):
        """Validate status column data after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("Status column name cannot be empty")

        if self.data_type != "SINGLE_SELECT":
            raise ValueError(
                f"Invalid data type for status column: {self.data_type}. Must be SINGLE_SELECT"
            )

        if len(self.options) == 0:
            raise ValueError("Status column must have at least one option")

        if len(self.options) > 50:
            raise ValueError("Status column cannot have more than 50 options")

    @classmethod
    def from_github_field(cls, field_data: Dict[str, Any]) -> "StatusColumn":
        """
        Create a StatusColumn instance from GitHub GraphQL API response.

        Args:
            field_data: Raw GraphQL response data for a ProjectV2SingleSelectField

        Returns:
            StatusColumn instance
        """
        # Validate that this is a single select field
        if field_data.get("__typename") != "ProjectV2SingleSelectField":
            raise ValueError("Field data is not for a single select field")

        # Parse options
        options = []
        for option_data in field_data.get("options", []):
            options.append(StatusColumnOption.from_github_option(option_data))

        return cls(
            id=field_data["id"],
            name=field_data["name"],
            data_type=field_data.get("dataType", "SINGLE_SELECT"),
            options=options,
            created_at=field_data.get("createdAt"),
            updated_at=field_data.get("updatedAt"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the status column to a dictionary representation.

        Returns:
            Dictionary representation of the status column
        """
        return {
            "id": self.id,
            "name": self.name,
            "data_type": self.data_type,
            "options": [option.to_dict() for option in self.options],
            "option_count": len(self.options),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def get_option_by_name(self, name: str) -> Optional[StatusColumnOption]:
        """
        Get an option by its name.

        Args:
            name: Name of the option to find

        Returns:
            StatusColumnOption if found, None otherwise
        """
        for option in self.options:
            if option.name == name:
                return option
        return None

    def get_option_by_id(self, option_id: str) -> Optional[StatusColumnOption]:
        """
        Get an option by its ID.

        Args:
            option_id: ID of the option to find

        Returns:
            StatusColumnOption if found, None otherwise
        """
        for option in self.options:
            if option.id == option_id:
                return option
        return None

    def has_option(self, name: str) -> bool:
        """
        Check if the status column has an option with the given name.

        Args:
            name: Name of the option to check for

        Returns:
            True if option exists, False otherwise
        """
        return self.get_option_by_name(name) is not None

    def get_option_names(self) -> List[str]:
        """
        Get a list of all option names in this status column.

        Returns:
            List of option names
        """
        return [option.name for option in self.options]


class DefaultStatusColumns(Enum):
    """Common default status column configurations."""

    BASIC = ["Todo", "In Progress", "Done"]
    KANBAN = ["Backlog", "This Sprint", "Up Next", "In Progress", "Done"]
    EXTENDED = ["Backlog", "This Sprint", "Up Next", "In Progress", "Done", "Cancelled"]
    PRIORITY = ["High", "Medium", "Low"]
    DEVELOPMENT = ["Planned", "In Development", "In Review", "Testing", "Ready", "Done"]

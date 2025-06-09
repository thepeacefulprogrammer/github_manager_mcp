"""
Project Data Model

This module contains data models for GitHub Projects v2 entities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class ProjectVisibility(Enum):
    """Valid visibility values for GitHub Projects v2."""

    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


@dataclass
class ProjectFieldOption:
    """Represents an option in a single-select or multi-select project field."""

    id: str
    name: str
    description: Optional[str] = None


@dataclass
class ProjectFieldIteration:
    """Represents an iteration in an iteration project field."""

    id: str
    title: str
    start_date: str
    duration: int  # Duration in days


@dataclass
class ProjectFieldConfiguration:
    """Configuration for project fields that require additional setup."""

    iterations: Optional[List[ProjectFieldIteration]] = None


@dataclass
class ProjectField:
    """Represents a custom field in a GitHub Project v2."""

    id: str
    name: str
    data_type: str  # TEXT, NUMBER, DATE, SINGLE_SELECT, ITERATION, etc.
    options: Optional[List[ProjectFieldOption]] = None
    configuration: Optional[ProjectFieldConfiguration] = None

    def __post_init__(self):
        """Validate field configuration based on data type."""
        valid_types = [
            "TEXT",
            "NUMBER",
            "DATE",
            "SINGLE_SELECT",
            "ITERATION",
            "MILESTONE",
            "REPOSITORY",
            "ASSIGNEES",
            "LABELS",
        ]
        if self.data_type not in valid_types:
            raise ValueError(
                f"Invalid data_type: {self.data_type}. Must be one of {valid_types}"
            )


@dataclass
class Project:
    """
    Represents a GitHub Projects v2 project.

    This model maps to the GitHub GraphQL API ProjectV2 object structure.
    """

    # Required fields
    id: str  # GitHub's global node ID (e.g., "PVT_kwDOBQfyVc0FoQ")
    number: int  # Project number within the organization/user
    title: str  # Project title
    url: str  # GitHub URL to the project
    owner_login: str  # Username or organization name that owns the project

    # Optional fields
    description: Optional[str] = None
    visibility: Optional[str] = None
    public: Optional[bool] = None
    closed: Optional[bool] = None
    created_at: Optional[str] = None  # ISO 8601 datetime string
    updated_at: Optional[str] = None  # ISO 8601 datetime string
    creator_login: Optional[str] = None
    short_description: Optional[str] = None
    readme: Optional[str] = None

    # Additional fields
    fields: Optional[List[ProjectField]] = field(default_factory=list)

    def __post_init__(self):
        """Validate project data after initialization."""
        if self.visibility and self.visibility not in [
            v.value for v in ProjectVisibility
        ]:
            raise ValueError(
                f"Invalid visibility: {self.visibility}. Must be PUBLIC or PRIVATE"
            )

    @classmethod
    def from_graphql(cls, data: Dict[str, Any]) -> "Project":
        """
        Create a Project instance from a GitHub GraphQL API response.

        Args:
            data: Raw GraphQL response data for a ProjectV2 object

        Returns:
            Project instance
        """
        # Extract nested fields with safe navigation
        owner_login = data.get("owner", {}).get("login", "")
        creator_login = (
            data.get("creator", {}).get("login") if data.get("creator") else None
        )

        # Convert GraphQL field names to our model field names
        project_data = {
            "id": data["id"],
            "number": data["number"],
            "title": data["title"],
            "url": data["url"],
            "owner_login": owner_login,
            "description": data.get("description"),
            "visibility": data.get("visibility"),
            "public": data.get("public"),
            "closed": data.get("closed"),
            "created_at": data.get("createdAt"),
            "updated_at": data.get("updatedAt"),
            "creator_login": creator_login,
            "short_description": data.get("shortDescription"),
            "readme": data.get("readme"),
        }

        # Process custom fields if present
        fields = []
        if "fields" in data and data["fields"]:
            field_nodes = data["fields"].get("nodes", [])
            for field_data in field_nodes:
                try:
                    project_field = ProjectField(
                        id=field_data["id"],
                        name=field_data["name"],
                        data_type=field_data.get("__typename", "TEXT")
                        .replace("ProjectV2", "")
                        .replace("Field", ""),
                    )

                    # Handle single select fields with options
                    if hasattr(field_data, "options") and field_data.get("options"):
                        project_field.options = [
                            ProjectFieldOption(
                                id=opt["id"],
                                name=opt["name"],
                                description=opt.get("description"),
                            )
                            for opt in field_data["options"]
                        ]

                    # Handle iteration fields with configuration
                    if hasattr(field_data, "configuration") and field_data.get(
                        "configuration"
                    ):
                        config = field_data["configuration"]
                        if "iterations" in config:
                            iterations = [
                                ProjectFieldIteration(
                                    id=iter_data["id"],
                                    title=iter_data["title"],
                                    start_date=iter_data["startDate"],
                                    duration=iter_data["duration"],
                                )
                                for iter_data in config["iterations"]
                            ]
                            project_field.configuration = ProjectFieldConfiguration(
                                iterations=iterations
                            )

                    fields.append(project_field)
                except (KeyError, TypeError) as e:
                    # Skip malformed field data
                    continue

        project_data["fields"] = fields

        return cls(**project_data)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Project instance to a dictionary.

        Returns:
            Dictionary representation of the project
        """
        result = {
            "id": self.id,
            "number": self.number,
            "title": self.title,
            "url": self.url,
            "owner_login": self.owner_login,
        }

        # Add optional fields if they have values
        optional_fields = [
            "description",
            "visibility",
            "public",
            "closed",
            "created_at",
            "updated_at",
            "creator_login",
            "short_description",
            "readme",
        ]

        for field_name in optional_fields:
            value = getattr(self, field_name)
            if value is not None:
                result[field_name] = value

        # Add fields if present
        if self.fields:
            result["fields"] = [
                {
                    "id": f.id,
                    "name": f.name,
                    "data_type": f.data_type,
                    "options": (
                        [{"id": opt.id, "name": opt.name} for opt in f.options]
                        if f.options
                        else None
                    ),
                    "configuration": f.configuration,
                }
                for f in self.fields
            ]

        return result

    def __str__(self) -> str:
        """String representation of the project."""
        return f"{self.title} (#{self.number}) - {self.owner_login}"

    def __eq__(self, other) -> bool:
        """Equality comparison based on project ID."""
        if not isinstance(other, Project):
            return False
        return self.id == other.id

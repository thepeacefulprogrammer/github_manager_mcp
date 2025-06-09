"""
PRD (Product Requirements Document) data models for GitHub Projects v2.

This module provides data models for managing Product Requirements Documents
as items within GitHub Projects v2, including status tracking, priority management,
and comprehensive metadata handling.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class PRDStatus(Enum):
    """Valid status values for PRDs in GitHub Projects v2."""

    BACKLOG = "Backlog"
    THIS_SPRINT = "This Sprint"
    UP_NEXT = "Up Next"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
    CANCELLED = "Cancelled"


class PRDPriority(Enum):
    """Priority levels for PRDs."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


@dataclass
class PRD:
    """
    Represents a Product Requirements Document as a GitHub Projects v2 item.

    This model maps to GitHub GraphQL API ProjectV2Item objects that represent
    PRDs with custom fields for status, priority, and metadata tracking.
    """

    # Required fields
    id: str  # GitHub's global node ID for the project item
    project_id: str  # ID of the containing project
    title: str  # PRD title

    # Content fields
    description: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    technical_requirements: Optional[str] = None
    business_value: Optional[str] = None

    # Status and workflow
    status: PRDStatus = PRDStatus.BACKLOG
    priority: PRDPriority = PRDPriority.MEDIUM

    # Metadata
    created_at: Optional[str] = None  # ISO 8601 datetime string
    updated_at: Optional[str] = None  # ISO 8601 datetime string
    creator_login: Optional[str] = None
    assignee_login: Optional[str] = None

    # GitHub-specific fields
    content_id: Optional[str] = None  # ID of linked GitHub issue/PR
    content_url: Optional[str] = None  # URL to linked content
    content_type: Optional[str] = None  # "Issue", "PullRequest", "DraftIssue"

    # Project item fields
    position: Optional[int] = None  # Position within the project
    archived: bool = False

    # Custom field values (GitHub Projects v2 supports custom fields)
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate PRD data after initialization."""
        if not self.title or not self.title.strip():
            raise ValueError("PRD title cannot be empty")

        if not self.project_id or not self.project_id.strip():
            raise ValueError("PRD must be associated with a project")

    @classmethod
    def from_github_item(cls, item_data: Dict[str, Any], project_id: str) -> "PRD":
        """
        Create a PRD instance from a GitHub Projects v2 item response.

        Args:
            item_data: Raw GraphQL response data for a ProjectV2Item
            project_id: ID of the containing project

        Returns:
            PRD instance
        """
        # Extract content information
        content = item_data.get("content", {})
        content_type = content.get("__typename", "DraftIssue")
        content_id = content.get("id") if content else None
        content_url = content.get("url") if content else None

        # Extract basic item information
        title = ""
        description = ""

        if content_type == "Issue":
            title = content.get("title", "Untitled PRD")
            description = content.get("body", "")
        elif content_type == "PullRequest":
            title = content.get("title", "Untitled PRD")
            description = content.get("body", "")
        else:
            # For draft issues or direct project items
            title = item_data.get("title", "Untitled PRD")
            description = item_data.get("body", "")

        # Extract field values (GitHub Projects v2 custom fields)
        field_values = item_data.get("fieldValues", {}).get("nodes", [])
        custom_fields = {}
        status = PRDStatus.BACKLOG
        priority = PRDPriority.MEDIUM

        for field_value in field_values:
            field_name = field_value.get("field", {}).get("name", "").lower()
            value = None

            # Handle different field types
            if "text" in field_value:
                value = field_value["text"]
            elif "number" in field_value:
                value = field_value["number"]
            elif "date" in field_value:
                value = field_value["date"]
            elif "singleSelectOption" in field_value:
                # For status and priority fields
                option_name = field_value.get("singleSelectOption", {}).get("name", "")
                value = option_name

                if field_name in ["status", "state"]:
                    try:
                        status = PRDStatus(option_name)
                    except ValueError:
                        status = PRDStatus.BACKLOG
                elif field_name == "priority":
                    try:
                        priority = PRDPriority(option_name)
                    except ValueError:
                        priority = PRDPriority.MEDIUM

            if value is not None:
                custom_fields[field_name] = value

        # Extract creator and assignee information
        creator_login = None
        assignee_login = None

        if content_type in ["Issue", "PullRequest"] and content:
            creator_login = content.get("author", {}).get("login")
            assignees = content.get("assignees", {}).get("nodes", [])
            if assignees:
                assignee_login = assignees[0].get("login")

        return cls(
            id=item_data["id"],
            project_id=project_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            created_at=item_data.get("createdAt"),
            updated_at=item_data.get("updatedAt"),
            creator_login=creator_login,
            assignee_login=assignee_login,
            content_id=content_id,
            content_url=content_url,
            content_type=content_type,
            position=item_data.get("position"),
            archived=item_data.get("archived", False),
            custom_fields=custom_fields,
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the PRD instance to a dictionary.

        Returns:
            Dictionary representation of the PRD
        """
        result = {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "status": self.status.value,
            "priority": self.priority.value,
            "archived": self.archived,
        }

        # Add optional fields if they have values
        optional_fields = [
            "description",
            "acceptance_criteria",
            "technical_requirements",
            "business_value",
            "created_at",
            "updated_at",
            "creator_login",
            "assignee_login",
            "content_id",
            "content_url",
            "content_type",
            "position",
        ]

        for field_name in optional_fields:
            value = getattr(self, field_name)
            if value is not None:
                result[field_name] = value

        # Add custom fields
        if self.custom_fields:
            result["custom_fields"] = self.custom_fields

        return result

    def __str__(self) -> str:
        """String representation of the PRD."""
        return f"PRD: {self.title} ({self.status.value}, {self.priority.value})"

    def __eq__(self, other) -> bool:
        """Equality comparison based on PRD ID."""
        if not isinstance(other, PRD):
            return False
        return self.id == other.id

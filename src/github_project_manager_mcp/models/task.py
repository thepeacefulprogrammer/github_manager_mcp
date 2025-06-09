"""
Task data models for GitHub Projects v2.

This module provides data models for managing Tasks as items within GitHub Projects v2,
including status tracking, priority management, parent PRD relationship, and
comprehensive metadata handling.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskStatus(Enum):
    """Valid status values for Tasks in GitHub Projects v2."""

    TODO = "Todo"
    IN_PROGRESS = "In Progress"
    BLOCKED = "Blocked"
    REVIEW = "Review"
    DONE = "Done"
    CANCELLED = "Cancelled"


class TaskPriority(Enum):
    """Priority levels for Tasks."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


@dataclass
class Task:
    """
    Represents a Task as a GitHub Projects v2 item with relationship to parent PRD.

    This model maps to GitHub GraphQL API ProjectV2Item objects that represent
    Tasks with custom fields for status, priority, parent PRD relationship,
    and time tracking metadata.
    """

    # Required fields
    id: str  # GitHub's global node ID for the project item
    project_id: str  # ID of the containing project
    parent_prd_id: str  # ID of the parent PRD this task belongs to
    title: str  # Task title

    # Content fields
    description: Optional[str] = None

    # Status and workflow
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM

    # Time tracking
    estimated_hours: Optional[int] = None
    actual_hours: Optional[int] = None

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
        """Validate Task data after initialization."""
        if not self.title or not self.title.strip():
            raise ValueError("Task title cannot be empty")

        if not self.project_id or not self.project_id.strip():
            raise ValueError("Task must be associated with a project")

        if not self.parent_prd_id or not self.parent_prd_id.strip():
            raise ValueError("Task must be associated with a parent PRD")

    @classmethod
    def from_github_item(cls, item_data: Dict[str, Any], project_id: str) -> "Task":
        """
        Create a Task instance from a GitHub Projects v2 item response.

        Args:
            item_data: Raw GraphQL response data for a ProjectV2Item
            project_id: ID of the containing project

        Returns:
            Task instance
        """
        # Extract content information
        content = item_data.get("content", {})
        content_type = content.get("__typename") if content else None
        content_id = content.get("id") if content else None
        content_url = content.get("url") if content else None

        # Extract basic item information
        title = ""
        description = ""

        if content_type == "Issue":
            title = content.get("title", "Untitled Task")
            description = content.get("body", "")
        elif content_type == "PullRequest":
            title = content.get("title", "Untitled Task")
            description = content.get("body", "")
        else:
            # For draft issues or direct project items
            title = item_data.get("title", "Untitled Task")
            description = item_data.get("body", "")

        # Extract field values (GitHub Projects v2 custom fields)
        field_values = item_data.get("fieldValues", {}).get("nodes", [])
        custom_fields = {}
        status = TaskStatus.TODO
        priority = TaskPriority.MEDIUM
        parent_prd_id = None
        estimated_hours = None
        actual_hours = None

        for field_value in field_values:
            field_name = field_value.get("field", {}).get("name", "").lower()
            value = None

            # Handle different field types
            if "text" in field_value:
                value = field_value["text"]
                # Special handling for parent PRD field
                if field_name in ["parent prd", "parent_prd", "prd"]:
                    parent_prd_id = value
            elif "number" in field_value:
                value = field_value["number"]
                if field_name in ["estimated hours", "estimated_hours"]:
                    estimated_hours = value
                elif field_name in ["actual hours", "actual_hours"]:
                    actual_hours = value
            elif "date" in field_value:
                value = field_value["date"]
            elif "singleSelectOption" in field_value:
                # For status and priority fields
                option_name = field_value.get("singleSelectOption", {}).get("name", "")
                value = option_name

                if field_name in ["status", "state"]:
                    try:
                        status = TaskStatus(option_name)
                    except ValueError:
                        status = TaskStatus.TODO
                elif field_name == "priority":
                    try:
                        priority = TaskPriority(option_name)
                    except ValueError:
                        priority = TaskPriority.MEDIUM

            if value is not None:
                custom_fields[field_name] = value

        # Validate that parent PRD is specified
        if not parent_prd_id:
            raise ValueError("Task must have a parent PRD specified")

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
            parent_prd_id=parent_prd_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            estimated_hours=estimated_hours,
            actual_hours=actual_hours,
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
        Convert the Task instance to a dictionary.

        Returns:
            Dictionary representation of the Task
        """
        result = {
            "id": self.id,
            "project_id": self.project_id,
            "parent_prd_id": self.parent_prd_id,
            "title": self.title,
            "status": self.status.value,
            "priority": self.priority.value,
            "archived": self.archived,
        }

        # Add optional fields if they have values
        optional_fields = [
            "description",
            "estimated_hours",
            "actual_hours",
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
        """String representation of the Task."""
        return f"Task: {self.title} ({self.status.value}, {self.priority.value}) [PRD: {self.parent_prd_id}]"

    def __eq__(self, other) -> bool:
        """Equality comparison based on Task ID."""
        if not isinstance(other, Task):
            return False
        return self.id == other.id

    # Time tracking and progress methods
    def is_overestimated(self) -> bool:
        """Check if actual hours exceed estimated hours."""
        if self.estimated_hours is None or self.actual_hours is None:
            return False
        return self.actual_hours > self.estimated_hours

    def get_time_remaining(self) -> Optional[int]:
        """Get remaining hours based on estimate and actual hours."""
        if self.estimated_hours is None:
            return None
        if self.actual_hours is None:
            return self.estimated_hours
        return self.estimated_hours - self.actual_hours

    def get_progress_percentage(self) -> Optional[float]:
        """Get progress percentage based on time tracking."""
        if self.estimated_hours is None or self.estimated_hours == 0:
            return None
        if self.actual_hours is None:
            return 0.0
        return (self.actual_hours / self.estimated_hours) * 100.0

    # Status checking convenience methods
    def is_active(self) -> bool:
        """Check if task is currently being worked on."""
        return self.status == TaskStatus.IN_PROGRESS

    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status == TaskStatus.DONE

    def is_blocked(self) -> bool:
        """Check if task is blocked."""
        return self.status == TaskStatus.BLOCKED

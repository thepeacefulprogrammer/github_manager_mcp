"""
Subtask data models for GitHub Projects v2.

This module provides data models for managing Subtasks as checklist items within
GitHub Projects v2 Tasks, including completion tracking, ordering, and
comprehensive metadata handling.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SubtaskStatus(Enum):
    """Valid status values for Subtasks."""

    INCOMPLETE = "Incomplete"
    COMPLETE = "Complete"


@dataclass
class Subtask:
    """
    Represents a Subtask as a checklist item within a GitHub Projects v2 Task.

    This model maps to GitHub checklist items or custom field data that represent
    Subtasks with status tracking, ordering, and completion metadata.
    """

    # Required fields
    id: str  # Unique identifier for the subtask
    parent_task_id: str  # ID of the parent Task this subtask belongs to
    title: str  # Subtask title/description
    order: int  # Position/order within the parent task's subtask list

    # Status and completion
    status: SubtaskStatus = SubtaskStatus.INCOMPLETE

    # Content fields
    description: Optional[str] = None

    # Metadata
    created_at: Optional[str] = None  # ISO 8601 datetime string
    updated_at: Optional[str] = None  # ISO 8601 datetime string
    completed_at: Optional[str] = None  # ISO 8601 datetime string when marked complete
    assignee_login: Optional[str] = None

    # Custom field values (for additional metadata)
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate Subtask data after initialization."""
        if not self.title or not self.title.strip():
            raise ValueError("Subtask title cannot be empty")

        if not self.parent_task_id or not self.parent_task_id.strip():
            raise ValueError("Subtask must be associated with a parent Task")

        if self.order <= 0:
            raise ValueError("Subtask order must be positive")

    @classmethod
    def from_checklist_item(
        cls, checklist_data: Dict[str, Any], parent_task_id: str
    ) -> "Subtask":
        """
        Create a Subtask instance from a GitHub checklist item response.

        Args:
            checklist_data: Raw GitHub checklist item data
            parent_task_id: ID of the parent task

        Returns:
            Subtask instance
        """
        status = (
            SubtaskStatus.COMPLETE
            if checklist_data.get("checked", False)
            else SubtaskStatus.INCOMPLETE
        )
        completed_at = (
            checklist_data.get("completedAt")
            if status == SubtaskStatus.COMPLETE
            else None
        )

        return cls(
            id=checklist_data["id"],
            parent_task_id=parent_task_id,
            title=checklist_data.get("text", "Untitled Subtask"),
            order=checklist_data.get("position", 1),
            status=status,
            created_at=checklist_data.get("createdAt"),
            updated_at=checklist_data.get("updatedAt"),
            completed_at=completed_at,
        )

    @classmethod
    def from_custom_field_data(cls, field_data: Dict[str, Any]) -> "Subtask":
        """
        Create a Subtask instance from GitHub Projects v2 custom field data.

        Args:
            field_data: Raw custom field data containing subtask information

        Returns:
            Subtask instance
        """
        status_str = field_data.get("status", "Incomplete")
        try:
            status = SubtaskStatus(status_str)
        except ValueError:
            status = SubtaskStatus.INCOMPLETE

        completed_at = (
            field_data.get("completed_at") if status == SubtaskStatus.COMPLETE else None
        )

        return cls(
            id=field_data["id"],
            parent_task_id=field_data["parent_task_id"],
            title=field_data.get("title", "Untitled Subtask"),
            description=field_data.get("description"),
            order=field_data.get("order", 1),
            status=status,
            created_at=field_data.get("created_at"),
            updated_at=field_data.get("updated_at"),
            completed_at=completed_at,
            assignee_login=field_data.get("assignee_login"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Subtask instance to a dictionary.

        Returns:
            Dictionary representation of the Subtask
        """
        result = {
            "id": self.id,
            "parent_task_id": self.parent_task_id,
            "title": self.title,
            "order": self.order,
            "status": self.status.value,
        }

        # Add optional fields if they have values
        optional_fields = [
            "description",
            "created_at",
            "updated_at",
            "completed_at",
            "assignee_login",
        ]

        for field_name in optional_fields:
            value = getattr(self, field_name)
            if value is not None:
                result[field_name] = value

        # Add custom fields
        if self.custom_fields:
            result["custom_fields"] = self.custom_fields

        return result

    def to_checklist_item(self) -> Dict[str, Any]:
        """
        Convert the Subtask to GitHub checklist item format.

        Returns:
            Dictionary in GitHub checklist item format
        """
        return {
            "id": self.id,
            "text": self.title,
            "checked": self.status == SubtaskStatus.COMPLETE,
            "position": self.order,
        }

    def to_checklist_format(self) -> str:
        """
        Convert the Subtask to markdown checklist format.

        Returns:
            Markdown checklist item string
        """
        checkbox = "[x]" if self.status == SubtaskStatus.COMPLETE else "[ ]"
        return f"- {checkbox} {self.title}"

    def __str__(self) -> str:
        """String representation of the Subtask."""
        return (
            f"Subtask: {self.title} (Order: {self.order}, Status: {self.status.value})"
        )

    def __eq__(self, other) -> bool:
        """Equality comparison based on Subtask ID."""
        if not isinstance(other, Subtask):
            return False
        return self.id == other.id

    # Status checking convenience methods
    def is_completed(self) -> bool:
        """Check if subtask is completed."""
        return self.status == SubtaskStatus.COMPLETE

    def is_pending(self) -> bool:
        """Check if subtask is pending/incomplete."""
        return self.status == SubtaskStatus.INCOMPLETE

    # Status management methods
    def mark_complete(self) -> None:
        """Mark the subtask as complete."""
        self.status = SubtaskStatus.COMPLETE
        if self.completed_at is None:
            self.completed_at = datetime.utcnow().isoformat() + "Z"

    def mark_incomplete(self) -> None:
        """Mark the subtask as incomplete."""
        self.status = SubtaskStatus.INCOMPLETE
        self.completed_at = None

    # Ordering methods
    def reorder(self, new_order: int) -> None:
        """
        Change the order/position of the subtask.

        Args:
            new_order: New order position (must be positive)

        Raises:
            ValueError: If new_order is not positive
        """
        if new_order <= 0:
            raise ValueError("Order must be positive")
        self.order = new_order

"""
Unit tests for Subtask data model.

Tests the Subtask model's functionality including:
- Subtask creation and validation
- Parent Task relationship management
- Checklist item structure and completion tracking
- Status handling for subtasks
- GitHub Projects v2 API integration
- Data serialization and deserialization
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from src.github_project_manager_mcp.models.subtask import Subtask, SubtaskStatus


class TestSubtaskStatus:
    """Test SubtaskStatus enum."""

    def test_subtask_status_values(self):
        """Test that SubtaskStatus enum has correct values."""
        assert SubtaskStatus.INCOMPLETE.value == "Incomplete"
        assert SubtaskStatus.COMPLETE.value == "Complete"

    def test_subtask_status_iteration(self):
        """Test that all SubtaskStatus values are accessible."""
        statuses = list(SubtaskStatus)
        assert len(statuses) == 2
        assert SubtaskStatus.INCOMPLETE in statuses
        assert SubtaskStatus.COMPLETE in statuses


class TestSubtask:
    """Test Subtask data model."""

    def test_subtask_creation_with_required_fields(self):
        """Test creating a subtask with only required fields."""
        subtask = Subtask(
            id="SUBTASK_123",
            parent_task_id="PVTI_task456",
            title="Set up database connection",
            order=1,
        )

        assert subtask.id == "SUBTASK_123"
        assert subtask.parent_task_id == "PVTI_task456"
        assert subtask.title == "Set up database connection"
        assert subtask.order == 1
        assert subtask.status == SubtaskStatus.INCOMPLETE
        assert subtask.description is None
        assert subtask.completed_at is None
        assert subtask.custom_fields == {}

    def test_subtask_creation_with_all_fields(self):
        """Test creating a subtask with all fields populated."""
        subtask = Subtask(
            id="SUBTASK_123",
            parent_task_id="PVTI_task456",
            title="Set up database connection",
            description="Configure PostgreSQL connection with connection pooling",
            order=1,
            status=SubtaskStatus.COMPLETE,
            created_at="2024-01-01T10:00:00Z",
            updated_at="2024-01-02T15:30:00Z",
            completed_at="2024-01-02T14:00:00Z",
            assignee_login="developer1",
            custom_fields={"complexity": "low", "estimated_minutes": 30},
        )

        assert subtask.id == "SUBTASK_123"
        assert subtask.parent_task_id == "PVTI_task456"
        assert subtask.title == "Set up database connection"
        assert (
            subtask.description
            == "Configure PostgreSQL connection with connection pooling"
        )
        assert subtask.order == 1
        assert subtask.status == SubtaskStatus.COMPLETE
        assert subtask.created_at == "2024-01-01T10:00:00Z"
        assert subtask.updated_at == "2024-01-02T15:30:00Z"
        assert subtask.completed_at == "2024-01-02T14:00:00Z"
        assert subtask.assignee_login == "developer1"
        assert subtask.custom_fields == {"complexity": "low", "estimated_minutes": 30}

    def test_subtask_validation_empty_title(self):
        """Test that empty title raises validation error."""
        with pytest.raises(ValueError, match="Subtask title cannot be empty"):
            Subtask(id="SUBTASK_123", parent_task_id="PVTI_task456", title="", order=1)

        with pytest.raises(ValueError, match="Subtask title cannot be empty"):
            Subtask(
                id="SUBTASK_123", parent_task_id="PVTI_task456", title="   ", order=1
            )

    def test_subtask_validation_empty_parent_task_id(self):
        """Test that empty parent_task_id raises validation error."""
        with pytest.raises(
            ValueError, match="Subtask must be associated with a parent Task"
        ):
            Subtask(id="SUBTASK_123", parent_task_id="", title="Test subtask", order=1)

    def test_subtask_validation_negative_order(self):
        """Test that negative order raises validation error."""
        with pytest.raises(ValueError, match="Subtask order must be positive"):
            Subtask(
                id="SUBTASK_123",
                parent_task_id="PVTI_task456",
                title="Test subtask",
                order=-1,
            )

    def test_subtask_validation_zero_order(self):
        """Test that zero order raises validation error."""
        with pytest.raises(ValueError, match="Subtask order must be positive"):
            Subtask(
                id="SUBTASK_123",
                parent_task_id="PVTI_task456",
                title="Test subtask",
                order=0,
            )

    def test_subtask_from_checklist_item(self):
        """Test creating Subtask from GitHub checklist item data."""
        checklist_data = {
            "id": "SUBTASK_123",
            "text": "Set up database connection",
            "checked": False,
            "position": 1,
            "createdAt": "2024-01-01T10:00:00Z",
            "updatedAt": "2024-01-02T15:30:00Z",
        }

        subtask = Subtask.from_checklist_item(
            checklist_data, parent_task_id="PVTI_task456"
        )

        assert subtask.id == "SUBTASK_123"
        assert subtask.parent_task_id == "PVTI_task456"
        assert subtask.title == "Set up database connection"
        assert subtask.order == 1
        assert subtask.status == SubtaskStatus.INCOMPLETE
        assert subtask.created_at == "2024-01-01T10:00:00Z"
        assert subtask.updated_at == "2024-01-02T15:30:00Z"
        assert subtask.completed_at is None

    def test_subtask_from_checklist_item_completed(self):
        """Test creating completed Subtask from GitHub checklist item data."""
        checklist_data = {
            "id": "SUBTASK_123",
            "text": "Configure database schema",
            "checked": True,
            "position": 2,
            "createdAt": "2024-01-01T10:00:00Z",
            "updatedAt": "2024-01-02T15:30:00Z",
            "completedAt": "2024-01-02T14:00:00Z",
        }

        subtask = Subtask.from_checklist_item(
            checklist_data, parent_task_id="PVTI_task456"
        )

        assert subtask.id == "SUBTASK_123"
        assert subtask.parent_task_id == "PVTI_task456"
        assert subtask.title == "Configure database schema"
        assert subtask.order == 2
        assert subtask.status == SubtaskStatus.COMPLETE
        assert subtask.completed_at == "2024-01-02T14:00:00Z"

    def test_subtask_from_custom_field_data(self):
        """Test creating Subtask from GitHub Projects v2 custom field data."""
        custom_field_data = {
            "id": "SUBTASK_456",
            "title": "Write unit tests",
            "description": "Create comprehensive test coverage for authentication module",
            "status": "Complete",
            "order": 3,
            "parent_task_id": "PVTI_task789",
            "created_at": "2024-01-01T09:00:00Z",
            "updated_at": "2024-01-03T12:00:00Z",
            "completed_at": "2024-01-03T11:30:00Z",
            "assignee_login": "tester1",
        }

        subtask = Subtask.from_custom_field_data(custom_field_data)

        assert subtask.id == "SUBTASK_456"
        assert subtask.parent_task_id == "PVTI_task789"
        assert subtask.title == "Write unit tests"
        assert (
            subtask.description
            == "Create comprehensive test coverage for authentication module"
        )
        assert subtask.order == 3
        assert subtask.status == SubtaskStatus.COMPLETE
        assert subtask.created_at == "2024-01-01T09:00:00Z"
        assert subtask.updated_at == "2024-01-03T12:00:00Z"
        assert subtask.completed_at == "2024-01-03T11:30:00Z"
        assert subtask.assignee_login == "tester1"

    def test_subtask_from_custom_field_data_incomplete(self):
        """Test creating incomplete Subtask from custom field data."""
        custom_field_data = {
            "id": "SUBTASK_789",
            "title": "Deploy to staging",
            "status": "Incomplete",
            "order": 4,
            "parent_task_id": "PVTI_task999",
        }

        subtask = Subtask.from_custom_field_data(custom_field_data)

        assert subtask.id == "SUBTASK_789"
        assert subtask.parent_task_id == "PVTI_task999"
        assert subtask.title == "Deploy to staging"
        assert subtask.order == 4
        assert subtask.status == SubtaskStatus.INCOMPLETE
        assert subtask.completed_at is None

    def test_subtask_to_dict(self):
        """Test converting Subtask to dictionary."""
        subtask = Subtask(
            id="SUBTASK_123",
            parent_task_id="PVTI_task456",
            title="Set up database connection",
            description="Configure PostgreSQL connection",
            order=1,
            status=SubtaskStatus.COMPLETE,
            created_at="2024-01-01T10:00:00Z",
            updated_at="2024-01-02T15:30:00Z",
            completed_at="2024-01-02T14:00:00Z",
            assignee_login="developer1",
            custom_fields={"complexity": "low"},
        )

        result = subtask.to_dict()

        expected = {
            "id": "SUBTASK_123",
            "parent_task_id": "PVTI_task456",
            "title": "Set up database connection",
            "description": "Configure PostgreSQL connection",
            "order": 1,
            "status": "Complete",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-02T15:30:00Z",
            "completed_at": "2024-01-02T14:00:00Z",
            "assignee_login": "developer1",
            "custom_fields": {"complexity": "low"},
        }

        assert result == expected

    def test_subtask_to_dict_minimal(self):
        """Test converting minimal Subtask to dictionary."""
        subtask = Subtask(
            id="SUBTASK_123",
            parent_task_id="PVTI_task456",
            title="Test subtask",
            order=1,
        )

        result = subtask.to_dict()

        expected = {
            "id": "SUBTASK_123",
            "parent_task_id": "PVTI_task456",
            "title": "Test subtask",
            "order": 1,
            "status": "Incomplete",
        }

        assert result == expected

    def test_subtask_to_checklist_item(self):
        """Test converting Subtask to GitHub checklist item format."""
        subtask = Subtask(
            id="SUBTASK_123",
            parent_task_id="PVTI_task456",
            title="Set up database connection",
            order=1,
            status=SubtaskStatus.COMPLETE,
            completed_at="2024-01-02T14:00:00Z",
        )

        result = subtask.to_checklist_item()

        expected = {
            "id": "SUBTASK_123",
            "text": "Set up database connection",
            "checked": True,
            "position": 1,
        }

        assert result == expected

    def test_subtask_to_checklist_item_incomplete(self):
        """Test converting incomplete Subtask to checklist item format."""
        subtask = Subtask(
            id="SUBTASK_123",
            parent_task_id="PVTI_task456",
            title="Configure logging",
            order=2,
            status=SubtaskStatus.INCOMPLETE,
        )

        result = subtask.to_checklist_item()

        expected = {
            "id": "SUBTASK_123",
            "text": "Configure logging",
            "checked": False,
            "position": 2,
        }

        assert result == expected

    def test_subtask_string_representation(self):
        """Test string representation of Subtask."""
        subtask = Subtask(
            id="SUBTASK_123",
            parent_task_id="PVTI_task456",
            title="Set up database connection",
            order=1,
            status=SubtaskStatus.COMPLETE,
        )

        expected = "Subtask: Set up database connection (Order: 1, Status: Complete)"
        assert str(subtask) == expected

    def test_subtask_equality(self):
        """Test equality comparison of Subtask instances."""
        subtask1 = Subtask(
            id="SUBTASK_123", parent_task_id="PVTI_task456", title="Task 1", order=1
        )

        subtask2 = Subtask(
            id="SUBTASK_123", parent_task_id="PVTI_task789", title="Task 2", order=2
        )

        subtask3 = Subtask(
            id="SUBTASK_456", parent_task_id="PVTI_task456", title="Task 3", order=1
        )

        # Same ID should be equal
        assert subtask1 == subtask2
        # Different ID should not be equal
        assert subtask1 != subtask3
        # Different types should not be equal
        assert subtask1 != "not a subtask"

    def test_subtask_completion_methods(self):
        """Test subtask completion status methods."""
        incomplete_subtask = Subtask(
            id="SUBTASK_123",
            parent_task_id="PVTI_task456",
            title="Incomplete task",
            order=1,
            status=SubtaskStatus.INCOMPLETE,
        )

        complete_subtask = Subtask(
            id="SUBTASK_456",
            parent_task_id="PVTI_task456",
            title="Complete task",
            order=2,
            status=SubtaskStatus.COMPLETE,
            completed_at="2024-01-02T14:00:00Z",
        )

        # Test is_completed method
        assert not incomplete_subtask.is_completed()
        assert complete_subtask.is_completed()

        # Test is_pending method
        assert incomplete_subtask.is_pending()
        assert not complete_subtask.is_pending()

    def test_subtask_mark_complete(self):
        """Test marking a subtask as complete."""
        subtask = Subtask(
            id="SUBTASK_123",
            parent_task_id="PVTI_task456",
            title="Test task",
            order=1,
            status=SubtaskStatus.INCOMPLETE,
        )

        # Mark as complete
        subtask.mark_complete()

        assert subtask.status == SubtaskStatus.COMPLETE
        assert subtask.completed_at is not None

    def test_subtask_mark_incomplete(self):
        """Test marking a subtask as incomplete."""
        subtask = Subtask(
            id="SUBTASK_123",
            parent_task_id="PVTI_task456",
            title="Test task",
            order=1,
            status=SubtaskStatus.COMPLETE,
            completed_at="2024-01-02T14:00:00Z",
        )

        # Mark as incomplete
        subtask.mark_incomplete()

        assert subtask.status == SubtaskStatus.INCOMPLETE
        assert subtask.completed_at is None

    def test_subtask_reorder(self):
        """Test reordering subtasks."""
        subtask = Subtask(
            id="SUBTASK_123", parent_task_id="PVTI_task456", title="Test task", order=1
        )

        # Change order
        subtask.reorder(5)

        assert subtask.order == 5

    def test_subtask_reorder_invalid(self):
        """Test reordering with invalid order values."""
        subtask = Subtask(
            id="SUBTASK_123", parent_task_id="PVTI_task456", title="Test task", order=1
        )

        # Test negative order
        with pytest.raises(ValueError, match="Order must be positive"):
            subtask.reorder(-1)

        # Test zero order
        with pytest.raises(ValueError, match="Order must be positive"):
            subtask.reorder(0)

    def test_subtask_checklist_formatting(self):
        """Test formatting subtask for checklist display."""
        incomplete_subtask = Subtask(
            id="SUBTASK_123",
            parent_task_id="PVTI_task456",
            title="Incomplete task",
            order=1,
            status=SubtaskStatus.INCOMPLETE,
        )

        complete_subtask = Subtask(
            id="SUBTASK_456",
            parent_task_id="PVTI_task456",
            title="Complete task",
            order=2,
            status=SubtaskStatus.COMPLETE,
        )

        # Test checklist format
        assert incomplete_subtask.to_checklist_format() == "- [ ] Incomplete task"
        assert complete_subtask.to_checklist_format() == "- [x] Complete task"

    def test_subtask_validation_edge_cases(self):
        """Test subtask validation with edge cases."""
        # Test very long title
        long_title = "A" * 1000
        subtask = Subtask(
            id="SUBTASK_123", parent_task_id="PVTI_task456", title=long_title, order=1
        )
        assert subtask.title == long_title

        # Test unicode characters in title
        unicode_title = "测试任务 🚀"
        subtask = Subtask(
            id="SUBTASK_123",
            parent_task_id="PVTI_task456",
            title=unicode_title,
            order=1,
        )
        assert subtask.title == unicode_title

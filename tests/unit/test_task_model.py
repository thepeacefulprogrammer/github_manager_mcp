"""
Unit tests for Task data model.

Tests the Task model's functionality including:
- Task creation and validation
- Parent PRD relationship management
- Status and priority handling
- GitHub Projects v2 API integration
- Data serialization and deserialization
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from src.github_project_manager_mcp.models.task import Task, TaskPriority, TaskStatus


class TestTaskStatus:
    """Test TaskStatus enum."""

    def test_task_status_values(self):
        """Test that TaskStatus enum has correct values."""
        assert TaskStatus.TODO.value == "Todo"
        assert TaskStatus.IN_PROGRESS.value == "In Progress"
        assert TaskStatus.BLOCKED.value == "Blocked"
        assert TaskStatus.REVIEW.value == "Review"
        assert TaskStatus.DONE.value == "Done"
        assert TaskStatus.CANCELLED.value == "Cancelled"

    def test_task_status_iteration(self):
        """Test that all TaskStatus values are accessible."""
        statuses = list(TaskStatus)
        assert len(statuses) == 6
        assert TaskStatus.TODO in statuses
        assert TaskStatus.DONE in statuses


class TestTaskPriority:
    """Test TaskPriority enum."""

    def test_task_priority_values(self):
        """Test that TaskPriority enum has correct values."""
        assert TaskPriority.LOW.value == "Low"
        assert TaskPriority.MEDIUM.value == "Medium"
        assert TaskPriority.HIGH.value == "High"
        assert TaskPriority.CRITICAL.value == "Critical"

    def test_task_priority_iteration(self):
        """Test that all TaskPriority values are accessible."""
        priorities = list(TaskPriority)
        assert len(priorities) == 4
        assert TaskPriority.LOW in priorities
        assert TaskPriority.CRITICAL in priorities


class TestTask:
    """Test Task data model."""

    def test_task_creation_with_required_fields(self):
        """Test creating a task with only required fields."""
        task = Task(
            id="PVTI_task123",
            project_id="PVT_project123",
            parent_prd_id="PVTI_prd456",
            title="Implement user authentication",
        )

        assert task.id == "PVTI_task123"
        assert task.project_id == "PVT_project123"
        assert task.parent_prd_id == "PVTI_prd456"
        assert task.title == "Implement user authentication"
        assert task.status == TaskStatus.TODO
        assert task.priority == TaskPriority.MEDIUM
        assert task.description is None
        assert task.archived is False
        assert task.custom_fields == {}

    def test_task_creation_with_all_fields(self):
        """Test creating a task with all fields populated."""
        task = Task(
            id="PVTI_task123",
            project_id="PVT_project123",
            parent_prd_id="PVTI_prd456",
            title="Implement user authentication",
            description="Add OAuth2 and JWT token support",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            estimated_hours=8,
            actual_hours=5,
            created_at="2024-01-01T10:00:00Z",
            updated_at="2024-01-02T15:30:00Z",
            creator_login="developer1",
            assignee_login="developer2",
            content_id="ISS_123",
            content_url="https://github.com/user/repo/issues/123",
            content_type="Issue",
            position=1,
            archived=False,
            custom_fields={"complexity": "medium", "component": "auth"},
        )

        assert task.id == "PVTI_task123"
        assert task.project_id == "PVT_project123"
        assert task.parent_prd_id == "PVTI_prd456"
        assert task.title == "Implement user authentication"
        assert task.description == "Add OAuth2 and JWT token support"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.HIGH
        assert task.estimated_hours == 8
        assert task.actual_hours == 5
        assert task.created_at == "2024-01-01T10:00:00Z"
        assert task.updated_at == "2024-01-02T15:30:00Z"
        assert task.creator_login == "developer1"
        assert task.assignee_login == "developer2"
        assert task.content_id == "ISS_123"
        assert task.content_url == "https://github.com/user/repo/issues/123"
        assert task.content_type == "Issue"
        assert task.position == 1
        assert task.archived is False
        assert task.custom_fields == {"complexity": "medium", "component": "auth"}

    def test_task_validation_empty_title(self):
        """Test that empty title raises validation error."""
        with pytest.raises(ValueError, match="Task title cannot be empty"):
            Task(
                id="PVTI_task123",
                project_id="PVT_project123",
                parent_prd_id="PVTI_prd456",
                title="",
            )

        with pytest.raises(ValueError, match="Task title cannot be empty"):
            Task(
                id="PVTI_task123",
                project_id="PVT_project123",
                parent_prd_id="PVTI_prd456",
                title="   ",
            )

    def test_task_validation_empty_project_id(self):
        """Test that empty project_id raises validation error."""
        with pytest.raises(ValueError, match="Task must be associated with a project"):
            Task(
                id="PVTI_task123",
                project_id="",
                parent_prd_id="PVTI_prd456",
                title="Test task",
            )

    def test_task_validation_empty_parent_prd_id(self):
        """Test that empty parent_prd_id raises validation error."""
        with pytest.raises(
            ValueError, match="Task must be associated with a parent PRD"
        ):
            Task(
                id="PVTI_task123",
                project_id="PVT_project123",
                parent_prd_id="",
                title="Test task",
            )

    def test_task_from_github_item_issue_content(self):
        """Test creating Task from GitHub Projects v2 item with Issue content."""
        item_data = {
            "id": "PVTI_task123",
            "createdAt": "2024-01-01T10:00:00Z",
            "updatedAt": "2024-01-02T15:30:00Z",
            "position": 1,
            "archived": False,
            "content": {
                "__typename": "Issue",
                "id": "ISS_123",
                "title": "Implement user authentication",
                "body": "Add OAuth2 and JWT token support",
                "url": "https://github.com/user/repo/issues/123",
                "author": {"login": "developer1"},
                "assignees": {"nodes": [{"login": "developer2"}]},
            },
            "fieldValues": {
                "nodes": [
                    {
                        "field": {"name": "Status"},
                        "singleSelectOption": {"name": "In Progress"},
                    },
                    {
                        "field": {"name": "Priority"},
                        "singleSelectOption": {"name": "High"},
                    },
                    {"field": {"name": "Parent PRD"}, "text": "PVTI_prd456"},
                    {"field": {"name": "Estimated Hours"}, "number": 8},
                    {
                        "field": {"name": "Complexity"},
                        "singleSelectOption": {"name": "Medium"},
                    },
                ]
            },
        }

        task = Task.from_github_item(item_data, "PVT_project123")

        assert task.id == "PVTI_task123"
        assert task.project_id == "PVT_project123"
        assert task.parent_prd_id == "PVTI_prd456"
        assert task.title == "Implement user authentication"
        assert task.description == "Add OAuth2 and JWT token support"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.HIGH
        assert task.estimated_hours == 8
        assert task.creator_login == "developer1"
        assert task.assignee_login == "developer2"
        assert task.content_id == "ISS_123"
        assert task.content_url == "https://github.com/user/repo/issues/123"
        assert task.content_type == "Issue"
        assert task.custom_fields["complexity"] == "Medium"

    def test_task_from_github_item_draft_issue_content(self):
        """Test creating Task from GitHub Projects v2 item with DraftIssue content."""
        item_data = {
            "id": "PVTI_task123",
            "title": "Create database schema",
            "body": "Design and implement user tables",
            "createdAt": "2024-01-01T10:00:00Z",
            "updatedAt": "2024-01-02T15:30:00Z",
            "position": 2,
            "archived": False,
            "content": None,
            "fieldValues": {
                "nodes": [
                    {"field": {"name": "Parent PRD"}, "text": "PVTI_prd789"},
                    {
                        "field": {"name": "Status"},
                        "singleSelectOption": {"name": "Todo"},
                    },
                ]
            },
        }

        task = Task.from_github_item(item_data, "PVT_project123")

        assert task.id == "PVTI_task123"
        assert task.project_id == "PVT_project123"
        assert task.parent_prd_id == "PVTI_prd789"
        assert task.title == "Create database schema"
        assert task.description == "Design and implement user tables"
        assert task.status == TaskStatus.TODO
        assert task.priority == TaskPriority.MEDIUM
        assert task.content_type is None

    def test_task_from_github_item_missing_parent_prd(self):
        """Test that missing parent PRD field raises validation error."""
        item_data = {
            "id": "PVTI_task123",
            "title": "Test task",
            "createdAt": "2024-01-01T10:00:00Z",
            "fieldValues": {"nodes": []},
        }

        with pytest.raises(ValueError, match="Task must have a parent PRD specified"):
            Task.from_github_item(item_data, "PVT_project123")

    def test_task_to_dict(self):
        """Test converting Task to dictionary."""
        task = Task(
            id="PVTI_task123",
            project_id="PVT_project123",
            parent_prd_id="PVTI_prd456",
            title="Implement user authentication",
            description="Add OAuth2 and JWT token support",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            estimated_hours=8,
            actual_hours=5,
            creator_login="developer1",
            assignee_login="developer2",
            custom_fields={"complexity": "medium"},
        )

        result = task.to_dict()

        expected = {
            "id": "PVTI_task123",
            "project_id": "PVT_project123",
            "parent_prd_id": "PVTI_prd456",
            "title": "Implement user authentication",
            "description": "Add OAuth2 and JWT token support",
            "status": "In Progress",
            "priority": "High",
            "estimated_hours": 8,
            "actual_hours": 5,
            "creator_login": "developer1",
            "assignee_login": "developer2",
            "archived": False,
            "custom_fields": {"complexity": "medium"},
        }

        assert result == expected

    def test_task_to_dict_minimal(self):
        """Test converting minimal Task to dictionary."""
        task = Task(
            id="PVTI_task123",
            project_id="PVT_project123",
            parent_prd_id="PVTI_prd456",
            title="Simple task",
        )

        result = task.to_dict()

        expected = {
            "id": "PVTI_task123",
            "project_id": "PVT_project123",
            "parent_prd_id": "PVTI_prd456",
            "title": "Simple task",
            "status": "Todo",
            "priority": "Medium",
            "archived": False,
        }

        assert result == expected

    def test_task_string_representation(self):
        """Test Task string representation."""
        task = Task(
            id="PVTI_task123",
            project_id="PVT_project123",
            parent_prd_id="PVTI_prd456",
            title="Implement user authentication",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
        )

        expected = (
            "Task: Implement user authentication (In Progress, High) [PRD: PVTI_prd456]"
        )
        assert str(task) == expected

    def test_task_equality(self):
        """Test Task equality comparison based on ID."""
        task1 = Task(
            id="PVTI_task123",
            project_id="PVT_project123",
            parent_prd_id="PVTI_prd456",
            title="Task 1",
        )

        task2 = Task(
            id="PVTI_task123",
            project_id="PVT_different123",
            parent_prd_id="PVTI_prd789",
            title="Task 2",
        )

        task3 = Task(
            id="PVTI_task456",
            project_id="PVT_project123",
            parent_prd_id="PVTI_prd456",
            title="Task 3",
        )

        assert task1 == task2  # Same ID
        assert task1 != task3  # Different ID
        assert task1 != "not a task"  # Different type

    def test_task_progress_calculation(self):
        """Test task progress calculation methods."""
        task = Task(
            id="PVTI_task123",
            project_id="PVT_project123",
            parent_prd_id="PVTI_prd456",
            title="Test task",
            estimated_hours=10,
            actual_hours=7,
        )

        assert task.is_overestimated() is False
        assert task.get_time_remaining() == 3
        assert task.get_progress_percentage() == 70.0

        # Test with actual hours exceeding estimate
        task.actual_hours = 12
        assert task.is_overestimated() is True
        assert task.get_time_remaining() == -2
        assert task.get_progress_percentage() == 120.0

    def test_task_progress_no_estimate(self):
        """Test task progress methods when no estimate is provided."""
        task = Task(
            id="PVTI_task123",
            project_id="PVT_project123",
            parent_prd_id="PVTI_prd456",
            title="Test task",
            actual_hours=5,
        )

        assert task.is_overestimated() is False
        assert task.get_time_remaining() is None
        assert task.get_progress_percentage() is None

    def test_task_status_checking_methods(self):
        """Test convenience methods for checking task status."""
        task = Task(
            id="PVTI_task123",
            project_id="PVT_project123",
            parent_prd_id="PVTI_prd456",
            title="Test task",
            status=TaskStatus.IN_PROGRESS,
        )

        assert task.is_active() is True
        assert task.is_completed() is False
        assert task.is_blocked() is False

        task.status = TaskStatus.DONE
        assert task.is_active() is False
        assert task.is_completed() is True
        assert task.is_blocked() is False

        task.status = TaskStatus.BLOCKED
        assert task.is_active() is False
        assert task.is_completed() is False
        assert task.is_blocked() is True

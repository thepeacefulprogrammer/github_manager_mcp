"""
Unit tests for PRD (Product Requirements Document) data models.

This module provides comprehensive test coverage for PRD data models
used in GitHub Projects v2 integration.
"""

from datetime import datetime
from typing import Any, Dict

import pytest

from github_project_manager_mcp.models.prd import PRD, PRDPriority, PRDStatus


class TestPRDStatus:
    """Test cases for PRDStatus enum."""

    def test_prd_status_values(self):
        """Test that PRDStatus enum has correct values."""
        assert PRDStatus.BACKLOG.value == "Backlog"
        assert PRDStatus.THIS_SPRINT.value == "This Sprint"
        assert PRDStatus.UP_NEXT.value == "Up Next"
        assert PRDStatus.IN_PROGRESS.value == "In Progress"
        assert PRDStatus.DONE.value == "Done"
        assert PRDStatus.CANCELLED.value == "Cancelled"

    def test_prd_status_count(self):
        """Test that we have the expected number of status values."""
        statuses = list(PRDStatus)
        assert len(statuses) == 6


class TestPRDPriority:
    """Test cases for PRDPriority enum."""

    def test_prd_priority_values(self):
        """Test that PRDPriority enum has correct values."""
        assert PRDPriority.LOW.value == "Low"
        assert PRDPriority.MEDIUM.value == "Medium"
        assert PRDPriority.HIGH.value == "High"
        assert PRDPriority.CRITICAL.value == "Critical"

    def test_prd_priority_count(self):
        """Test that we have the expected number of priority values."""
        priorities = list(PRDPriority)
        assert len(priorities) == 4


class TestPRDModel:
    """Test cases for PRD data model."""

    def test_prd_creation_minimal(self):
        """Test creating a PRD with minimal required fields."""
        prd = PRD(id="PRD_123", project_id="PVT_kwDOBQfyVc0FoQ", title="Test PRD")

        assert prd.id == "PRD_123"
        assert prd.project_id == "PVT_kwDOBQfyVc0FoQ"
        assert prd.title == "Test PRD"
        assert prd.status == PRDStatus.BACKLOG  # Default
        assert prd.priority == PRDPriority.MEDIUM  # Default
        assert prd.archived is False  # Default
        assert prd.custom_fields == {}  # Default

    def test_prd_creation_full(self):
        """Test creating a PRD with all fields specified."""
        custom_fields = {"estimation": "5 days", "team": "Backend"}

        prd = PRD(
            id="PRD_456",
            project_id="PVT_kwDOBQfyVc0FoQ",
            title="Comprehensive PRD",
            description="Detailed PRD description",
            acceptance_criteria="User can complete the workflow",
            technical_requirements="React frontend, Node.js backend",
            business_value="Increases user engagement by 20%",
            status=PRDStatus.IN_PROGRESS,
            priority=PRDPriority.HIGH,
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-02T00:00:00Z",
            creator_login="developer1",
            assignee_login="developer2",
            content_id="ISSUE_789",
            content_url="https://github.com/user/repo/issues/1",
            content_type="Issue",
            position=3,
            archived=False,
            custom_fields=custom_fields,
        )

        assert prd.description == "Detailed PRD description"
        assert prd.acceptance_criteria == "User can complete the workflow"
        assert prd.technical_requirements == "React frontend, Node.js backend"
        assert prd.business_value == "Increases user engagement by 20%"
        assert prd.status == PRDStatus.IN_PROGRESS
        assert prd.priority == PRDPriority.HIGH
        assert prd.creator_login == "developer1"
        assert prd.assignee_login == "developer2"
        assert prd.content_type == "Issue"
        assert prd.position == 3
        assert prd.custom_fields == custom_fields

    def test_prd_validation_empty_title(self):
        """Test that PRD validation fails with empty title."""
        with pytest.raises(ValueError, match="PRD title cannot be empty"):
            PRD(id="PRD_123", project_id="PVT_kwDOBQfyVc0FoQ", title="")

    def test_prd_validation_whitespace_title(self):
        """Test that PRD validation fails with whitespace-only title."""
        with pytest.raises(ValueError, match="PRD title cannot be empty"):
            PRD(id="PRD_123", project_id="PVT_kwDOBQfyVc0FoQ", title="   ")

    def test_prd_validation_empty_project_id(self):
        """Test that PRD validation fails with empty project_id."""
        with pytest.raises(ValueError, match="PRD must be associated with a project"):
            PRD(id="PRD_123", project_id="", title="Test PRD")

    def test_prd_validation_whitespace_project_id(self):
        """Test that PRD validation fails with whitespace-only project_id."""
        with pytest.raises(ValueError, match="PRD must be associated with a project"):
            PRD(id="PRD_123", project_id="   ", title="Test PRD")

    def test_prd_to_dict_minimal(self):
        """Test converting minimal PRD to dictionary."""
        prd = PRD(id="PRD_123", project_id="PVT_kwDOBQfyVc0FoQ", title="Test PRD")

        result = prd.to_dict()
        expected = {
            "id": "PRD_123",
            "project_id": "PVT_kwDOBQfyVc0FoQ",
            "title": "Test PRD",
            "status": "Backlog",
            "priority": "Medium",
            "archived": False,
        }

        assert result == expected

    def test_prd_to_dict_full(self):
        """Test converting full PRD to dictionary."""
        custom_fields = {"estimation": "5 days"}

        prd = PRD(
            id="PRD_456",
            project_id="PVT_kwDOBQfyVc0FoQ",
            title="Full PRD",
            description="Test description",
            status=PRDStatus.DONE,
            priority=PRDPriority.CRITICAL,
            created_at="2025-01-01T00:00:00Z",
            creator_login="user1",
            content_type="Issue",
            position=1,
            custom_fields=custom_fields,
        )

        result = prd.to_dict()

        assert result["id"] == "PRD_456"
        assert result["title"] == "Full PRD"
        assert result["description"] == "Test description"
        assert result["status"] == "Done"
        assert result["priority"] == "Critical"
        assert result["created_at"] == "2025-01-01T00:00:00Z"
        assert result["creator_login"] == "user1"
        assert result["content_type"] == "Issue"
        assert result["position"] == 1
        assert result["custom_fields"] == custom_fields

    def test_prd_str_representation(self):
        """Test string representation of PRD."""
        prd = PRD(
            id="PRD_123",
            project_id="PVT_kwDOBQfyVc0FoQ",
            title="Test PRD",
            status=PRDStatus.IN_PROGRESS,
            priority=PRDPriority.HIGH,
        )

        result = str(prd)
        expected = "PRD: Test PRD (In Progress, High)"
        assert result == expected

    def test_prd_equality(self):
        """Test PRD equality comparison based on ID."""
        prd1 = PRD(id="PRD_123", project_id="PVT_kwDOBQfyVc0FoQ", title="PRD 1")

        prd2 = PRD(id="PRD_123", project_id="PVT_different", title="PRD 2")

        prd3 = PRD(id="PRD_456", project_id="PVT_kwDOBQfyVc0FoQ", title="PRD 3")

        assert prd1 == prd2  # Same ID
        assert prd1 != prd3  # Different ID
        assert prd1 != "not a PRD"  # Different type


class TestPRDFromGitHubItem:
    """Test cases for creating PRD from GitHub Projects v2 item data."""

    def test_from_github_item_issue(self):
        """Test creating PRD from GitHub issue item data."""
        item_data = {
            "id": "PVTI_123",
            "createdAt": "2025-01-01T00:00:00Z",
            "updatedAt": "2025-01-02T00:00:00Z",
            "position": 1,
            "archived": False,
            "content": {
                "__typename": "Issue",
                "id": "ISSUE_456",
                "title": "Feature Request PRD",
                "body": "Detailed description of the feature",
                "url": "https://github.com/user/repo/issues/1",
                "author": {"login": "creator1"},
                "assignees": {"nodes": [{"login": "assignee1"}]},
            },
            "fieldValues": {
                "nodes": [
                    {
                        "field": {"name": "Status"},
                        "name": "In Progress",
                    },
                    {
                        "field": {"name": "Priority"},
                        "name": "High",
                    },
                    {"field": {"name": "Estimation"}, "text": "3 days"},
                ]
            },
        }

        prd = PRD.from_github_item(item_data, "PVT_kwDOBQfyVc0FoQ")

        assert prd.id == "PVTI_123"
        assert prd.project_id == "PVT_kwDOBQfyVc0FoQ"
        assert prd.title == "Feature Request PRD"
        assert prd.description == "Detailed description of the feature"
        assert prd.status == PRDStatus.IN_PROGRESS
        assert prd.priority == PRDPriority.HIGH
        assert prd.creator_login == "creator1"
        assert prd.assignee_login == "assignee1"
        assert prd.content_id == "ISSUE_456"
        assert prd.content_type == "Issue"
        assert prd.content_url == "https://github.com/user/repo/issues/1"
        assert prd.custom_fields["estimation"] == "3 days"

    def test_from_github_item_draft_issue(self):
        """Test creating PRD from draft issue (no linked content)."""
        item_data = {
            "id": "PVTI_789",
            "title": "Draft PRD",
            "body": "Draft PRD content",
            "createdAt": "2025-01-01T00:00:00Z",
            "updatedAt": "2025-01-01T00:00:00Z",
            "position": 2,
            "archived": False,
            "fieldValues": {"nodes": []},
        }

        prd = PRD.from_github_item(item_data, "PVT_kwDOBQfyVc0FoQ")

        assert prd.id == "PVTI_789"
        assert prd.title == "Draft PRD"
        assert prd.description == "Draft PRD content"
        assert prd.status == PRDStatus.BACKLOG  # Default
        assert prd.priority == PRDPriority.MEDIUM  # Default
        assert prd.content_type == "DraftIssue"
        assert prd.content_id is None

    def test_from_github_item_invalid_status(self):
        """Test handling invalid status values gracefully."""
        item_data = {
            "id": "PVTI_999",
            "title": "PRD with invalid status",
            "createdAt": "2025-01-01T00:00:00Z",
            "fieldValues": {
                "nodes": [
                    {
                        "field": {"name": "Status"},
                        "name": "Invalid Status",
                    }
                ]
            },
        }

        prd = PRD.from_github_item(item_data, "PVT_kwDOBQfyVc0FoQ")

        # Should fall back to default status
        assert prd.status == PRDStatus.BACKLOG

    def test_from_github_item_invalid_priority(self):
        """Test handling invalid priority values gracefully."""
        item_data = {
            "id": "PVTI_999",
            "title": "PRD with invalid priority",
            "createdAt": "2025-01-01T00:00:00Z",
            "fieldValues": {
                "nodes": [
                    {
                        "field": {"name": "Priority"},
                        "name": "Invalid Priority",
                    }
                ]
            },
        }

        prd = PRD.from_github_item(item_data, "PVT_kwDOBQfyVc0FoQ")

        # Should fall back to default priority
        assert prd.priority == PRDPriority.MEDIUM

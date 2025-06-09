"""
Unit tests for RelationshipManager utility.

This module tests the hierarchical relationship management functionality
between PRDs, Tasks, and Subtasks in GitHub Projects v2.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass
from typing import Dict, List, Any

from github_project_manager_mcp.utils.relationship_manager import (
    RelationshipManager,
    RelationshipValidationResult,
)


class TestRelationshipValidationResult:
    """Test the RelationshipValidationResult dataclass."""

    def test_relationship_validation_result_creation(self):
        """Test creating a RelationshipValidationResult."""
        result = RelationshipValidationResult(
            is_valid=True,
            errors=[],
            warnings=["test warning"],
            metadata={"test": "data"},
        )

        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == ["test warning"]
        assert result.metadata == {"test": "data"}

    def test_relationship_validation_result_with_errors(self):
        """Test creating a RelationshipValidationResult with errors."""
        result = RelationshipValidationResult(
            is_valid=False,
            errors=["validation failed", "missing data"],
            warnings=[],
            metadata={},
        )

        assert result.is_valid is False
        assert len(result.errors) == 2
        assert "validation failed" in result.errors
        assert "missing data" in result.errors


class TestRelationshipManager:
    """Test cases for the RelationshipManager class."""

    def test_relationship_manager_initialization(self):
        """Test RelationshipManager initialization."""
        mock_client = MagicMock()
        manager = RelationshipManager(github_client=mock_client)

        assert manager.github_client == mock_client

    def test_relationship_manager_initialization_without_client(self):
        """Test RelationshipManager initialization without GitHub client."""
        manager = RelationshipManager()

        assert manager.github_client is None


class TestValidatePrdTaskRelationship:
    """Test cases for validate_prd_task_relationship method."""

    @pytest.mark.asyncio
    async def test_validate_prd_task_relationship_success(self):
        """Test successful PRD-Task relationship validation."""
        mock_client = AsyncMock()
        manager = RelationshipManager(github_client=mock_client)

        # Mock successful API response showing task belongs to PRD
        mock_task_response = {
            "node": {
                "id": "PVTI_task123",
                "content": {
                    "id": "DI_task123",
                    "title": "Test Task",
                    "body": "**Parent PRD:** PVTI_prd123\n\nTask description",
                },
            }
        }
        mock_client.query.return_value = mock_task_response

        result = await manager.validate_prd_task_relationship(
            project_id="PVT_project123",
            prd_item_id="PVTI_prd123",
            task_item_id="PVTI_task123",
        )

        # Should succeed for valid relationship
        assert result.is_valid is True
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_prd_task_relationship_missing_project_id(self):
        """Test PRD-Task validation with missing project_id."""
        manager = RelationshipManager()

        result = await manager.validate_prd_task_relationship(
            project_id="", prd_item_id="PVTI_prd123", task_item_id="PVTI_task123"
        )

        assert result.is_valid is False
        assert "Missing required parameters" in result.errors[0]

    @pytest.mark.asyncio
    async def test_validate_prd_task_relationship_missing_prd_id(self):
        """Test PRD-Task validation with missing prd_item_id."""
        manager = RelationshipManager()

        result = await manager.validate_prd_task_relationship(
            project_id="PVT_project123", prd_item_id="", task_item_id="PVTI_task123"
        )

        assert result.is_valid is False
        assert "Missing required parameters" in result.errors[0]

    @pytest.mark.asyncio
    async def test_validate_prd_task_relationship_missing_task_id(self):
        """Test PRD-Task validation with missing task_item_id."""
        manager = RelationshipManager()

        result = await manager.validate_prd_task_relationship(
            project_id="PVT_project123", prd_item_id="PVTI_prd123", task_item_id=""
        )

        assert result.is_valid is False
        assert "Missing required parameters" in result.errors[0]

    @pytest.mark.asyncio
    async def test_validate_prd_task_relationship_invalid_relationship(self):
        """Test PRD-Task validation with invalid relationship."""
        mock_client = AsyncMock()
        manager = RelationshipManager(github_client=mock_client)

        # Mock API response showing task belongs to different PRD
        mock_task_response = {
            "node": {
                "id": "PVTI_task123",
                "content": {
                    "id": "DI_task123",
                    "title": "Test Task",
                    "body": "**Parent PRD:** PVTI_different_prd\n\nTask description",
                },
            }
        }
        mock_client.query.return_value = mock_task_response

        result = await manager.validate_prd_task_relationship(
            project_id="PVT_project123",
            prd_item_id="PVTI_prd123",
            task_item_id="PVTI_task123",
        )

        # Should fail for invalid relationship
        assert result.is_valid is False
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_validate_prd_task_relationship_api_exception(self):
        """Test PRD-Task validation with API exception."""
        mock_client = AsyncMock()
        manager = RelationshipManager(github_client=mock_client)

        # Mock API exception
        mock_client.query.side_effect = Exception("GitHub API error")

        result = await manager.validate_prd_task_relationship(
            project_id="PVT_project123",
            prd_item_id="PVTI_prd123",
            task_item_id="PVTI_task123",
        )

        assert result.is_valid is False
        assert "Validation failed" in result.errors[0]


class TestValidateTaskSubtaskRelationship:
    """Test cases for validate_task_subtask_relationship method."""

    @pytest.mark.asyncio
    async def test_validate_task_subtask_relationship_success(self):
        """Test successful Task-Subtask relationship validation."""
        mock_client = AsyncMock()
        manager = RelationshipManager(github_client=mock_client)

        # Mock successful API response showing subtask belongs to task
        mock_subtask_response = {
            "node": {
                "id": "PVTI_subtask123",
                "content": {
                    "id": "DI_subtask123",
                    "title": "Test Subtask",
                    "body": "**Type:** Subtask\n**Parent Task:** PVTI_task123\n**Order:** 1\n\nSubtask description",
                },
            }
        }
        mock_client.query.return_value = mock_subtask_response

        result = await manager.validate_task_subtask_relationship(
            project_id="PVT_project123",
            task_item_id="PVTI_task123",
            subtask_item_id="PVTI_subtask123",
        )

        # Should succeed for valid relationship
        assert result.is_valid is True
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_task_subtask_relationship_missing_project_id(self):
        """Test Task-Subtask validation with missing project_id."""
        manager = RelationshipManager()

        result = await manager.validate_task_subtask_relationship(
            project_id="",
            task_item_id="PVTI_task123",
            subtask_item_id="PVTI_subtask123",
        )

        assert result.is_valid is False
        assert "Missing required parameters" in result.errors[0]

    @pytest.mark.asyncio
    async def test_validate_task_subtask_relationship_missing_task_id(self):
        """Test Task-Subtask validation with missing task_item_id."""
        manager = RelationshipManager()

        result = await manager.validate_task_subtask_relationship(
            project_id="PVT_project123",
            task_item_id="",
            subtask_item_id="PVTI_subtask123",
        )

        assert result.is_valid is False
        assert "Missing required parameters" in result.errors[0]

    @pytest.mark.asyncio
    async def test_validate_task_subtask_relationship_missing_subtask_id(self):
        """Test Task-Subtask validation with missing subtask_item_id."""
        manager = RelationshipManager()

        result = await manager.validate_task_subtask_relationship(
            project_id="PVT_project123", task_item_id="PVTI_task123", subtask_item_id=""
        )

        assert result.is_valid is False
        assert "Missing required parameters" in result.errors[0]

    @pytest.mark.asyncio
    async def test_validate_task_subtask_relationship_invalid_relationship(self):
        """Test Task-Subtask validation with invalid relationship."""
        mock_client = AsyncMock()
        manager = RelationshipManager(github_client=mock_client)

        # Mock API response showing subtask belongs to different task
        mock_subtask_response = {
            "node": {
                "id": "PVTI_subtask123",
                "content": {
                    "id": "DI_subtask123",
                    "title": "Test Subtask",
                    "body": "**Type:** Subtask\n**Parent Task:** PVTI_different_task\n**Order:** 1\n\nSubtask description",
                },
            }
        }
        mock_client.query.return_value = mock_subtask_response

        result = await manager.validate_task_subtask_relationship(
            project_id="PVT_project123",
            task_item_id="PVTI_task123",
            subtask_item_id="PVTI_subtask123",
        )

        # Should fail for invalid relationship
        assert result.is_valid is False
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_validate_task_subtask_relationship_api_exception(self):
        """Test Task-Subtask validation with API exception."""
        mock_client = AsyncMock()
        manager = RelationshipManager(github_client=mock_client)

        # Mock API exception
        mock_client.query.side_effect = Exception("GitHub API error")

        result = await manager.validate_task_subtask_relationship(
            project_id="PVT_project123",
            task_item_id="PVTI_task123",
            subtask_item_id="PVTI_subtask123",
        )

        assert result.is_valid is False
        assert "Validation failed" in result.errors[0]


class TestGetPrdChildren:
    """Test cases for get_prd_children method."""

    @pytest.mark.asyncio
    async def test_get_prd_children_success(self):
        """Test successful retrieval of PRD children (tasks)."""
        mock_client = AsyncMock()
        manager = RelationshipManager(github_client=mock_client)

        # Mock API response with tasks belonging to PRD
        mock_tasks_response = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "PVTI_task1",
                            "content": {
                                "id": "DI_task1",
                                "title": "Task 1",
                                "body": "**Parent PRD:** PVTI_prd123\n\nTask 1 description",
                            },
                        },
                        {
                            "id": "PVTI_task2",
                            "content": {
                                "id": "DI_task2",
                                "title": "Task 2",
                                "body": "**Parent PRD:** PVTI_prd123\n\nTask 2 description",
                            },
                        },
                    ]
                }
            }
        }
        mock_client.query.return_value = mock_tasks_response

        children = await manager.get_prd_children(
            project_id="PVT_project123", prd_item_id="PVTI_prd123"
        )

        # Should return list of child tasks
        assert isinstance(children, list)
        assert len(children) == 2

    @pytest.mark.asyncio
    async def test_get_prd_children_empty_result(self):
        """Test PRD children retrieval with no tasks."""
        mock_client = AsyncMock()
        manager = RelationshipManager(github_client=mock_client)

        # Mock API response with no tasks
        mock_empty_response = {"node": {"items": {"nodes": []}}}
        mock_client.query.return_value = mock_empty_response

        children = await manager.get_prd_children(
            project_id="PVT_project123", prd_item_id="PVTI_prd123"
        )

        assert isinstance(children, list)
        assert len(children) == 0

    @pytest.mark.asyncio
    async def test_get_prd_children_api_exception(self):
        """Test PRD children retrieval with API exception."""
        mock_client = AsyncMock()
        manager = RelationshipManager(github_client=mock_client)

        # Mock API exception
        mock_client.query.side_effect = Exception("GitHub API error")

        children = await manager.get_prd_children(
            project_id="PVT_project123", prd_item_id="PVTI_prd123"
        )

        # Should return empty list on error
        assert isinstance(children, list)
        assert len(children) == 0


class TestGetTaskChildren:
    """Test cases for get_task_children method."""

    @pytest.mark.asyncio
    async def test_get_task_children_success(self):
        """Test successful retrieval of Task children (subtasks)."""
        mock_client = AsyncMock()
        manager = RelationshipManager(github_client=mock_client)

        # Mock API response with subtasks belonging to task
        mock_subtasks_response = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "PVTI_subtask1",
                            "content": {
                                "id": "DI_subtask1",
                                "title": "Subtask 1",
                                "body": "**Type:** Subtask\n**Parent Task:** PVTI_task123\n**Order:** 1\n\nSubtask 1 description",
                            },
                        },
                        {
                            "id": "PVTI_subtask2",
                            "content": {
                                "id": "DI_subtask2",
                                "title": "Subtask 2",
                                "body": "**Type:** Subtask\n**Parent Task:** PVTI_task123\n**Order:** 2\n\nSubtask 2 description",
                            },
                        },
                    ]
                }
            }
        }
        mock_client.query.return_value = mock_subtasks_response

        children = await manager.get_task_children(
            project_id="PVT_project123", task_item_id="PVTI_task123"
        )

        # Should return list of child subtasks
        assert isinstance(children, list)
        assert len(children) == 2

    @pytest.mark.asyncio
    async def test_get_task_children_empty_result(self):
        """Test Task children retrieval with no subtasks."""
        mock_client = AsyncMock()
        manager = RelationshipManager(github_client=mock_client)

        # Mock API response with no subtasks
        mock_empty_response = {"node": {"items": {"nodes": []}}}
        mock_client.query.return_value = mock_empty_response

        children = await manager.get_task_children(
            project_id="PVT_project123", task_item_id="PVTI_task123"
        )

        assert isinstance(children, list)
        assert len(children) == 0

    @pytest.mark.asyncio
    async def test_get_task_children_api_exception(self):
        """Test Task children retrieval with API exception."""
        mock_client = AsyncMock()
        manager = RelationshipManager(github_client=mock_client)

        # Mock API exception
        mock_client.query.side_effect = Exception("GitHub API error")

        children = await manager.get_task_children(
            project_id="PVT_project123", task_item_id="PVTI_task123"
        )

        # Should return empty list on error
        assert isinstance(children, list)
        assert len(children) == 0


class TestValidateHierarchyConsistency:
    """Test cases for validate_hierarchy_consistency method."""

    @pytest.mark.asyncio
    async def test_validate_hierarchy_consistency_success(self):
        """Test successful hierarchy consistency validation."""
        mock_client = AsyncMock()
        manager = RelationshipManager(github_client=mock_client)

        # Mock API responses for comprehensive hierarchy check
        mock_project_response = {
            "node": {
                "items": {
                    "nodes": [
                        # PRD
                        {
                            "id": "PVTI_prd1",
                            "content": {
                                "id": "DI_prd1",
                                "title": "PRD 1",
                                "body": "PRD description",
                            },
                        },
                        # Task belonging to PRD
                        {
                            "id": "PVTI_task1",
                            "content": {
                                "id": "DI_task1",
                                "title": "Task 1",
                                "body": "**Parent PRD:** PVTI_prd1\n\nTask description",
                            },
                        },
                        # Subtask belonging to Task
                        {
                            "id": "PVTI_subtask1",
                            "content": {
                                "id": "DI_subtask1",
                                "title": "Subtask 1",
                                "body": "**Type:** Subtask\n**Parent Task:** PVTI_task1\n**Order:** 1\n\nSubtask description",
                            },
                        },
                    ]
                }
            }
        }
        mock_client.query.return_value = mock_project_response

        result = await manager.validate_hierarchy_consistency(
            project_id="PVT_project123"
        )

        # Should succeed for consistent hierarchy
        assert result.is_valid is True
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_hierarchy_consistency_orphaned_items(self):
        """Test hierarchy validation with orphaned items."""
        mock_client = AsyncMock()
        manager = RelationshipManager(github_client=mock_client)

        # Mock API response with orphaned task (no parent PRD)
        mock_project_response = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "PVTI_task1",
                            "content": {
                                "id": "DI_task1",
                                "title": "Orphaned Task",
                                "body": "Task without parent PRD",
                            },
                        }
                    ]
                }
            }
        }
        mock_client.query.return_value = mock_project_response

        result = await manager.validate_hierarchy_consistency(
            project_id="PVT_project123"
        )

        # Should fail for inconsistent hierarchy
        assert result.is_valid is False
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_validate_hierarchy_consistency_missing_parents(self):
        """Test hierarchy validation with missing parent references."""
        mock_client = AsyncMock()
        manager = RelationshipManager(github_client=mock_client)

        # Mock API response with task referencing non-existent PRD
        mock_project_response = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "PVTI_task1",
                            "content": {
                                "id": "DI_task1",
                                "title": "Task 1",
                                "body": "**Parent PRD:** PVTI_nonexistent_prd\n\nTask description",
                            },
                        }
                    ]
                }
            }
        }
        mock_client.query.return_value = mock_project_response

        result = await manager.validate_hierarchy_consistency(
            project_id="PVT_project123"
        )

        # Should fail for missing parent references
        assert result.is_valid is False
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_validate_hierarchy_consistency_api_exception(self):
        """Test hierarchy validation with API exception."""
        mock_client = AsyncMock()
        manager = RelationshipManager(github_client=mock_client)

        # Mock API exception
        mock_client.query.side_effect = Exception("GitHub API error")

        result = await manager.validate_hierarchy_consistency(
            project_id="PVT_project123"
        )

        assert result.is_valid is False
        assert "Hierarchy validation failed" in result.errors[0]

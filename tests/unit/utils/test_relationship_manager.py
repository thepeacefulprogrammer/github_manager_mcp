"""
Unit tests for RelationshipManager utility.

This module tests the hierarchical relationship management functionality
between PRDs, Tasks, and Subtasks in GitHub Projects v2.
"""

from dataclasses import dataclass
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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


class TestCascadeCompletion:
    """Test cases for cascade completion logic."""

    @pytest.mark.asyncio
    async def test_check_and_complete_parent_task_success(self):
        """Test successful cascade completion of task when all subtasks are complete."""
        mock_client = AsyncMock()
        manager = RelationshipManager(github_client=mock_client)

        # Mock task field values response (showing task is not yet complete) - FIRST CALL
        mock_task_fields_response = {
            "node": {
                "id": "PVTI_task123",
                "project": {
                    "id": "PVT_project123",
                    "fields": {
                        "nodes": [
                            {
                                "id": "FIELD_STATUS_ID",
                                "name": "Status",
                                "dataType": "SINGLE_SELECT",
                            }
                        ]
                    },
                },
                "fieldValues": {
                    "nodes": [
                        {
                            "field": {"id": "FIELD_STATUS_ID", "name": "Status"},
                            "value": "In Progress",
                        }
                    ]
                },
            }
        }

        # Mock the main project items query that get_task_children uses - SECOND CALL
        mock_project_response = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "PVTI_subtask1",
                            "content": {
                                "id": "DI_subtask1",
                                "title": "Subtask 1",
                                "body": "**Type:** Subtask\n**Parent Task:** PVTI_task123\n**Order:** 1\n**Status:** Complete\n\nSubtask 1 description",
                            },
                        },
                        {
                            "id": "PVTI_subtask2",
                            "content": {
                                "id": "DI_subtask2",
                                "title": "Subtask 2",
                                "body": "**Type:** Subtask\n**Parent Task:** PVTI_task123\n**Order:** 2\n**Status:** Complete\n\nSubtask 2 description",
                            },
                        },
                    ]
                }
            }
        }

        # Mock successful task completion response
        mock_task_update_response = {
            "updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "PVTI_task123"}}
        }

        mock_client.query.side_effect = [
            mock_task_fields_response,  # First call: get task status
            mock_project_response,  # Second call: get_task_children query for project items
        ]
        mock_client.mutate.return_value = mock_task_update_response

        result = await manager.check_and_complete_parent_task(
            project_id="PVT_project123", task_item_id="PVTI_task123"
        )

        # Should complete the task since all subtasks are complete
        assert result.is_valid is True
        assert "completed automatically" in result.metadata.get("action", "").lower()
        assert mock_client.mutate.called  # Task completion mutation should be called

    @pytest.mark.asyncio
    async def test_check_and_complete_parent_task_incomplete_children(self):
        """Test that task is not completed when some subtasks are incomplete."""
        mock_client = AsyncMock()
        manager = RelationshipManager(github_client=mock_client)

        # Mock subtasks with mixed completion status
        mock_subtasks_response = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "PVTI_subtask1",
                            "content": {
                                "id": "DI_subtask1",
                                "title": "Subtask 1",
                                "body": "**Type:** Subtask\n**Parent Task:** PVTI_task123\n**Order:** 1\n**Status:** Complete\n\nSubtask 1 description",
                            },
                        },
                        {
                            "id": "PVTI_subtask2",
                            "content": {
                                "id": "DI_subtask2",
                                "title": "Subtask 2",
                                "body": "**Type:** Subtask\n**Parent Task:** PVTI_task123\n**Order:** 2\n**Status:** Incomplete\n\nSubtask 2 description",
                            },
                        },
                    ]
                }
            }
        }

        mock_client.query.return_value = mock_subtasks_response

        result = await manager.check_and_complete_parent_task(
            project_id="PVT_project123", task_item_id="PVTI_task123"
        )

        # Should not complete the task since not all subtasks are complete
        assert result.is_valid is True
        assert "not all children complete" in result.metadata.get("reason", "").lower()
        assert not mock_client.mutate.called  # No completion mutation should be called

    @pytest.mark.asyncio
    async def test_check_and_complete_parent_task_already_complete(self):
        """Test that already complete task is not processed again."""
        mock_client = AsyncMock()
        manager = RelationshipManager(github_client=mock_client)

        # Mock task field values showing task is already complete
        mock_task_fields_response = {
            "node": {
                "id": "PVTI_task123",
                "project": {
                    "id": "PVT_project123",
                    "fields": {
                        "nodes": [
                            {
                                "id": "FIELD_STATUS_ID",
                                "name": "Status",
                                "dataType": "SINGLE_SELECT",
                            }
                        ]
                    },
                },
                "fieldValues": {
                    "nodes": [
                        {
                            "field": {"id": "FIELD_STATUS_ID", "name": "Status"},
                            "value": "Done",
                        }
                    ]
                },
            }
        }

        mock_client.query.return_value = mock_task_fields_response

        result = await manager.check_and_complete_parent_task(
            project_id="PVT_project123", task_item_id="PVTI_task123"
        )

        # Should return success but no action needed
        assert result.is_valid is True
        assert "already complete" in result.metadata.get("reason", "").lower()
        assert not mock_client.mutate.called

    @pytest.mark.asyncio
    async def test_check_and_complete_parent_prd_success(self):
        """Test successful cascade completion of PRD when all tasks are complete."""
        mock_client = AsyncMock()
        manager = RelationshipManager(github_client=mock_client)

        # Mock PRD field values response (showing PRD is not yet complete) - FIRST CALL
        mock_prd_fields_response = {
            "node": {
                "id": "PVTI_prd123",
                "project": {
                    "id": "PVT_project123",
                    "fields": {
                        "nodes": [
                            {
                                "id": "FIELD_STATUS_ID",
                                "name": "Status",
                                "dataType": "SINGLE_SELECT",
                            }
                        ]
                    },
                },
                "fieldValues": {
                    "nodes": [
                        {
                            "field": {"id": "FIELD_STATUS_ID", "name": "Status"},
                            "value": "In Progress",
                        }
                    ]
                },
            }
        }

        # Mock the main project items query that get_prd_children uses - SECOND CALL
        mock_project_response = {
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

        # Mock the task completion status query for checking if all tasks are complete - THIRD CALL
        mock_tasks_status_response = {
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
                            "fieldValues": {
                                "nodes": [
                                    {"field": {"name": "Status"}, "value": "Done"}
                                ]
                            },
                        },
                        {
                            "id": "PVTI_task2",
                            "content": {
                                "id": "DI_task2",
                                "title": "Task 2",
                                "body": "**Parent PRD:** PVTI_prd123\n\nTask 2 description",
                            },
                            "fieldValues": {
                                "nodes": [
                                    {"field": {"name": "Status"}, "value": "Done"}
                                ]
                            },
                        },
                    ]
                }
            }
        }

        # Mock successful PRD completion response
        mock_prd_update_response = {
            "updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "PVTI_prd123"}}
        }

        # Mock the project response with tasks that have field values showing completion status
        mock_project_with_status_response = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "PVTI_task1",
                            "content": {
                                "id": "DI_task1",
                                "title": "Task 1",
                                "body": "**Parent PRD:** PVTI_prd123\n**Status:** Done\n\nTask 1 description",
                            },
                            "fieldValues": {
                                "nodes": [
                                    {"field": {"name": "Status"}, "value": "Done"}
                                ]
                            },
                        },
                        {
                            "id": "PVTI_task2",
                            "content": {
                                "id": "DI_task2",
                                "title": "Task 2",
                                "body": "**Parent PRD:** PVTI_prd123\n**Status:** Done\n\nTask 2 description",
                            },
                            "fieldValues": {
                                "nodes": [
                                    {"field": {"name": "Status"}, "value": "Done"}
                                ]
                            },
                        },
                    ]
                }
            }
        }
        mock_client.query.return_value = mock_project_with_status_response
        mock_client.mutate.return_value = mock_prd_update_response

        result = await manager.check_and_complete_parent_prd(
            project_id="PVT_project123", prd_item_id="PVTI_prd123"
        )

        # Should complete the PRD since all tasks are complete
        assert result.is_valid is True
        assert "completed automatically" in result.metadata.get("action", "").lower()
        assert mock_client.mutate.called  # PRD completion mutation should be called

    @pytest.mark.asyncio
    async def test_check_and_complete_parent_prd_incomplete_children(self):
        """Test that PRD is not completed when some tasks are incomplete."""
        mock_client = AsyncMock()
        manager = RelationshipManager(github_client=mock_client)

        # Mock tasks with mixed completion status
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
                            "fieldValues": {
                                "nodes": [
                                    {"field": {"name": "Status"}, "value": "Done"}
                                ]
                            },
                        },
                        {
                            "id": "PVTI_task2",
                            "content": {
                                "id": "DI_task2",
                                "title": "Task 2",
                                "body": "**Parent PRD:** PVTI_prd123\n\nTask 2 description",
                            },
                            "fieldValues": {
                                "nodes": [
                                    {
                                        "field": {"name": "Status"},
                                        "value": "In Progress",
                                    }
                                ]
                            },
                        },
                    ]
                }
            }
        }

        mock_client.query.return_value = mock_tasks_response

        result = await manager.check_and_complete_parent_prd(
            project_id="PVT_project123", prd_item_id="PVTI_prd123"
        )

        # Should not complete the PRD since not all tasks are complete
        assert result.is_valid is True
        assert "not all children complete" in result.metadata.get("reason", "").lower()
        assert not mock_client.mutate.called  # No completion mutation should be called

    @pytest.mark.asyncio
    async def test_cascade_completion_full_hierarchy(self):
        """Test full cascade completion from subtask to task to PRD."""
        mock_client = AsyncMock()
        manager = RelationshipManager(github_client=mock_client)

        # Mock the subtask query to get parent task ID
        mock_subtask_response = {
            "node": {
                "content": {
                    "body": "**Type:** Subtask\n**Parent Task:** PVTI_task123\n**Order:** 1\n**Status:** Complete\n\nSubtask description"
                }
            }
        }

        # Mock the task query to get parent PRD ID
        mock_task_response = {
            "node": {
                "content": {"body": "**Parent PRD:** PVTI_prd123\n\nTask description"}
            }
        }

        # Mock successful mutations
        mock_mutation_response = {
            "updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "PVTI_updated"}}
        }

        mock_client.query.side_effect = [
            mock_subtask_response,  # First call: get subtask to find parent task
            mock_task_response,  # Second call: get task to find parent PRD
        ]
        mock_client.mutate.return_value = mock_mutation_response

        result = await manager.cascade_completion_check(
            project_id="PVT_project123",
            completed_item_id="PVTI_subtask1",
            item_type="subtask",
        )

        # Should successfully process the cascade
        assert result.is_valid is True
        assert "cascade" in result.metadata.get("action", "").lower()
        assert (
            len(result.metadata.get("cascade_actions", [])) >= 1
        )  # At least one cascade action should occur

    @pytest.mark.asyncio
    async def test_cascade_completion_error_handling(self):
        """Test error handling in cascade completion logic."""
        mock_client = AsyncMock()
        manager = RelationshipManager(github_client=mock_client)

        # Mock API exception
        mock_client.query.side_effect = Exception("GitHub API error")

        result = await manager.cascade_completion_check(
            project_id="PVT_project123",
            completed_item_id="PVTI_subtask1",
            item_type="subtask",
        )

        assert result.is_valid is False
        assert "cascade completion failed" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_cascade_completion_invalid_item_type(self):
        """Test cascade completion with invalid item type."""
        manager = RelationshipManager()

        result = await manager.cascade_completion_check(
            project_id="PVT_project123",
            completed_item_id="PVTI_invalid",
            item_type="invalid_type",
        )

        assert result.is_valid is False
        assert "invalid item type" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_get_completion_status_from_body(self):
        """Test extraction of completion status from item body content."""
        manager = RelationshipManager()

        # Test complete status
        complete_body = (
            "**Type:** Subtask\n**Status:** Complete\n**Order:** 1\n\nDescription"
        )
        assert manager._get_completion_status_from_body(complete_body) == "Complete"

        # Test incomplete status
        incomplete_body = (
            "**Type:** Subtask\n**Status:** Incomplete\n**Order:** 1\n\nDescription"
        )
        assert manager._get_completion_status_from_body(incomplete_body) == "Incomplete"

        # Test done status
        done_body = "**Type:** Task\n**Status:** Done\n\nDescription"
        assert manager._get_completion_status_from_body(done_body) == "Done"

        # Test no status
        no_status_body = "**Type:** Task\n\nDescription without status"
        assert manager._get_completion_status_from_body(no_status_body) is None

    @pytest.mark.asyncio
    async def test_is_item_complete_with_field_values(self):
        """Test completion status checking with field values."""
        manager = RelationshipManager()

        # Test with field values indicating completion
        complete_item = {
            "fieldValues": {"nodes": [{"field": {"name": "Status"}, "value": "Done"}]}
        }
        assert manager._is_item_complete(complete_item) is True

        # Test with field values indicating incomplete
        incomplete_item = {
            "fieldValues": {
                "nodes": [{"field": {"name": "Status"}, "value": "In Progress"}]
            }
        }
        assert manager._is_item_complete(incomplete_item) is False

        # Test with no field values but complete body content
        body_complete_item = {
            "content": {"body": "**Status:** Complete\n\nDescription"}
        }
        assert manager._is_item_complete(body_complete_item) is True

    @pytest.mark.asyncio
    async def test_is_item_complete_edge_cases(self):
        """Test completion status checking edge cases."""
        manager = RelationshipManager()

        # Test with empty item
        assert manager._is_item_complete({}) is False

        # Test with None item
        assert manager._is_item_complete(None) is False

        # Test with item missing content and field values
        minimal_item = {"id": "PVTI_test"}
        assert manager._is_item_complete(minimal_item) is False


class TestStatusSynchronizationAndProgress:
    """Test status synchronization and progress tracking functionality."""

    @pytest.fixture
    def mock_github_client(self):
        """Create a mock GitHub client."""
        return AsyncMock()

    @pytest.fixture
    def relationship_manager(self, mock_github_client):
        """Create a RelationshipManager instance with mock client."""
        return RelationshipManager(github_client=mock_github_client)

    @pytest.mark.asyncio
    async def test_calculate_prd_progress_success(
        self, relationship_manager, mock_github_client
    ):
        """Test successful PRD progress calculation."""
        # Mock response for getting PRD children (tasks) - need to mock the project query structure
        mock_github_client.query.return_value = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "TASK_1",
                            "content": {
                                "id": "CONTENT_1",
                                "title": "Task 1",
                                "body": "**Parent PRD:** PRD_123",
                            },
                            "fieldValues": {
                                "nodes": [{"field": {"name": "Status"}, "name": "Done"}]
                            },
                        },
                        {
                            "id": "TASK_2",
                            "content": {
                                "id": "CONTENT_2",
                                "title": "Task 2",
                                "body": "**Parent PRD:** PRD_123",
                            },
                            "fieldValues": {
                                "nodes": [
                                    {"field": {"name": "Status"}, "name": "In Progress"}
                                ]
                            },
                        },
                        {
                            "id": "TASK_3",
                            "content": {
                                "id": "CONTENT_3",
                                "title": "Task 3",
                                "body": "**Parent PRD:** PRD_123",
                            },
                            "fieldValues": {
                                "nodes": [{"field": {"name": "Status"}, "name": "Done"}]
                            },
                        },
                        {
                            "id": "OTHER_TASK",
                            "content": {
                                "id": "CONTENT_OTHER",
                                "title": "Other Task",
                                "body": "**Parent PRD:** OTHER_PRD",
                            },
                        },
                    ]
                }
            }
        }

        result = await relationship_manager.calculate_prd_progress(
            "PROJECT_123", "PRD_123"
        )

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.metadata["total_tasks"] == 3
        assert result.metadata["completed_tasks"] == 2
        assert result.metadata["progress_percentage"] == 66.67
        assert result.metadata["status"] == "In Progress"

    @pytest.mark.asyncio
    async def test_calculate_prd_progress_all_complete(
        self, relationship_manager, mock_github_client
    ):
        """Test PRD progress calculation when all tasks are complete."""
        # Mock response for getting PRD children (all tasks complete)
        mock_github_client.query.return_value = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "TASK_1",
                            "content": {
                                "id": "CONTENT_1",
                                "title": "Task 1",
                                "body": "**Parent PRD:** PRD_123",
                            },
                            "fieldValues": {
                                "nodes": [{"field": {"name": "Status"}, "name": "Done"}]
                            },
                        },
                        {
                            "id": "TASK_2",
                            "content": {
                                "id": "CONTENT_2",
                                "title": "Task 2",
                                "body": "**Parent PRD:** PRD_123",
                            },
                            "fieldValues": {
                                "nodes": [{"field": {"name": "Status"}, "name": "Done"}]
                            },
                        },
                    ]
                }
            }
        }

        result = await relationship_manager.calculate_prd_progress(
            "PROJECT_123", "PRD_123"
        )

        assert result.is_valid is True
        assert result.metadata["total_tasks"] == 2
        assert result.metadata["completed_tasks"] == 2
        assert result.metadata["progress_percentage"] == 100.0
        assert result.metadata["status"] == "Complete"

    @pytest.mark.asyncio
    async def test_calculate_prd_progress_no_tasks(
        self, relationship_manager, mock_github_client
    ):
        """Test PRD progress calculation when no tasks exist."""
        # Mock response for getting PRD children (no tasks)
        mock_github_client.query.return_value = {"node": {"items": {"nodes": []}}}

        result = await relationship_manager.calculate_prd_progress(
            "PROJECT_123", "PRD_123"
        )

        assert result.is_valid is True
        assert result.metadata["total_tasks"] == 0
        assert result.metadata["completed_tasks"] == 0
        assert result.metadata["progress_percentage"] == 0.0
        assert result.metadata["status"] == "Not Started"

    @pytest.mark.asyncio
    async def test_calculate_task_progress_success(
        self, relationship_manager, mock_github_client
    ):
        """Test successful task progress calculation."""
        # Mock response for getting task children (subtasks)
        mock_github_client.query.return_value = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "SUBTASK_1",
                            "content": {
                                "id": "CONTENT_1",
                                "title": "Subtask 1",
                                "body": "**Type:** Subtask\n**Parent Task:** TASK_123\n**Status:** Complete\n**Order:** 1",
                            },
                        },
                        {
                            "id": "SUBTASK_2",
                            "content": {
                                "id": "CONTENT_2",
                                "title": "Subtask 2",
                                "body": "**Type:** Subtask\n**Parent Task:** TASK_123\n**Status:** Incomplete\n**Order:** 2",
                            },
                        },
                        {
                            "id": "SUBTASK_3",
                            "content": {
                                "id": "CONTENT_3",
                                "title": "Subtask 3",
                                "body": "**Type:** Subtask\n**Parent Task:** TASK_123\n**Status:** Complete\n**Order:** 3",
                            },
                        },
                        {
                            "id": "OTHER_SUBTASK",
                            "content": {
                                "id": "CONTENT_OTHER",
                                "title": "Other Subtask",
                                "body": "**Type:** Subtask\n**Parent Task:** OTHER_TASK\n**Status:** Complete",
                            },
                        },
                    ]
                }
            }
        }

        result = await relationship_manager.calculate_task_progress(
            "PROJECT_123", "TASK_123"
        )

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.metadata["total_subtasks"] == 3
        assert result.metadata["completed_subtasks"] == 2
        assert result.metadata["progress_percentage"] == 66.67
        assert result.metadata["status"] == "In Progress"

    @pytest.mark.asyncio
    async def test_calculate_task_progress_all_complete(
        self, relationship_manager, mock_github_client
    ):
        """Test task progress calculation when all subtasks are complete."""
        # Mock response for getting task children (all subtasks complete)
        mock_github_client.query.return_value = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "SUBTASK_1",
                            "content": {
                                "id": "CONTENT_1",
                                "title": "Subtask 1",
                                "body": "**Type:** Subtask\n**Parent Task:** TASK_123\n**Status:** Complete\n**Order:** 1",
                            },
                        },
                        {
                            "id": "SUBTASK_2",
                            "content": {
                                "id": "CONTENT_2",
                                "title": "Subtask 2",
                                "body": "**Type:** Subtask\n**Parent Task:** TASK_123\n**Status:** Complete\n**Order:** 2",
                            },
                        },
                    ]
                }
            }
        }

        result = await relationship_manager.calculate_task_progress(
            "PROJECT_123", "TASK_123"
        )

        assert result.is_valid is True
        assert result.metadata["total_subtasks"] == 2
        assert result.metadata["completed_subtasks"] == 2
        assert result.metadata["progress_percentage"] == 100.0
        assert result.metadata["status"] == "Complete"

    @pytest.mark.asyncio
    async def test_calculate_task_progress_no_subtasks(
        self, relationship_manager, mock_github_client
    ):
        """Test task progress calculation when no subtasks exist."""
        # Mock response for getting task children (no subtasks)
        mock_github_client.query.return_value = {"node": {"items": {"nodes": []}}}

        result = await relationship_manager.calculate_task_progress(
            "PROJECT_123", "TASK_123"
        )

        assert result.is_valid is True
        assert result.metadata["total_subtasks"] == 0
        assert result.metadata["completed_subtasks"] == 0
        assert result.metadata["progress_percentage"] == 0.0
        assert result.metadata["status"] == "Not Started"

    @pytest.mark.asyncio
    async def test_calculate_progress_api_error(
        self, relationship_manager, mock_github_client
    ):
        """Test progress calculation with API error."""
        mock_github_client.query.side_effect = Exception("API Error")

        result = await relationship_manager.calculate_prd_progress(
            "PROJECT_123", "PRD_123"
        )

        assert result.is_valid is False  # The method properly propagates API errors
        assert "Progress calculation failed: API Error" in result.errors[0]

    @pytest.mark.asyncio
    async def test_synchronize_hierarchy_status_success(
        self, relationship_manager, mock_github_client
    ):
        """Test successful hierarchy status synchronization."""
        # Mock responses for getting hierarchy data - need to handle multiple calls
        mock_github_client.query.side_effect = [
            # First call: Get all project items for synchronization
            {
                "node": {
                    "items": {
                        "nodes": [
                            {
                                "id": "PRD_1",
                                "fieldValues": {
                                    "nodes": [
                                        {
                                            "field": {"name": "Status"},
                                            "name": "In Progress",
                                        }
                                    ]
                                },
                                "content": {
                                    "id": "CONTENT_PRD1",
                                    "title": "PRD 1",
                                    "body": "**Type:** PRD",
                                },
                            },
                            {
                                "id": "TASK_1",
                                "fieldValues": {
                                    "nodes": [
                                        {"field": {"name": "Status"}, "name": "Done"}
                                    ]
                                },
                                "content": {
                                    "id": "CONTENT_TASK1",
                                    "title": "Task 1",
                                    "body": "**Parent PRD:** PRD_1",
                                },
                            },
                        ]
                    }
                }
            },
            # Second call: Get tasks for PRD_1 progress calculation
            {
                "node": {
                    "items": {
                        "nodes": [
                            {
                                "id": "TASK_1",
                                "content": {
                                    "id": "CONTENT_TASK1",
                                    "title": "Task 1",
                                    "body": "**Parent PRD:** PRD_1",
                                },
                                "fieldValues": {
                                    "nodes": [
                                        {"field": {"name": "Status"}, "name": "Done"}
                                    ]
                                },
                            }
                        ]
                    }
                }
            },
            # Third call: Get subtasks for TASK_1 progress calculation
            {
                "node": {
                    "items": {
                        "nodes": [
                            {
                                "id": "SUBTASK_1",
                                "content": {
                                    "id": "CONTENT_SUB1",
                                    "title": "Subtask 1",
                                    "body": "**Type:** Subtask\n**Parent Task:** TASK_1\n**Status:** Complete",
                                },
                            }
                        ]
                    }
                }
            },
        ]

        result = await relationship_manager.synchronize_hierarchy_status("PROJECT_123")

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert "synchronization_summary" in result.metadata
        assert "prds_processed" in result.metadata
        assert "tasks_processed" in result.metadata

    @pytest.mark.asyncio
    async def test_get_project_completion_statistics_success(
        self, relationship_manager, mock_github_client
    ):
        """Test successful project completion statistics calculation."""
        # Mock response for getting all project items
        mock_github_client.query.return_value = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "PRD_1",
                            "fieldValues": {
                                "nodes": [{"field": {"name": "Status"}, "name": "Done"}]
                            },
                            "content": {
                                "id": "CONTENT_PRD1",
                                "title": "PRD 1",
                                "body": "**Type:** PRD",
                            },
                        },
                        {
                            "id": "PRD_2",
                            "fieldValues": {
                                "nodes": [
                                    {"field": {"name": "Status"}, "name": "In Progress"}
                                ]
                            },
                            "content": {
                                "id": "CONTENT_PRD2",
                                "title": "PRD 2",
                                "body": "**Type:** PRD",
                            },
                        },
                        {
                            "id": "TASK_1",
                            "fieldValues": {
                                "nodes": [{"field": {"name": "Status"}, "name": "Done"}]
                            },
                            "content": {
                                "id": "CONTENT_TASK1",
                                "title": "Task 1",
                                "body": "**Parent PRD:** PRD_1",
                            },
                        },
                        {
                            "id": "TASK_2",
                            "fieldValues": {
                                "nodes": [
                                    {"field": {"name": "Status"}, "name": "Backlog"}
                                ]
                            },
                            "content": {
                                "id": "CONTENT_TASK2",
                                "title": "Task 2",
                                "body": "**Parent PRD:** PRD_2",
                            },
                        },
                        {
                            "id": "SUBTASK_1",
                            "content": {
                                "id": "CONTENT_SUB1",
                                "title": "Subtask 1",
                                "body": "**Type:** Subtask\n**Parent Task:** TASK_1\n**Status:** Complete",
                            },
                        },
                        {
                            "id": "SUBTASK_2",
                            "content": {
                                "id": "CONTENT_SUB2",
                                "title": "Subtask 2",
                                "body": "**Type:** Subtask\n**Parent Task:** TASK_2\n**Status:** Incomplete",
                            },
                        },
                    ]
                }
            }
        }

        result = await relationship_manager.get_project_completion_statistics(
            "PROJECT_123"
        )

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.metadata["total_prds"] == 2
        assert result.metadata["completed_prds"] == 1
        assert result.metadata["total_tasks"] == 2
        assert result.metadata["completed_tasks"] == 1
        assert result.metadata["total_subtasks"] == 2
        assert result.metadata["completed_subtasks"] == 1
        assert result.metadata["overall_progress_percentage"] == 50.0

    @pytest.mark.asyncio
    async def test_calculate_progress_missing_parameters(self, relationship_manager):
        """Test progress calculation with missing parameters."""
        result = await relationship_manager.calculate_prd_progress("", "PRD_123")

        assert result.is_valid is False
        assert "Missing required parameters" in result.errors[0]

    @pytest.mark.asyncio
    async def test_calculate_progress_no_github_client(self):
        """Test progress calculation without GitHub client."""
        manager = RelationshipManager(github_client=None)
        result = await manager.calculate_prd_progress("PROJECT_123", "PRD_123")

        assert result.is_valid is False
        assert "GitHub client not initialized" in result.errors[0]

    @pytest.mark.asyncio
    async def test_synchronize_status_missing_parameters(self, relationship_manager):
        """Test status synchronization with missing parameters."""
        result = await relationship_manager.synchronize_hierarchy_status("")

        assert result.is_valid is False
        assert "Missing required parameters" in result.errors[0]

    @pytest.mark.asyncio
    async def test_synchronize_status_no_github_client(self):
        """Test status synchronization without GitHub client."""
        manager = RelationshipManager(github_client=None)
        result = await manager.synchronize_hierarchy_status("PROJECT_123")

        assert result.is_valid is False
        assert "GitHub client not initialized" in result.errors[0]

    @pytest.mark.asyncio
    async def test_synchronize_status_api_error(
        self, relationship_manager, mock_github_client
    ):
        """Test status synchronization with API error."""
        mock_github_client.query.side_effect = Exception("API Error")

        result = await relationship_manager.synchronize_hierarchy_status("PROJECT_123")

        assert result.is_valid is False
        assert "Status synchronization failed" in result.errors[0]

    @pytest.mark.asyncio
    async def test_statistics_missing_parameters(self, relationship_manager):
        """Test statistics calculation with missing parameters."""
        result = await relationship_manager.get_project_completion_statistics("")

        assert result.is_valid is False
        assert "Missing required parameters" in result.errors[0]

    @pytest.mark.asyncio
    async def test_statistics_no_github_client(self):
        """Test statistics calculation without GitHub client."""
        manager = RelationshipManager(github_client=None)
        result = await manager.get_project_completion_statistics("PROJECT_123")

        assert result.is_valid is False
        assert "GitHub client not initialized" in result.errors[0]

    @pytest.mark.asyncio
    async def test_statistics_api_error(self, relationship_manager, mock_github_client):
        """Test statistics calculation with API error."""
        mock_github_client.query.side_effect = Exception("API Error")

        result = await relationship_manager.get_project_completion_statistics(
            "PROJECT_123"
        )

        assert result.is_valid is False
        assert "Statistics calculation failed" in result.errors[0]


class TestEnhancedRelationshipQuerying:
    """Test enhanced relationship querying and filtering capabilities."""

    @pytest.fixture
    def mock_github_client(self):
        """Create a mock GitHub client."""
        return AsyncMock()

    @pytest.fixture
    def relationship_manager(self, mock_github_client):
        """Create a RelationshipManager instance with mock client."""
        return RelationshipManager(github_client=mock_github_client)

    @pytest.mark.asyncio
    async def test_query_items_by_status_success(
        self, relationship_manager, mock_github_client
    ):
        """Test successful querying of items by status."""
        # Mock response for querying items by status
        mock_github_client.query.return_value = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "ITEM_1",
                            "fieldValues": {
                                "nodes": [{"field": {"name": "Status"}, "name": "Done"}]
                            },
                            "content": {
                                "id": "CONTENT_1",
                                "title": "Item 1",
                                "body": "**Type:** PRD",
                            },
                        },
                        {
                            "id": "ITEM_2",
                            "fieldValues": {
                                "nodes": [{"field": {"name": "Status"}, "name": "Done"}]
                            },
                            "content": {
                                "id": "CONTENT_2",
                                "title": "Item 2",
                                "body": "**Parent PRD:** PRD_123",
                            },
                        },
                    ]
                }
            }
        }

        result = await relationship_manager.query_items_by_status("PROJECT_123", "Done")

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.metadata["items"]) == 2
        assert result.metadata["status_filter"] == "Done"
        assert result.metadata["total_count"] == 2

    @pytest.mark.asyncio
    async def test_query_items_by_type_success(
        self, relationship_manager, mock_github_client
    ):
        """Test successful querying of items by type."""
        # Mock response for querying items by type
        mock_github_client.query.return_value = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "PRD_1",
                            "fieldValues": {
                                "nodes": [
                                    {"field": {"name": "Status"}, "name": "In Progress"}
                                ]
                            },
                            "content": {
                                "id": "CONTENT_1",
                                "title": "PRD 1",
                                "body": "**Type:** PRD",
                            },
                        },
                        {
                            "id": "PRD_2",
                            "fieldValues": {
                                "nodes": [{"field": {"name": "Status"}, "name": "Done"}]
                            },
                            "content": {
                                "id": "CONTENT_2",
                                "title": "PRD 2",
                                "body": "**Type:** PRD",
                            },
                        },
                        {
                            "id": "TASK_1",
                            "fieldValues": {
                                "nodes": [{"field": {"name": "Status"}, "name": "Done"}]
                            },
                            "content": {
                                "id": "CONTENT_3",
                                "title": "Task 1",
                                "body": "**Parent PRD:** PRD_1",
                            },
                        },
                    ]
                }
            }
        }

        result = await relationship_manager.query_items_by_type("PROJECT_123", "PRD")

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.metadata["items"]) == 2
        assert result.metadata["item_type"] == "PRD"
        assert result.metadata["total_count"] == 2

    @pytest.mark.asyncio
    async def test_search_items_by_title_success(
        self, relationship_manager, mock_github_client
    ):
        """Test successful searching of items by title."""
        # Mock response for searching items by title
        mock_github_client.query.return_value = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "ITEM_1",
                            "fieldValues": {
                                "nodes": [{"field": {"name": "Status"}, "name": "Done"}]
                            },
                            "content": {
                                "id": "CONTENT_1",
                                "title": "User Authentication Feature",
                                "body": "**Type:** PRD",
                            },
                        },
                        {
                            "id": "ITEM_2",
                            "fieldValues": {
                                "nodes": [
                                    {"field": {"name": "Status"}, "name": "In Progress"}
                                ]
                            },
                            "content": {
                                "id": "CONTENT_2",
                                "title": "User Profile Management",
                                "body": "**Parent PRD:** PRD_123",
                            },
                        },
                    ]
                }
            }
        }

        result = await relationship_manager.search_items_by_title("PROJECT_123", "User")

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.metadata["items"]) == 2
        assert result.metadata["search_query"] == "User"
        assert result.metadata["total_count"] == 2

    @pytest.mark.asyncio
    async def test_get_orphaned_items_success(
        self, relationship_manager, mock_github_client
    ):
        """Test successful detection of orphaned items."""
        # Mock response for getting orphaned items
        mock_github_client.query.return_value = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "TASK_1",
                            "fieldValues": {
                                "nodes": [{"field": {"name": "Status"}, "name": "Done"}]
                            },
                            "content": {
                                "id": "CONTENT_1",
                                "title": "Orphaned Task",
                                "body": "**Parent PRD:** MISSING_PRD",
                            },
                        },
                        {
                            "id": "SUBTASK_1",
                            "content": {
                                "id": "CONTENT_2",
                                "title": "Orphaned Subtask",
                                "body": "**Type:** Subtask\n**Parent Task:** MISSING_TASK\n**Status:** Complete",
                            },
                        },
                        {
                            "id": "PRD_1",
                            "fieldValues": {
                                "nodes": [{"field": {"name": "Status"}, "name": "Done"}]
                            },
                            "content": {
                                "id": "CONTENT_3",
                                "title": "Valid PRD",
                                "body": "**Type:** PRD",
                            },
                        },
                    ]
                }
            }
        }

        result = await relationship_manager.get_orphaned_items("PROJECT_123")

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.metadata["orphaned_items"]) == 2
        assert result.metadata["total_orphaned"] == 2

    @pytest.mark.asyncio
    async def test_get_items_by_priority_success(
        self, relationship_manager, mock_github_client
    ):
        """Test successful querying of items by priority."""
        # Mock response for querying items by priority
        mock_github_client.query.return_value = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "ITEM_1",
                            "fieldValues": {
                                "nodes": [
                                    {"field": {"name": "Status"}, "name": "Done"},
                                    {"field": {"name": "Priority"}, "name": "High"},
                                ]
                            },
                            "content": {
                                "id": "CONTENT_1",
                                "title": "High Priority Item",
                                "body": "**Type:** PRD",
                            },
                        },
                        {
                            "id": "ITEM_2",
                            "fieldValues": {
                                "nodes": [
                                    {
                                        "field": {"name": "Status"},
                                        "name": "In Progress",
                                    },
                                    {"field": {"name": "Priority"}, "name": "High"},
                                ]
                            },
                            "content": {
                                "id": "CONTENT_2",
                                "title": "Another High Priority",
                                "body": "**Parent PRD:** PRD_123",
                            },
                        },
                    ]
                }
            }
        }

        result = await relationship_manager.get_items_by_priority("PROJECT_123", "High")

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.metadata["items"]) == 2
        assert result.metadata["priority_filter"] == "High"
        assert result.metadata["total_count"] == 2

    @pytest.mark.asyncio
    async def test_get_hierarchy_tree_success(
        self, relationship_manager, mock_github_client
    ):
        """Test successful retrieval of complete hierarchy tree."""
        # Mock responses for building hierarchy tree
        mock_github_client.query.side_effect = [
            # First call: Get all project items
            {
                "node": {
                    "items": {
                        "nodes": [
                            {
                                "id": "PRD_1",
                                "fieldValues": {
                                    "nodes": [
                                        {
                                            "field": {"name": "Status"},
                                            "name": "In Progress",
                                        }
                                    ]
                                },
                                "content": {
                                    "id": "CONTENT_PRD1",
                                    "title": "PRD 1",
                                    "body": "**Type:** PRD",
                                },
                            },
                            {
                                "id": "TASK_1",
                                "fieldValues": {
                                    "nodes": [
                                        {"field": {"name": "Status"}, "name": "Done"}
                                    ]
                                },
                                "content": {
                                    "id": "CONTENT_TASK1",
                                    "title": "Task 1",
                                    "body": "**Parent PRD:** PRD_1",
                                },
                            },
                            {
                                "id": "SUBTASK_1",
                                "content": {
                                    "id": "CONTENT_SUB1",
                                    "title": "Subtask 1",
                                    "body": "**Type:** Subtask\n**Parent Task:** TASK_1\n**Status:** Complete",
                                },
                            },
                        ]
                    }
                }
            }
        ]

        result = await relationship_manager.get_hierarchy_tree("PROJECT_123")

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert "hierarchy_tree" in result.metadata
        assert len(result.metadata["hierarchy_tree"]) > 0

    @pytest.mark.asyncio
    async def test_filter_items_by_date_range_success(
        self, relationship_manager, mock_github_client
    ):
        """Test successful filtering of items by date range."""
        # Mock response for filtering items by date
        mock_github_client.query.return_value = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "ITEM_1",
                            "fieldValues": {
                                "nodes": [{"field": {"name": "Status"}, "name": "Done"}]
                            },
                            "content": {
                                "id": "CONTENT_1",
                                "title": "Recent Item",
                                "body": "**Type:** PRD",
                            },
                            "createdAt": "2024-01-15T10:00:00Z",
                        },
                        {
                            "id": "ITEM_2",
                            "fieldValues": {
                                "nodes": [
                                    {"field": {"name": "Status"}, "name": "In Progress"}
                                ]
                            },
                            "content": {
                                "id": "CONTENT_2",
                                "title": "Another Recent Item",
                                "body": "**Parent PRD:** PRD_123",
                            },
                            "createdAt": "2024-01-16T10:00:00Z",
                        },
                    ]
                }
            }
        }

        result = await relationship_manager.filter_items_by_date_range(
            "PROJECT_123", "2024-01-01", "2024-01-31"
        )

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.metadata["items"]) == 2
        assert result.metadata["date_from"] == "2024-01-01"
        assert result.metadata["date_to"] == "2024-01-31"

    @pytest.mark.asyncio
    async def test_query_missing_parameters(self, relationship_manager):
        """Test querying with missing parameters."""
        result = await relationship_manager.query_items_by_status("", "Done")

        assert result.is_valid is False
        assert "Missing required parameters" in result.errors[0]

    @pytest.mark.asyncio
    async def test_query_no_github_client(self):
        """Test querying without GitHub client."""
        manager = RelationshipManager(github_client=None)
        result = await manager.query_items_by_status("PROJECT_123", "Done")

        assert result.is_valid is False
        assert "GitHub client not initialized" in result.errors[0]

    @pytest.mark.asyncio
    async def test_query_api_error(self, relationship_manager, mock_github_client):
        """Test querying with API error."""
        mock_github_client.query.side_effect = Exception("API Error")

        result = await relationship_manager.query_items_by_status("PROJECT_123", "Done")

        assert result.is_valid is False
        assert "Query failed" in result.errors[0]

    @pytest.mark.asyncio
    async def test_search_missing_parameters(self, relationship_manager):
        """Test searching with missing parameters."""
        result = await relationship_manager.search_items_by_title("", "test")

        assert result.is_valid is False
        assert "Missing required parameters" in result.errors[0]

    @pytest.mark.asyncio
    async def test_search_no_github_client(self):
        """Test searching without GitHub client."""
        manager = RelationshipManager(github_client=None)
        result = await manager.search_items_by_title("PROJECT_123", "test")

        assert result.is_valid is False
        assert "GitHub client not initialized" in result.errors[0]

    @pytest.mark.asyncio
    async def test_search_api_error(self, relationship_manager, mock_github_client):
        """Test searching with API error."""
        mock_github_client.query.side_effect = Exception("API Error")

        result = await relationship_manager.search_items_by_title("PROJECT_123", "test")

        assert result.is_valid is False
        assert "Search failed" in result.errors[0]

    @pytest.mark.asyncio
    async def test_orphaned_items_missing_parameters(self, relationship_manager):
        """Test orphaned items detection with missing parameters."""
        result = await relationship_manager.get_orphaned_items("")

        assert result.is_valid is False
        assert "Missing required parameters" in result.errors[0]

    @pytest.mark.asyncio
    async def test_orphaned_items_no_github_client(self):
        """Test orphaned items detection without GitHub client."""
        manager = RelationshipManager(github_client=None)
        result = await manager.get_orphaned_items("PROJECT_123")

        assert result.is_valid is False
        assert "GitHub client not initialized" in result.errors[0]

    @pytest.mark.asyncio
    async def test_orphaned_items_api_error(
        self, relationship_manager, mock_github_client
    ):
        """Test orphaned items detection with API error."""
        mock_github_client.query.side_effect = Exception("API Error")

        result = await relationship_manager.get_orphaned_items("PROJECT_123")

        assert result.is_valid is False
        assert "Orphaned items detection failed" in result.errors[0]


class TestDependencyManagementAndValidation:
    """Test suite for dependency management and validation between hierarchy levels."""

    @pytest.fixture
    def mock_github_client(self):
        """Create a mock GitHub client for testing."""
        return AsyncMock()

    @pytest.fixture
    def relationship_manager(self, mock_github_client):
        """Create RelationshipManager with mock client."""
        return RelationshipManager(github_client=mock_github_client)

    @pytest.mark.asyncio
    async def test_validate_prd_deletion_dependencies_success(
        self, relationship_manager, mock_github_client
    ):
        """Test PRD can be deleted when no dependent tasks exist."""
        # Mock response showing no tasks depend on this PRD
        mock_response = {"node": {"items": {"nodes": []}}}  # No dependent tasks
        mock_github_client.query.return_value = mock_response

        result = await relationship_manager.validate_prd_deletion_dependencies(
            "PROJECT_123", "PRD_123"
        )

        assert result.is_valid is True
        assert result.metadata["can_delete"] is True
        assert result.metadata["dependent_tasks"] == 0
        assert result.metadata["deletion_safe"] is True

    @pytest.mark.asyncio
    async def test_validate_prd_deletion_dependencies_blocked(
        self, relationship_manager, mock_github_client
    ):
        """Test PRD deletion is blocked when dependent tasks exist."""
        # Mock response showing tasks depend on this PRD
        mock_response = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "PVTI_task1",
                            "content": {
                                "id": "DI_task1",
                                "title": "Dependent Task 1",
                                "body": "**Parent PRD:** PRD_123\n\nTask description",
                            },
                        },
                        {
                            "id": "PVTI_task2",
                            "content": {
                                "id": "DI_task2",
                                "title": "Dependent Task 2",
                                "body": "**Parent PRD:** PRD_123\n\nAnother task",
                            },
                        },
                    ]
                }
            }
        }
        mock_github_client.query.return_value = mock_response

        result = await relationship_manager.validate_prd_deletion_dependencies(
            "PROJECT_123", "PRD_123"
        )

        assert result.is_valid is False
        assert result.metadata["can_delete"] is False
        assert result.metadata["dependent_tasks"] == 2
        assert result.metadata["deletion_safe"] is False
        assert "dependent tasks must be deleted first" in result.errors[0].lower()
        assert "Dependent Task 1" in str(result.metadata["blocking_items"])
        assert "Dependent Task 2" in str(result.metadata["blocking_items"])

    @pytest.mark.asyncio
    async def test_validate_task_deletion_dependencies_success(
        self, relationship_manager, mock_github_client
    ):
        """Test task can be deleted when no dependent subtasks exist."""
        # Mock response showing no subtasks depend on this task
        mock_response = {"node": {"items": {"nodes": []}}}  # No dependent subtasks
        mock_github_client.query.return_value = mock_response

        result = await relationship_manager.validate_task_deletion_dependencies(
            "PROJECT_123", "TASK_123"
        )

        assert result.is_valid is True
        assert result.metadata["can_delete"] is True
        assert result.metadata["dependent_subtasks"] == 0
        assert result.metadata["deletion_safe"] is True

    @pytest.mark.asyncio
    async def test_validate_task_deletion_dependencies_blocked(
        self, relationship_manager, mock_github_client
    ):
        """Test task deletion is blocked when dependent subtasks exist."""
        # Mock response showing subtasks depend on this task
        mock_response = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "PVTI_subtask1",
                            "content": {
                                "id": "DI_subtask1",
                                "title": "Dependent Subtask 1",
                                "body": "**Type:** Subtask\n**Parent Task:** TASK_123\n**Order:** 1\n\nSubtask description",
                            },
                        }
                    ]
                }
            }
        }
        mock_github_client.query.return_value = mock_response

        result = await relationship_manager.validate_task_deletion_dependencies(
            "PROJECT_123", "TASK_123"
        )

        assert result.is_valid is False
        assert result.metadata["can_delete"] is False
        assert result.metadata["dependent_subtasks"] == 1
        assert result.metadata["deletion_safe"] is False
        assert "dependent subtasks must be deleted first" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_validate_parent_exists_prd_success(
        self, relationship_manager, mock_github_client
    ):
        """Test validation succeeds when parent PRD exists."""
        # Mock response showing PRD exists
        mock_response = {
            "node": {
                "id": "PRD_123",
                "content": {
                    "id": "DI_prd123",
                    "title": "Existing PRD",
                    "body": "PRD description",
                },
            }
        }
        mock_github_client.query.return_value = mock_response

        result = await relationship_manager.validate_parent_exists(
            "PROJECT_123", "PRD_123", "PRD"
        )

        assert result.is_valid is True
        assert result.metadata["parent_exists"] is True
        assert result.metadata["parent_type"] == "PRD"
        assert result.metadata["parent_id"] == "PRD_123"

    @pytest.mark.asyncio
    async def test_validate_parent_exists_missing_parent(
        self, relationship_manager, mock_github_client
    ):
        """Test validation fails when parent does not exist."""
        # Mock response showing parent doesn't exist
        mock_response = {"node": None}
        mock_github_client.query.return_value = mock_response

        result = await relationship_manager.validate_parent_exists(
            "PROJECT_123", "NONEXISTENT_PRD", "PRD"
        )

        assert result.is_valid is False
        assert result.metadata["parent_exists"] is False
        assert "parent prd does not exist" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_check_dependency_cycles_no_cycles(
        self, relationship_manager, mock_github_client
    ):
        """Test dependency cycle detection when no cycles exist."""
        # Mock project items with proper hierarchy
        mock_response = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "PVTI_prd1",
                            "content": {
                                "id": "DI_prd1",
                                "title": "PRD 1",
                                "body": "**Type:** PRD\n\nPRD description",
                            },
                        },
                        {
                            "id": "PVTI_task1",
                            "content": {
                                "id": "DI_task1",
                                "title": "Task 1",
                                "body": "**Parent PRD:** DI_prd1\n\nTask description",
                            },
                        },
                        {
                            "id": "PVTI_subtask1",
                            "content": {
                                "id": "DI_subtask1",
                                "title": "Subtask 1",
                                "body": "**Type:** Subtask\n**Parent Task:** DI_task1\n**Order:** 1\n\nSubtask description",
                            },
                        },
                    ]
                }
            }
        }
        mock_github_client.query.return_value = mock_response

        result = await relationship_manager.check_dependency_cycles("PROJECT_123")

        assert result.is_valid is True
        assert result.metadata["cycles_detected"] is False
        assert result.metadata["total_items_checked"] == 3
        assert len(result.metadata["dependency_graph"]) == 3

    @pytest.mark.asyncio
    async def test_check_dependency_cycles_cycle_detected(
        self, relationship_manager, mock_github_client
    ):
        """Test dependency cycle detection when cycles exist."""
        # Mock project items with circular dependency
        mock_response = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "PVTI_task1",
                            "content": {
                                "id": "DI_task1",
                                "title": "Task 1",
                                "body": "**Parent PRD:** DI_task2\n\nCyclic dependency",
                            },
                        },
                        {
                            "id": "PVTI_task2",
                            "content": {
                                "id": "DI_task2",
                                "title": "Task 2",
                                "body": "**Parent PRD:** DI_task1\n\nAnother cyclic dependency",
                            },
                        },
                    ]
                }
            }
        }
        mock_github_client.query.return_value = mock_response

        result = await relationship_manager.check_dependency_cycles("PROJECT_123")

        assert result.is_valid is False
        assert result.metadata["cycles_detected"] is True
        assert "circular dependencies detected" in result.errors[0].lower()
        assert len(result.metadata["detected_cycles"]) > 0

    @pytest.mark.asyncio
    async def test_enforce_hierarchy_constraints_success(
        self, relationship_manager, mock_github_client
    ):
        """Test hierarchy constraint enforcement succeeds with valid structure."""
        # Mock project items with valid hierarchy
        mock_response = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "PVTI_prd1",
                            "content": {
                                "id": "DI_prd1",
                                "title": "PRD 1",
                                "body": "**Type:** PRD\n\nPRD description",
                            },
                        },
                        {
                            "id": "PVTI_task1",
                            "content": {
                                "id": "DI_task1",
                                "title": "Task 1",
                                "body": "**Parent PRD:** DI_prd1\n\nTask description",
                            },
                        },
                    ]
                }
            }
        }
        mock_github_client.query.return_value = mock_response

        result = await relationship_manager.enforce_hierarchy_constraints("PROJECT_123")

        assert result.is_valid is True
        assert result.metadata["constraints_violated"] is False
        assert result.metadata["total_items_validated"] == 2

    @pytest.mark.asyncio
    async def test_enforce_hierarchy_constraints_violations(
        self, relationship_manager, mock_github_client
    ):
        """Test hierarchy constraint enforcement detects violations."""
        # Mock project items with constraint violations
        mock_response = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "PVTI_task1",
                            "content": {
                                "id": "DI_task1",
                                "title": "Orphaned Task",
                                "body": "**Parent PRD:** NONEXISTENT_PRD\n\nTask with missing parent",
                            },
                        },
                        {
                            "id": "PVTI_subtask1",
                            "content": {
                                "id": "DI_subtask1",
                                "title": "Invalid Subtask",
                                "body": "**Type:** Subtask\n**Parent Task:** NONEXISTENT_TASK\n**Order:** 1\n\nSubtask with missing parent",
                            },
                        },
                    ]
                }
            }
        }
        mock_github_client.query.return_value = mock_response

        result = await relationship_manager.enforce_hierarchy_constraints("PROJECT_123")

        assert result.is_valid is False
        assert result.metadata["constraints_violated"] is True
        assert "hierarchy constraint violations detected" in result.errors[0].lower()
        assert len(result.metadata["violations"]) >= 2

    @pytest.mark.asyncio
    async def test_get_dependency_chain_success(
        self, relationship_manager, mock_github_client
    ):
        """Test dependency chain retrieval for a complete hierarchy."""
        # Mock project items
        mock_response = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "PVTI_prd1",
                            "content": {
                                "id": "DI_prd1",
                                "title": "PRD 1",
                                "body": "**Type:** PRD\n\nPRD description",
                            },
                        },
                        {
                            "id": "PVTI_task1",
                            "content": {
                                "id": "DI_task1",
                                "title": "Task 1",
                                "body": "**Parent PRD:** DI_prd1\n\nTask description",
                            },
                        },
                        {
                            "id": "PVTI_subtask1",
                            "content": {
                                "id": "DI_subtask1",
                                "title": "Subtask 1",
                                "body": "**Type:** Subtask\n**Parent Task:** DI_task1\n**Order:** 1\n\nSubtask description",
                            },
                        },
                    ]
                }
            }
        }
        mock_github_client.query.return_value = mock_response

        result = await relationship_manager.get_dependency_chain(
            "PROJECT_123", "DI_subtask1"
        )

        assert result.is_valid is True
        assert len(result.metadata["dependency_chain"]) == 3  # PRD -> Task -> Subtask
        assert result.metadata["chain_root"] == "DI_prd1"
        assert result.metadata["target_item"] == "DI_subtask1"

    @pytest.mark.asyncio
    async def test_validate_deletion_impact_analysis(
        self, relationship_manager, mock_github_client
    ):
        """Test deletion impact analysis for cascading effects."""
        # Mock project items with dependencies
        mock_response = {
            "node": {
                "items": {
                    "nodes": [
                        {
                            "id": "PVTI_prd1",
                            "content": {
                                "id": "DI_prd1",
                                "title": "PRD 1",
                                "body": "**Type:** PRD\n\nPRD description",
                            },
                        },
                        {
                            "id": "PVTI_task1",
                            "content": {
                                "id": "DI_task1",
                                "title": "Task 1",
                                "body": "**Parent PRD:** DI_prd1\n\nTask description",
                            },
                        },
                        {
                            "id": "PVTI_task2",
                            "content": {
                                "id": "DI_task2",
                                "title": "Task 2",
                                "body": "**Parent PRD:** DI_prd1\n\nAnother task",
                            },
                        },
                    ]
                }
            }
        }
        mock_github_client.query.return_value = mock_response

        result = await relationship_manager.validate_deletion_impact(
            "PROJECT_123", "DI_prd1", "PRD"
        )

        assert result.is_valid is True
        assert result.metadata["deletion_impact"]["total_affected_items"] == 2
        assert result.metadata["deletion_impact"]["affected_tasks"] == 2
        assert result.metadata["deletion_impact"]["affected_subtasks"] == 0
        assert "Task 1" in str(result.metadata["deletion_impact"]["affected_items"])
        assert "Task 2" in str(result.metadata["deletion_impact"]["affected_items"])

    @pytest.mark.asyncio
    async def test_dependency_validation_missing_parameters(self, relationship_manager):
        """Test dependency validation with missing required parameters."""
        result = await relationship_manager.validate_prd_deletion_dependencies(
            "", "PRD_123"
        )

        assert result.is_valid is False
        assert "missing required parameters" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_dependency_validation_no_github_client(self):
        """Test dependency validation without GitHub client."""
        manager = RelationshipManager(github_client=None)

        result = await manager.validate_prd_deletion_dependencies(
            "PROJECT_123", "PRD_123"
        )

        assert result.is_valid is False
        assert "github client not initialized" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_dependency_validation_api_error(
        self, relationship_manager, mock_github_client
    ):
        """Test dependency validation with API error."""
        mock_github_client.query.side_effect = Exception("API error")

        result = await relationship_manager.validate_prd_deletion_dependencies(
            "PROJECT_123", "PRD_123"
        )

        assert result.is_valid is False
        assert "dependency validation failed" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_parent_validation_missing_parameters(self, relationship_manager):
        """Test parent validation with missing parameters."""
        result = await relationship_manager.validate_parent_exists(
            "", "PARENT_123", "PRD"
        )

        assert result.is_valid is False
        assert "missing required parameters" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_parent_validation_no_github_client(self):
        """Test parent validation without GitHub client."""
        manager = RelationshipManager(github_client=None)

        result = await manager.validate_parent_exists(
            "PROJECT_123", "PARENT_123", "PRD"
        )

        assert result.is_valid is False
        assert "github client not initialized" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_parent_validation_api_error(
        self, relationship_manager, mock_github_client
    ):
        """Test parent validation with API error."""
        mock_github_client.query.side_effect = Exception("API error")

        result = await relationship_manager.validate_parent_exists(
            "PROJECT_123", "PARENT_123", "PRD"
        )

        assert result.is_valid is False
        assert "parent validation failed" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_cycle_detection_missing_parameters(self, relationship_manager):
        """Test cycle detection with missing parameters."""
        result = await relationship_manager.check_dependency_cycles("")

        assert result.is_valid is False
        assert "missing required parameters" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_cycle_detection_no_github_client(self):
        """Test cycle detection without GitHub client."""
        manager = RelationshipManager(github_client=None)

        result = await manager.check_dependency_cycles("PROJECT_123")

        assert result.is_valid is False
        assert "github client not initialized" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_cycle_detection_api_error(
        self, relationship_manager, mock_github_client
    ):
        """Test cycle detection with API error."""
        mock_github_client.query.side_effect = Exception("API error")

        result = await relationship_manager.check_dependency_cycles("PROJECT_123")

        assert result.is_valid is False
        assert "dependency cycle check failed" in result.errors[0].lower()

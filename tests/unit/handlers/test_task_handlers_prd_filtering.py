"""
Unit tests for task handlers PRD filtering functionality.

This test file specifically focuses on the PRD filtering issue identified
during testing where list_tasks with parent_prd_id returns no results.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from github_project_manager_mcp.handlers.task_handlers import list_tasks_handler


class TestTaskHandlersPRDFiltering:
    """Test PRD filtering functionality in task handlers."""

    @pytest.fixture
    def mock_github_client(self):
        """Mock GitHub client for testing."""
        client = AsyncMock()
        return client

    @pytest.fixture
    def sample_task_response(self):
        """Sample GitHub API response with tasks that have Parent PRD field."""
        return {
            "data": {
                "node": {
                    "title": "Test Project",
                    "items": {
                        "totalCount": 2,
                        "pageInfo": {
                            "hasNextPage": False,
                            "hasPreviousPage": False,
                            "startCursor": "cursor1",
                            "endCursor": "cursor2",
                        },
                        "nodes": [
                            {
                                "id": "PVTI_task1",
                                "createdAt": "2025-01-01T00:00:00Z",
                                "updatedAt": "2025-01-01T00:00:00Z",
                                "content": {
                                    "id": "DI_task1",
                                    "title": "Task 1",
                                    "body": "Task 1 description",
                                    "createdAt": "2025-01-01T00:00:00Z",
                                    "updatedAt": "2025-01-01T00:00:00Z",
                                    "assignees": {"totalCount": 0, "nodes": []},
                                },
                                "fieldValues": {
                                    "nodes": [
                                        {
                                            "text": "PVTI_prd1",
                                            "field": {"name": "Parent PRD"},
                                        }
                                    ]
                                },
                            },
                            {
                                "id": "PVTI_task2",
                                "createdAt": "2025-01-01T00:00:00Z",
                                "updatedAt": "2025-01-01T00:00:00Z",
                                "content": {
                                    "id": "DI_task2",
                                    "title": "Task 2",
                                    "body": "Task 2 description",
                                    "createdAt": "2025-01-01T00:00:00Z",
                                    "updatedAt": "2025-01-01T00:00:00Z",
                                    "assignees": {"totalCount": 0, "nodes": []},
                                },
                                "fieldValues": {
                                    "nodes": [
                                        {
                                            "text": "PVTI_prd2",
                                            "field": {"name": "Parent PRD"},
                                        }
                                    ]
                                },
                            },
                        ],
                    },
                }
            }
        }

    @pytest.fixture
    def sample_task_response_with_description_prd(self):
        """Sample GitHub API response with tasks that have Parent PRD in description instead of field."""
        return {
            "data": {
                "node": {
                    "title": "Test Project",
                    "items": {
                        "totalCount": 2,
                        "pageInfo": {
                            "hasNextPage": False,
                            "hasPreviousPage": False,
                            "startCursor": "cursor1",
                            "endCursor": "cursor2",
                        },
                        "nodes": [
                            {
                                "id": "PVTI_task1",
                                "createdAt": "2025-01-01T00:00:00Z",
                                "updatedAt": "2025-01-01T00:00:00Z",
                                "content": {
                                    "id": "DI_task1",
                                    "title": "Task 1",
                                    "body": "Task 1 description\n\n**Parent PRD:** PVTI_prd1\n\n**Priority:** Medium",
                                    "createdAt": "2025-01-01T00:00:00Z",
                                    "updatedAt": "2025-01-01T00:00:00Z",
                                    "assignees": {"totalCount": 0, "nodes": []},
                                },
                                "fieldValues": {
                                    "nodes": []  # No field values, PRD is in description
                                },
                            },
                            {
                                "id": "PVTI_task2",
                                "createdAt": "2025-01-01T00:00:00Z",
                                "updatedAt": "2025-01-01T00:00:00Z",
                                "content": {
                                    "id": "DI_task2",
                                    "title": "Task 2",
                                    "body": "Task 2 description\n\n**Parent PRD:** PVTI_prd2\n\n**Priority:** High",
                                    "createdAt": "2025-01-01T00:00:00Z",
                                    "updatedAt": "2025-01-01T00:00:00Z",
                                    "assignees": {"totalCount": 0, "nodes": []},
                                },
                                "fieldValues": {
                                    "nodes": []  # No field values, PRD is in description
                                },
                            },
                        ],
                    },
                }
            }
        }

    @pytest.mark.asyncio
    async def test_list_tasks_with_prd_filtering_should_return_filtered_tasks(
        self, mock_github_client, sample_task_response
    ):
        """Test that list_tasks with parent_prd_id returns only matching tasks."""
        # Arrange
        mock_github_client.query.return_value = sample_task_response

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            # Act
            result = await list_tasks_handler(
                {
                    "project_id": "PVT_project1",
                    "parent_prd_id": "PVTI_prd1",
                    "first": 25,
                }
            )

        # Assert
        assert (
            not result.isError
        ), f"Expected success but got error: {result.content[0].text if result.content else 'No content'}"

        # Parse the response text to verify filtering worked
        response_text = result.content[0].text
        assert (
            "Task 1" in response_text
        ), "Should include Task 1 which has parent PRD PVTI_prd1"
        assert (
            "Task 2" not in response_text
        ), "Should NOT include Task 2 which has parent PRD PVTI_prd2"
        assert "Total:** 1 tasks" in response_text, "Should show 1 task after filtering"

    @pytest.mark.asyncio
    async def test_list_tasks_with_prd_filtering_description_based_should_return_filtered_tasks(
        self, mock_github_client, sample_task_response_with_description_prd
    ):
        """Test that list_tasks with parent_prd_id works when PRD is in description instead of field."""
        # Arrange
        mock_github_client.query.return_value = (
            sample_task_response_with_description_prd
        )

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            # Act
            result = await list_tasks_handler(
                {
                    "project_id": "PVT_project1",
                    "parent_prd_id": "PVTI_prd1",
                    "first": 25,
                }
            )

        # Assert
        assert (
            not result.isError
        ), f"Expected success but got error: {result.content[0].text if result.content else 'No content'}"

        # Parse the response text to verify filtering worked with description parsing
        response_text = result.content[0].text
        assert (
            "Task 1" in response_text
        ), "Should include Task 1 which has parent PRD PVTI_prd1 in description"
        assert (
            "Task 2" not in response_text
        ), "Should NOT include Task 2 which has parent PRD PVTI_prd2 in description"
        assert "Total:** 1 tasks" in response_text, "Should show 1 task after filtering"

    @pytest.mark.asyncio
    async def test_list_tasks_without_prd_filtering_should_return_all_tasks(
        self, mock_github_client, sample_task_response
    ):
        """Test that list_tasks without parent_prd_id returns all tasks."""
        # Arrange
        mock_github_client.query.return_value = sample_task_response

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            # Act
            result = await list_tasks_handler(
                {"project_id": "PVT_project1", "first": 25}
            )

        # Assert
        assert (
            not result.isError
        ), f"Expected success but got error: {result.content[0].text if result.content else 'No content'}"

        # Parse the response text to verify all tasks are returned
        response_text = result.content[0].text
        assert "Task 1" in response_text, "Should include Task 1"
        assert "Task 2" in response_text, "Should include Task 2"
        assert (
            "Total:** 2 tasks" in response_text
        ), "Should show 2 tasks when no filtering"

    @pytest.mark.asyncio
    async def test_list_tasks_with_nonexistent_prd_should_return_no_tasks(
        self, mock_github_client, sample_task_response
    ):
        """Test that list_tasks with non-existent parent_prd_id returns no tasks."""
        # Arrange
        mock_github_client.query.return_value = sample_task_response

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            # Act
            result = await list_tasks_handler(
                {
                    "project_id": "PVT_project1",
                    "parent_prd_id": "PVTI_nonexistent",
                    "first": 25,
                }
            )

        # Assert
        assert (
            not result.isError
        ), f"Expected success but got error: {result.content[0].text if result.content else 'No content'}"

        # Parse the response text to verify no tasks are returned
        response_text = result.content[0].text
        assert "Task 1" not in response_text, "Should NOT include Task 1"
        assert "Task 2" not in response_text, "Should NOT include Task 2"
        assert (
            "Total:** 0 tasks" in response_text
        ), "Should show 0 tasks when no matches"

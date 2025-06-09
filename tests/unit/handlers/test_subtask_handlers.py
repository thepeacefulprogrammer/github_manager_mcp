"""
Unit tests for subtask handler functions.

This module provides comprehensive test coverage for all subtask management
operations including creation, listing, updating, and deletion of subtasks
within GitHub Projects v2 Tasks.
"""

from unittest.mock import AsyncMock, patch

import pytest
from mcp.types import CallToolResult, TextContent

from src.github_project_manager_mcp.handlers.subtask_handlers import (
    add_subtask_handler,
    list_subtasks_handler,
)


class TestAddSubtaskHandler:
    """Test cases for the add_subtask_handler function."""

    @pytest.mark.asyncio
    async def test_add_subtask_success_minimal_params(self):
        """Test successful subtask creation with minimal required parameters."""
        mock_client = AsyncMock()
        mock_response = {
            "addProjectV2DraftIssue": {
                "projectItem": {
                    "id": "PVTI_test123",
                    "content": {
                        "title": "Test Subtask",
                        "createdAt": "2024-01-01T10:00:00Z",
                    },
                }
            }
        }
        mock_client.mutate.return_value = mock_response

        with patch(
            "src.github_project_manager_mcp.handlers.subtask_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await add_subtask_handler(
                {
                    "project_id": "PVT_test123",
                    "parent_task_id": "PVTI_parent123",
                    "title": "Test Subtask",
                }
            )

        assert not result.isError
        assert "Subtask created successfully!" in result.content[0].text
        assert "Test Subtask" in result.content[0].text
        assert "PVTI_test123" in result.content[0].text
        assert "PVTI_parent123" in result.content[0].text

    @pytest.mark.asyncio
    async def test_add_subtask_success_all_params(self):
        """Test successful subtask creation with all optional parameters."""
        mock_client = AsyncMock()
        mock_response = {
            "addProjectV2DraftIssue": {
                "projectItem": {
                    "id": "PVTI_test456",
                    "content": {
                        "title": "Comprehensive Test Subtask",
                        "createdAt": "2024-01-01T10:00:00Z",
                    },
                }
            }
        }
        mock_client.mutate.return_value = mock_response

        with patch(
            "src.github_project_manager_mcp.handlers.subtask_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await add_subtask_handler(
                {
                    "project_id": "PVT_test123",
                    "parent_task_id": "PVTI_parent456",
                    "title": "Comprehensive Test Subtask",
                    "description": "Detailed subtask description",
                    "order": 3,
                }
            )

        assert not result.isError
        assert "Subtask created successfully!" in result.content[0].text
        assert "Comprehensive Test Subtask" in result.content[0].text
        assert "**Order:** 3" in result.content[0].text
        assert "Detailed subtask description" in result.content[0].text

    @pytest.mark.asyncio
    async def test_add_subtask_missing_project_id(self):
        """Test error handling when project_id is missing."""
        result = await add_subtask_handler(
            {
                "parent_task_id": "PVTI_parent123",
                "title": "Test Subtask",
            }
        )

        assert result.isError
        assert "project_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_add_subtask_empty_project_id(self):
        """Test error handling when project_id is empty."""
        result = await add_subtask_handler(
            {
                "project_id": "   ",
                "parent_task_id": "PVTI_parent123",
                "title": "Test Subtask",
            }
        )

        assert result.isError
        assert "project_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_add_subtask_missing_parent_task_id(self):
        """Test error handling when parent_task_id is missing."""
        result = await add_subtask_handler(
            {
                "project_id": "PVT_test123",
                "title": "Test Subtask",
            }
        )

        assert result.isError
        assert "parent_task_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_add_subtask_empty_parent_task_id(self):
        """Test error handling when parent_task_id is empty."""
        result = await add_subtask_handler(
            {
                "project_id": "PVT_test123",
                "parent_task_id": "",
                "title": "Test Subtask",
            }
        )

        assert result.isError
        assert "parent_task_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_add_subtask_missing_title(self):
        """Test error handling when title is missing."""
        result = await add_subtask_handler(
            {
                "project_id": "PVT_test123",
                "parent_task_id": "PVTI_parent123",
            }
        )

        assert result.isError
        assert "title is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_add_subtask_empty_title(self):
        """Test error handling when title is empty."""
        result = await add_subtask_handler(
            {
                "project_id": "PVT_test123",
                "parent_task_id": "PVTI_parent123",
                "title": "   ",
            }
        )

        assert result.isError
        assert "title is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_add_subtask_invalid_order_negative(self):
        """Test error handling when order is negative."""
        result = await add_subtask_handler(
            {
                "project_id": "PVT_test123",
                "parent_task_id": "PVTI_parent123",
                "title": "Test Subtask",
                "order": -1,
            }
        )

        assert result.isError
        assert "order must be a positive integer" in result.content[0].text

    @pytest.mark.asyncio
    async def test_add_subtask_invalid_order_zero(self):
        """Test error handling when order is zero."""
        result = await add_subtask_handler(
            {
                "project_id": "PVT_test123",
                "parent_task_id": "PVTI_parent123",
                "title": "Test Subtask",
                "order": 0,
            }
        )

        assert result.isError
        assert "order must be a positive integer" in result.content[0].text

    @pytest.mark.asyncio
    async def test_add_subtask_invalid_order_non_integer(self):
        """Test error handling when order is not an integer."""
        result = await add_subtask_handler(
            {
                "project_id": "PVT_test123",
                "parent_task_id": "PVTI_parent123",
                "title": "Test Subtask",
                "order": "invalid",
            }
        )

        assert result.isError
        assert "order must be a positive integer" in result.content[0].text

    @pytest.mark.asyncio
    async def test_add_subtask_github_client_not_initialized(self):
        """Test error handling when GitHub client is not initialized."""
        with patch(
            "src.github_project_manager_mcp.handlers.subtask_handlers.get_github_client",
            return_value=None,
        ):
            result = await add_subtask_handler(
                {
                    "project_id": "PVT_test123",
                    "parent_task_id": "PVTI_parent123",
                    "title": "Test Subtask",
                }
            )

        assert result.isError
        assert "GitHub client not initialized" in result.content[0].text

    @pytest.mark.asyncio
    async def test_add_subtask_invalid_project_id(self):
        """Test error handling when project ID is invalid."""
        mock_client = AsyncMock()
        mock_client.mutate.side_effect = Exception(
            "could not resolve to projectv2 node"
        )

        with patch(
            "src.github_project_manager_mcp.handlers.subtask_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await add_subtask_handler(
                {
                    "project_id": "invalid_project",
                    "parent_task_id": "PVTI_parent123",
                    "title": "Test Subtask",
                }
            )

        assert result.isError
        assert "Invalid project ID" in result.content[0].text

    @pytest.mark.asyncio
    async def test_add_subtask_api_error(self):
        """Test error handling when API call fails."""
        mock_client = AsyncMock()
        mock_client.mutate.side_effect = Exception("API error occurred")

        with patch(
            "src.github_project_manager_mcp.handlers.subtask_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await add_subtask_handler(
                {
                    "project_id": "PVT_test123",
                    "parent_task_id": "PVTI_parent123",
                    "title": "Test Subtask",
                }
            )

        assert result.isError
        assert "Failed to create subtask: API error occurred" in result.content[0].text

    @pytest.mark.asyncio
    async def test_add_subtask_no_response_data(self):
        """Test error handling when API returns no data."""
        mock_client = AsyncMock()
        mock_client.mutate.return_value = None

        with patch(
            "src.github_project_manager_mcp.handlers.subtask_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await add_subtask_handler(
                {
                    "project_id": "PVT_test123",
                    "parent_task_id": "PVTI_parent123",
                    "title": "Test Subtask",
                }
            )

        assert result.isError
        assert "No data returned from API" in result.content[0].text

    @pytest.mark.asyncio
    async def test_add_subtask_invalid_response_format(self):
        """Test error handling when API returns invalid response format."""
        mock_client = AsyncMock()
        mock_client.mutate.return_value = {"invalid": "response"}

        with patch(
            "src.github_project_manager_mcp.handlers.subtask_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await add_subtask_handler(
                {
                    "project_id": "PVT_test123",
                    "parent_task_id": "PVTI_parent123",
                    "title": "Test Subtask",
                }
            )

        assert result.isError
        assert "Invalid response format" in result.content[0].text

    @pytest.mark.asyncio
    async def test_add_subtask_unexpected_error(self):
        """Test error handling for unexpected exceptions."""
        with patch(
            "src.github_project_manager_mcp.handlers.subtask_handlers.get_github_client",
            side_effect=Exception("Unexpected error"),
        ):
            result = await add_subtask_handler(
                {
                    "project_id": "PVT_test123",
                    "parent_task_id": "PVTI_parent123",
                    "title": "Test Subtask",
                }
            )

        assert result.isError
        assert "Unexpected error creating subtask" in result.content[0].text


class TestListSubtasksHandler:
    """Test cases for the list_subtasks_handler function."""

    @pytest.mark.asyncio
    async def test_list_subtasks_success_with_parent_task(self):
        """Test successful subtask listing filtered by parent task."""
        mock_client = AsyncMock()
        mock_response = {
            "node": {
                "items": {
                    "totalCount": 2,
                    "pageInfo": {
                        "hasNextPage": False,
                        "endCursor": "cursor123",
                    },
                    "nodes": [
                        {
                            "id": "PVTI_subtask1",
                            "content": {
                                "title": "First Subtask",
                                "body": "Description of first subtask\n\n## Subtask Metadata\n- **Type:** Subtask\n- **Parent Task ID:** PVTI_parent123\n- **Order:** 1\n- **Status:** Incomplete",
                                "createdAt": "2024-01-01T10:00:00Z",
                                "updatedAt": "2024-01-01T11:00:00Z",
                            },
                            "parent_task": {"id": "PVTI_parent123"},
                        },
                        {
                            "id": "PVTI_subtask2",
                            "content": {
                                "title": "Second Subtask",
                                "body": "Description of second subtask\n\n## Subtask Metadata\n- **Type:** Subtask\n- **Parent Task ID:** PVTI_parent123\n- **Order:** 2\n- **Status:** Incomplete",
                                "createdAt": "2024-01-01T12:00:00Z",
                                "updatedAt": "2024-01-01T13:00:00Z",
                            },
                            "parent_task": {"id": "PVTI_parent123"},
                        },
                    ],
                }
            }
        }
        mock_client.query.return_value = mock_response

        with patch(
            "src.github_project_manager_mcp.handlers.subtask_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await list_subtasks_handler(
                {
                    "project_id": "PVT_test123",
                    "parent_task_id": "PVTI_parent123",
                }
            )

        assert not result.isError
        content = result.content[0].text
        assert "Subtasks in Project" in content
        assert "**Total:** 2 subtasks" in content
        assert "First Subtask" in content
        assert "Second Subtask" in content
        assert "PVTI_subtask1" in content
        assert "PVTI_subtask2" in content

    @pytest.mark.asyncio
    async def test_list_subtasks_success_all_subtasks(self):
        """Test successful listing of all subtasks in project without parent filter."""
        mock_client = AsyncMock()
        mock_response = {
            "node": {
                "items": {
                    "totalCount": 3,
                    "pageInfo": {
                        "hasNextPage": False,
                        "endCursor": "cursor456",
                    },
                    "nodes": [
                        {
                            "id": "PVTI_subtask1",
                            "content": {
                                "title": "Task A Subtask",
                                "body": "Description A\n\n## Subtask Metadata\n- **Type:** Subtask\n- **Parent Task ID:** PVTI_taskA\n- **Order:** 1\n- **Status:** Incomplete",
                                "createdAt": "2024-01-01T10:00:00Z",
                                "updatedAt": "2024-01-01T11:00:00Z",
                            },
                            "parent_task": {"id": "PVTI_taskA"},
                        },
                        {
                            "id": "PVTI_subtask2",
                            "content": {
                                "title": "Task B Subtask 1",
                                "body": "Description B1\n\n## Subtask Metadata\n- **Type:** Subtask\n- **Parent Task ID:** PVTI_taskB\n- **Order:** 1\n- **Status:** Incomplete",
                                "createdAt": "2024-01-01T12:00:00Z",
                                "updatedAt": "2024-01-01T13:00:00Z",
                            },
                            "parent_task": {"id": "PVTI_taskB"},
                        },
                        {
                            "id": "PVTI_subtask3",
                            "content": {
                                "title": "Task B Subtask 2",
                                "body": "Description B2\n\n## Subtask Metadata\n- **Type:** Subtask\n- **Parent Task ID:** PVTI_taskB\n- **Order:** 2\n- **Status:** Incomplete",
                                "createdAt": "2024-01-01T14:00:00Z",
                                "updatedAt": "2024-01-01T15:00:00Z",
                            },
                            "parent_task": {"id": "PVTI_taskB"},
                        },
                    ],
                }
            }
        }
        mock_client.query.return_value = mock_response

        with patch(
            "src.github_project_manager_mcp.handlers.subtask_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await list_subtasks_handler(
                {
                    "project_id": "PVT_test123",
                }
            )

        assert not result.isError
        content = result.content[0].text
        assert "**Total:** 3 subtasks" in content
        assert "Task A Subtask" in content
        assert "Task B Subtask 1" in content
        assert "Task B Subtask 2" in content

    @pytest.mark.asyncio
    async def test_list_subtasks_success_empty_result(self):
        """Test successful query but no subtasks found."""
        mock_client = AsyncMock()
        mock_response = {
            "node": {
                "items": {
                    "totalCount": 0,
                    "pageInfo": {
                        "hasNextPage": False,
                        "endCursor": None,
                    },
                    "nodes": [],
                }
            }
        }
        mock_client.query.return_value = mock_response

        with patch(
            "src.github_project_manager_mcp.handlers.subtask_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await list_subtasks_handler(
                {
                    "project_id": "PVT_test123",
                    "parent_task_id": "PVTI_parent123",
                }
            )

        assert not result.isError
        content = result.content[0].text
        assert "No subtasks found" in content
        assert "**Total:** 0 subtasks" in content

    @pytest.mark.asyncio
    async def test_list_subtasks_success_with_pagination(self):
        """Test successful subtask listing with pagination parameters."""
        mock_client = AsyncMock()
        mock_response = {
            "node": {
                "items": {
                    "totalCount": 25,
                    "pageInfo": {
                        "hasNextPage": True,
                        "endCursor": "next_cursor_789",
                    },
                    "nodes": [
                        {
                            "id": f"PVTI_subtask{i}",
                            "content": {
                                "title": f"Subtask {i}",
                                "body": f"Description {i}\n\n## Subtask Metadata\n- **Type:** Subtask\n- **Parent Task ID:** PVTI_parent123\n- **Order:** {i}\n- **Status:** Incomplete",
                                "createdAt": "2024-01-01T10:00:00Z",
                                "updatedAt": "2024-01-01T11:00:00Z",
                            },
                            "parent_task": {"id": "PVTI_parent123"},
                        }
                        for i in range(1, 11)  # 10 items
                    ],
                }
            }
        }
        mock_client.query.return_value = mock_response

        with patch(
            "src.github_project_manager_mcp.handlers.subtask_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await list_subtasks_handler(
                {
                    "project_id": "PVT_test123",
                    "first": 10,
                    "after": "prev_cursor",
                }
            )

        assert not result.isError
        content = result.content[0].text
        assert "**Showing:** 10 subtasks" in content
        assert "**Has next page:** True" in content
        assert "**Next cursor:** next_cursor_789" in content

    @pytest.mark.asyncio
    async def test_list_subtasks_missing_project_id(self):
        """Test error handling when project_id is missing."""
        result = await list_subtasks_handler({})

        assert result.isError
        assert "project_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_list_subtasks_empty_project_id(self):
        """Test error handling when project_id is empty."""
        result = await list_subtasks_handler(
            {
                "project_id": "   ",
            }
        )

        assert result.isError
        assert "project_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_list_subtasks_invalid_first_negative(self):
        """Test error handling when 'first' parameter is negative."""
        result = await list_subtasks_handler(
            {
                "project_id": "PVT_test123",
                "first": -5,
            }
        )

        assert result.isError
        assert "first must be a positive integer" in result.content[0].text

    @pytest.mark.asyncio
    async def test_list_subtasks_invalid_first_zero(self):
        """Test error handling when 'first' parameter is zero."""
        result = await list_subtasks_handler(
            {
                "project_id": "PVT_test123",
                "first": 0,
            }
        )

        assert result.isError
        assert "first must be a positive integer" in result.content[0].text

    @pytest.mark.asyncio
    async def test_list_subtasks_invalid_first_too_large(self):
        """Test error handling when 'first' parameter exceeds maximum."""
        result = await list_subtasks_handler(
            {
                "project_id": "PVT_test123",
                "first": 101,
            }
        )

        assert result.isError
        assert (
            "first must be a positive integer and cannot exceed 100"
            in result.content[0].text
        )

    @pytest.mark.asyncio
    async def test_list_subtasks_github_client_not_initialized(self):
        """Test error handling when GitHub client is not initialized."""
        with patch(
            "src.github_project_manager_mcp.handlers.subtask_handlers.get_github_client",
            return_value=None,
        ):
            result = await list_subtasks_handler(
                {
                    "project_id": "PVT_test123",
                }
            )

        assert result.isError
        assert "GitHub client not initialized" in result.content[0].text

    @pytest.mark.asyncio
    async def test_list_subtasks_graphql_error(self):
        """Test error handling when GraphQL query returns errors."""
        mock_client = AsyncMock()
        mock_client.query.side_effect = Exception("GraphQL error: Invalid project ID")

        with patch(
            "src.github_project_manager_mcp.handlers.subtask_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await list_subtasks_handler(
                {
                    "project_id": "PVT_invalid",
                }
            )

        assert result.isError
        assert "Error listing subtasks" in result.content[0].text
        assert "GraphQL error: Invalid project ID" in result.content[0].text

    @pytest.mark.asyncio
    async def test_list_subtasks_invalid_response_format(self):
        """Test error handling when API response has unexpected format."""
        mock_client = AsyncMock()
        mock_client.query.return_value = {"unexpected": "format"}

        with patch(
            "src.github_project_manager_mcp.handlers.subtask_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await list_subtasks_handler(
                {
                    "project_id": "PVT_test123",
                }
            )

        assert result.isError
        assert "Error listing subtasks" in result.content[0].text

    @pytest.mark.asyncio
    async def test_list_subtasks_api_exception(self):
        """Test error handling when API call raises an exception."""
        mock_client = AsyncMock()
        mock_client.query.side_effect = RuntimeError("Network timeout")

        with patch(
            "src.github_project_manager_mcp.handlers.subtask_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await list_subtasks_handler(
                {
                    "project_id": "PVT_test123",
                }
            )

        assert result.isError
        assert "Error listing subtasks" in result.content[0].text
        assert "Network timeout" in result.content[0].text

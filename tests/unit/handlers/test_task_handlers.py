"""
Unit tests for Task handlers.

Tests the Task handler functionality including:
- create_task tool handler with PRD association
- list_tasks tool handler with PRD and project filtering
- Parameter validation and error handling
"""

from unittest.mock import AsyncMock, patch

import pytest
from mcp.types import CallToolResult, TextContent

from src.github_project_manager_mcp.handlers.task_handlers import (
    TASK_TOOL_HANDLERS,
    TASK_TOOLS,
    create_task_handler,
    get_github_client,
    list_tasks_handler,
    complete_task_handler,
)


class TestCreateTaskHandler:
    """Test create_task handler functionality."""

    @pytest.mark.asyncio
    async def test_create_task_success(self):
        """Test successful task creation."""
        mock_client = AsyncMock()
        mock_client.mutate.return_value = {
            "addProjectV2DraftIssue": {
                "projectItem": {
                    "id": "PVTI_task123",
                    "content": {
                        "__typename": "DraftIssue",
                        "title": "Test task",
                        "body": "Test description",
                        "createdAt": "2024-01-01T10:00:00Z",
                    },
                }
            }
        }

        with patch(
            "src.github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await create_task_handler(
                {
                    "project_id": "PVT_project123",
                    "parent_prd_id": "PVTI_prd456",
                    "title": "Test task",
                }
            )

        assert result.isError is False
        assert "Task created successfully" in result.content[0].text

    @pytest.mark.asyncio
    async def test_create_task_missing_project_id(self):
        """Test error when project_id is missing."""
        result = await create_task_handler(
            {"parent_prd_id": "PVTI_prd456", "title": "Test task"}
        )

        assert result.isError is True
        assert "project_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_create_task_missing_parent_prd_id(self):
        """Test error when parent_prd_id is missing."""
        result = await create_task_handler(
            {"project_id": "PVT_project123", "title": "Test task"}
        )

        assert result.isError is True
        assert "parent_prd_id is required" in result.content[0].text


class TestListTasksHandler:
    """Test list_tasks handler functionality."""

    @pytest.mark.asyncio
    async def test_list_tasks_success_with_tasks(self):
        """Test successful task listing with tasks in project."""
        mock_client = AsyncMock()
        mock_client.query.return_value = {
            "data": {
                "node": {
                    "title": "Test Project",
                    "items": {
                        "totalCount": 2,
                        "pageInfo": {"hasNextPage": False, "endCursor": "cursor123"},
                        "nodes": [
                            {
                                "id": "PVTI_task123",
                                "createdAt": "2024-01-01T10:00:00Z",
                                "updatedAt": "2024-01-01T12:00:00Z",
                                "content": {
                                    "title": "Implement authentication",
                                    "body": "Add OAuth2 support\n\n**Parent PRD:** PVTI_prd456\n\n**Priority:** High",
                                    "createdAt": "2024-01-01T10:00:00Z",
                                },
                                "fieldValues": {
                                    "nodes": [
                                        {
                                            "field": {"name": "Parent PRD"},
                                            "text": "PVTI_prd456",
                                        },
                                        {
                                            "field": {"name": "Priority"},
                                            "singleSelectOption": {"name": "High"},
                                        },
                                    ]
                                },
                            },
                            {
                                "id": "PVTI_task456",
                                "createdAt": "2024-01-01T11:00:00Z",
                                "updatedAt": "2024-01-01T13:00:00Z",
                                "content": {
                                    "title": "Database schema",
                                    "body": "Design user tables\n\n**Parent PRD:** PVTI_prd789",
                                    "createdAt": "2024-01-01T11:00:00Z",
                                },
                                "fieldValues": {
                                    "nodes": [
                                        {
                                            "field": {"name": "Parent PRD"},
                                            "text": "PVTI_prd789",
                                        }
                                    ]
                                },
                            },
                        ],
                    },
                }
            }
        }

        with patch(
            "src.github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await list_tasks_handler({"project_id": "PVT_project123"})

        assert result.isError is False
        content = result.content[0].text
        assert "Tasks in Project: Test Project" in content
        assert "**Total:** 2 tasks" in content
        assert "Implement authentication" in content
        assert "Database schema" in content

    @pytest.mark.asyncio
    async def test_list_tasks_success_empty_project(self):
        """Test successful task listing with empty project."""
        mock_client = AsyncMock()
        mock_client.query.return_value = {
            "data": {
                "node": {
                    "title": "Empty Project",
                    "items": {
                        "totalCount": 0,
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                        "nodes": [],
                    },
                }
            }
        }

        with patch(
            "src.github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await list_tasks_handler({"project_id": "PVT_project123"})

        assert result.isError is False
        content = result.content[0].text
        assert "Tasks in Project: Empty Project" in content
        assert "**Total:** 0 tasks" in content
        assert "No tasks found" in content

    @pytest.mark.asyncio
    async def test_list_tasks_with_parent_prd_filter(self):
        """Test task listing with parent PRD filter."""
        mock_client = AsyncMock()
        mock_client.query.return_value = {
            "data": {
                "node": {
                    "title": "Test Project",
                    "items": {
                        "totalCount": 1,
                        "pageInfo": {"hasNextPage": False, "endCursor": "cursor123"},
                        "nodes": [
                            {
                                "id": "PVTI_task123",
                                "createdAt": "2024-01-01T10:00:00Z",
                                "updatedAt": "2024-01-01T12:00:00Z",
                                "content": {
                                    "title": "Filtered task",
                                    "body": "Task for specific PRD\n\n**Parent PRD:** PVTI_prd456",
                                    "createdAt": "2024-01-01T10:00:00Z",
                                },
                                "fieldValues": {
                                    "nodes": [
                                        {
                                            "field": {"name": "Parent PRD"},
                                            "text": "PVTI_prd456",
                                        }
                                    ]
                                },
                            }
                        ],
                    },
                }
            }
        }

        with patch(
            "src.github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await list_tasks_handler(
                {"project_id": "PVT_project123", "parent_prd_id": "PVTI_prd456"}
            )

        assert result.isError is False
        content = result.content[0].text
        assert "Tasks in Project: Test Project" in content
        assert "Parent PRD: PVTI_prd456" in content
        assert "Filtered task" in content

    @pytest.mark.asyncio
    async def test_list_tasks_with_pagination(self):
        """Test task listing with pagination parameters."""
        mock_client = AsyncMock()
        mock_client.query.return_value = {
            "data": {
                "node": {
                    "title": "Test Project",
                    "items": {
                        "totalCount": 10,
                        "pageInfo": {"hasNextPage": True, "endCursor": "cursor456"},
                        "nodes": [
                            {
                                "id": "PVTI_task123",
                                "createdAt": "2024-01-01T10:00:00Z",
                                "updatedAt": "2024-01-01T12:00:00Z",
                                "content": {
                                    "title": "Task 1",
                                    "body": "First task\n\n**Parent PRD:** PVTI_prd456",
                                    "createdAt": "2024-01-01T10:00:00Z",
                                },
                                "fieldValues": {
                                    "nodes": [
                                        {
                                            "field": {"name": "Parent PRD"},
                                            "text": "PVTI_prd456",
                                        }
                                    ]
                                },
                            }
                        ],
                    },
                }
            }
        }

        with patch(
            "src.github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await list_tasks_handler(
                {"project_id": "PVT_project123", "first": 5, "after": "cursor123"}
            )

        assert result.isError is False
        content = result.content[0].text
        assert "**Showing:** 1 tasks" in content
        assert "**Next page available**" in content

    @pytest.mark.asyncio
    async def test_list_tasks_missing_project_id(self):
        """Test error when project_id is missing."""
        result = await list_tasks_handler({})

        assert result.isError is True
        assert "project_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_list_tasks_invalid_first_parameter(self):
        """Test error when first parameter is invalid."""
        result = await list_tasks_handler(
            {"project_id": "PVT_project123", "first": "invalid"}
        )

        assert result.isError is True
        assert "'first' parameter must be a positive integer" in result.content[0].text

    @pytest.mark.asyncio
    async def test_list_tasks_github_client_not_initialized(self):
        """Test error when GitHub client is not initialized."""
        with patch(
            "src.github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=None,
        ):
            result = await list_tasks_handler({"project_id": "PVT_project123"})

        assert result.isError is True
        assert "GitHub client not initialized" in result.content[0].text

    @pytest.mark.asyncio
    async def test_list_tasks_project_not_found(self):
        """Test error when project is not found."""
        mock_client = AsyncMock()
        mock_client.query.return_value = {"data": {"node": None}}

        with patch(
            "src.github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await list_tasks_handler({"project_id": "invalid_project_id"})

        assert result.isError is True
        assert (
            "Project with ID 'invalid_project_id' not found" in result.content[0].text
        )

    @pytest.mark.asyncio
    async def test_list_tasks_graphql_errors(self):
        """Test error handling when GraphQL returns errors."""
        mock_client = AsyncMock()
        mock_client.query.return_value = {
            "errors": [
                {"message": "Rate limit exceeded"},
                {"message": "Invalid project ID"},
            ]
        }

        with patch(
            "src.github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await list_tasks_handler({"project_id": "PVT_project123"})

        assert result.isError is True
        assert "GraphQL errors" in result.content[0].text


class TestTaskHandlerRegistration:
    """Test task handler registration."""

    def test_task_tools_exist(self):
        """Test that task tools are registered."""
        tool_names = [tool.name for tool in TASK_TOOLS]
        assert "create_task" in tool_names
        assert "list_tasks" in tool_names

    def test_task_handlers_exist(self):
        """Test that task handlers are registered."""
        assert "create_task" in TASK_TOOL_HANDLERS
        assert "list_tasks" in TASK_TOOL_HANDLERS
        assert callable(TASK_TOOL_HANDLERS["create_task"])
        assert callable(TASK_TOOL_HANDLERS["list_tasks"])

    def test_list_tasks_tool_definition(self):
        """Test list_tasks tool definition."""
        list_tasks_tool = next(
            (tool for tool in TASK_TOOLS if tool.name == "list_tasks"), None
        )

        assert list_tasks_tool is not None
        assert list_tasks_tool.name == "list_tasks"
        assert "List tasks in a GitHub project" in list_tasks_tool.description

        # Check required parameters
        schema = list_tasks_tool.inputSchema
        required = schema.get("required", [])
        assert "project_id" in required

        # Check parameter definitions
        properties = schema.get("properties", {})
        assert "project_id" in properties
        assert "parent_prd_id" in properties
        assert "first" in properties
        assert "after" in properties


class TestUpdateTaskHandler:
    """Test cases for update_task MCP tool."""

    @pytest.mark.asyncio
    async def test_update_task_success_all_fields(self):
        """Test successful task update with all fields."""
        mock_arguments = {
            "task_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "title": "Updated Task Title",
            "description": "Updated task description with new requirements",
            "status": "In Progress",
            "priority": "High",
            "estimated_hours": 8,
            "actual_hours": 5,
        }

        # Mock GitHub client and response
        mock_client = AsyncMock()

        # Mock task content query response
        mock_content_response = {
            "node": {"content": {"id": "MDHI_lADOBQfyVc4AYzgCzgC5wQk"}}
        }

        # Mock draft issue update response
        mock_update_response = {
            "updateProjectV2DraftIssue": {
                "draftIssue": {
                    "id": "MDHI_lADOBQfyVc4AYzgCzgC5wQk",
                    "title": "Updated Task Title",
                    "body": "Updated task description with new requirements",
                    "createdAt": "2025-01-01T10:00:00Z",
                    "updatedAt": "2025-01-01T12:00:00Z",
                    "projectV2Items": {
                        "nodes": [
                            {
                                "project": {
                                    "id": "PVT_kwDOBQfyVc0FoQ",
                                    "title": "Test Project",
                                }
                            }
                        ]
                    },
                }
            }
        }

        # Mock project item field details response for status/priority updates
        mock_fields_response = {
            "node": {
                "id": "PVTI_lADOBQfyVc0FoQzgBVgC",
                "project": {
                    "id": "PVT_kwDOBQfyVc0FoQ",
                    "fields": {
                        "nodes": [
                            {
                                "id": "FIELD_STATUS_ID",
                                "name": "Status",
                                "dataType": "SINGLE_SELECT",
                                "options": [
                                    {"id": "OPT_TODO", "name": "Todo"},
                                    {"id": "OPT_IN_PROGRESS", "name": "In Progress"},
                                    {"id": "OPT_DONE", "name": "Done"},
                                ],
                            },
                            {
                                "id": "FIELD_PRIORITY_ID",
                                "name": "Priority",
                                "dataType": "SINGLE_SELECT",
                                "options": [
                                    {"id": "OPT_LOW", "name": "Low"},
                                    {"id": "OPT_MEDIUM", "name": "Medium"},
                                    {"id": "OPT_HIGH", "name": "High"},
                                ],
                            },
                            {
                                "id": "FIELD_EST_HOURS_ID",
                                "name": "Estimated Hours",
                                "dataType": "NUMBER",
                            },
                            {
                                "id": "FIELD_ACT_HOURS_ID",
                                "name": "Actual Hours",
                                "dataType": "NUMBER",
                            },
                        ]
                    },
                },
            }
        }

        # Mock field update responses
        mock_status_update_response = {
            "updateProjectV2ItemFieldValue": {
                "projectV2Item": {
                    "id": "PVTI_lADOBQfyVc0FoQzgBVgC",
                    "updatedAt": "2025-01-01T12:30:00Z",
                }
            }
        }

        mock_priority_update_response = {
            "updateProjectV2ItemFieldValue": {
                "projectV2Item": {
                    "id": "PVTI_lADOBQfyVc0FoQzgBVgC",
                    "updatedAt": "2025-01-01T12:31:00Z",
                }
            }
        }

        mock_est_hours_update_response = {
            "updateProjectV2ItemFieldValue": {
                "projectV2Item": {
                    "id": "PVTI_lADOBQfyVc0FoQzgBVgC",
                    "updatedAt": "2025-01-01T12:32:00Z",
                }
            }
        }

        mock_act_hours_update_response = {
            "updateProjectV2ItemFieldValue": {
                "projectV2Item": {
                    "id": "PVTI_lADOBQfyVc0FoQzgBVgC",
                    "updatedAt": "2025-01-01T12:33:00Z",
                }
            }
        }

        # Setup mock client call sequence
        mock_client.query.side_effect = [
            mock_content_response,  # Get task content ID
            mock_fields_response,  # Get project fields for field updates
        ]
        mock_client.mutate.side_effect = [
            mock_update_response,  # Update task title/description
            mock_status_update_response,  # Update status field
            mock_priority_update_response,  # Update priority field
            mock_est_hours_update_response,  # Update estimated hours field
            mock_act_hours_update_response,  # Update actual hours field
        ]

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            # Import the handler after patching
            from github_project_manager_mcp.handlers.task_handlers import (
                update_task_handler,
            )

            result = await update_task_handler(mock_arguments)

            assert result.isError is False
            assert len(result.content) == 1

            content = result.content[0].text
            assert "successfully updated" in content.lower()
            assert "Updated Task Title" in content
            assert (
                "title, description, status, priority, estimated_hours, actual_hours"
                in content
            )

    @pytest.mark.asyncio
    async def test_update_task_partial_fields(self):
        """Test updating only some task fields."""
        mock_arguments = {
            "task_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "title": "New Task Title",
            "status": "Done",
        }

        mock_client = AsyncMock()
        mock_content_response = {
            "node": {"content": {"id": "MDHI_lADOBQfyVc4AYzgCzgC5wQk"}}
        }

        mock_update_response = {
            "updateProjectV2DraftIssue": {
                "draftIssue": {
                    "id": "MDHI_lADOBQfyVc4AYzgCzgC5wQk",
                    "title": "New Task Title",
                    "body": "Original description",
                    "createdAt": "2025-01-01T10:00:00Z",
                    "updatedAt": "2025-01-01T12:00:00Z",
                    "projectV2Items": {
                        "nodes": [
                            {
                                "project": {
                                    "id": "PVT_kwDOBQfyVc0FoQ",
                                    "title": "Test Project",
                                }
                            }
                        ]
                    },
                }
            }
        }

        mock_fields_response = {
            "node": {
                "id": "PVTI_lADOBQfyVc0FoQzgBVgC",
                "project": {
                    "id": "PVT_kwDOBQfyVc0FoQ",
                    "fields": {
                        "nodes": [
                            {
                                "id": "FIELD_STATUS_ID",
                                "name": "Status",
                                "dataType": "SINGLE_SELECT",
                                "options": [
                                    {"id": "OPT_TODO", "name": "Todo"},
                                    {"id": "OPT_DONE", "name": "Done"},
                                ],
                            },
                        ]
                    },
                },
            }
        }

        mock_status_update_response = {
            "updateProjectV2ItemFieldValue": {
                "projectV2Item": {
                    "id": "PVTI_lADOBQfyVc0FoQzgBVgC",
                    "updatedAt": "2025-01-01T12:30:00Z",
                }
            }
        }

        mock_client.query.side_effect = [
            mock_content_response,
            mock_fields_response,
        ]
        mock_client.mutate.side_effect = [
            mock_update_response,
            mock_status_update_response,
        ]

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            from github_project_manager_mcp.handlers.task_handlers import (
                update_task_handler,
            )

            result = await update_task_handler(mock_arguments)

            assert result.isError is False
            content = result.content[0].text
            assert "New Task Title" in content
            assert "title, status" in content

    @pytest.mark.asyncio
    async def test_update_task_missing_item_id(self):
        """Test update_task with missing task_item_id."""
        mock_arguments = {"title": "New Title"}

        from github_project_manager_mcp.handlers.task_handlers import (
            update_task_handler,
        )

        result = await update_task_handler(mock_arguments)

        assert result.isError is True
        assert "task_item_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_update_task_empty_item_id(self):
        """Test update_task with empty task_item_id."""
        mock_arguments = {"task_item_id": "   ", "title": "New Title"}

        from github_project_manager_mcp.handlers.task_handlers import (
            update_task_handler,
        )

        result = await update_task_handler(mock_arguments)

        assert result.isError is True
        assert "task_item_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_update_task_no_updates_provided(self):
        """Test update_task when no update fields are provided."""
        mock_arguments = {"task_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC"}

        from github_project_manager_mcp.handlers.task_handlers import (
            update_task_handler,
        )

        result = await update_task_handler(mock_arguments)

        assert result.isError is True
        assert "at least one field to update" in result.content[0].text.lower()

    @pytest.mark.asyncio
    async def test_update_task_invalid_status(self):
        """Test update_task with invalid status value."""
        mock_arguments = {
            "task_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "status": "Invalid Status",
        }

        from github_project_manager_mcp.handlers.task_handlers import (
            update_task_handler,
        )

        result = await update_task_handler(mock_arguments)

        assert result.isError is True
        assert "invalid status" in result.content[0].text.lower()

    @pytest.mark.asyncio
    async def test_update_task_invalid_priority(self):
        """Test update_task with invalid priority value."""
        mock_arguments = {
            "task_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "priority": "Invalid Priority",
        }

        from github_project_manager_mcp.handlers.task_handlers import (
            update_task_handler,
        )

        result = await update_task_handler(mock_arguments)

        assert result.isError is True
        assert "invalid priority" in result.content[0].text.lower()

    @pytest.mark.asyncio
    async def test_update_task_invalid_estimated_hours(self):
        """Test update_task with invalid estimated_hours value."""
        mock_arguments = {
            "task_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "estimated_hours": -5,
        }

        from github_project_manager_mcp.handlers.task_handlers import (
            update_task_handler,
        )

        result = await update_task_handler(mock_arguments)

        assert result.isError is True
        assert "must be a positive integer" in result.content[0].text

    @pytest.mark.asyncio
    async def test_update_task_invalid_actual_hours(self):
        """Test update_task with invalid actual_hours value."""
        mock_arguments = {
            "task_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "actual_hours": "not_a_number",
        }

        from github_project_manager_mcp.handlers.task_handlers import (
            update_task_handler,
        )

        result = await update_task_handler(mock_arguments)

        assert result.isError is True
        assert "must be a positive integer" in result.content[0].text

    @pytest.mark.asyncio
    async def test_update_task_github_client_not_initialized(self):
        """Test update_task when GitHub client is not initialized."""
        mock_arguments = {
            "task_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "title": "New Title",
        }

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = None

            from github_project_manager_mcp.handlers.task_handlers import (
                update_task_handler,
            )

            result = await update_task_handler(mock_arguments)

            assert result.isError is True
            assert "not initialized" in result.content[0].text.lower()

    @pytest.mark.asyncio
    async def test_update_task_content_not_found(self):
        """Test update_task when task content is not found."""
        mock_arguments = {
            "task_item_id": "INVALID_ITEM_ID",
            "title": "New Title",
        }

        mock_client = AsyncMock()
        mock_response = {"node": {"content": None}}

        mock_client.query.return_value = mock_response

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            from github_project_manager_mcp.handlers.task_handlers import (
                update_task_handler,
            )

            result = await update_task_handler(mock_arguments)

            assert result.isError is True
            assert "does not have content" in result.content[0].text.lower()

    @pytest.mark.asyncio
    async def test_update_task_graphql_errors(self):
        """Test update_task with GraphQL API errors."""
        mock_arguments = {
            "task_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "title": "New Title",
        }

        mock_client = AsyncMock()
        mock_error_response = {
            "errors": [{"message": "Invalid task item ID"}],
        }

        mock_client.query.return_value = mock_error_response

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            from github_project_manager_mcp.handlers.task_handlers import (
                update_task_handler,
            )

            result = await update_task_handler(mock_arguments)

            assert result.isError is True
            assert "Invalid task item ID" in result.content[0].text

    @pytest.mark.asyncio
    async def test_update_task_field_not_found(self):
        """Test update_task when a field is not found in project."""
        mock_arguments = {
            "task_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "status": "In Progress",
        }

        mock_client = AsyncMock()

        # Only provide fields response since we're not updating content
        mock_fields_response = {
            "node": {
                "id": "PVTI_lADOBQfyVc0FoQzgBVgC",
                "project": {
                    "id": "PVT_kwDOBQfyVc0FoQ",
                    "fields": {"nodes": []},  # No fields found
                },
            }
        }

        mock_client.query.return_value = mock_fields_response

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            from github_project_manager_mcp.handlers.task_handlers import (
                update_task_handler,
            )

            result = await update_task_handler(mock_arguments)

            assert result.isError is True
            assert "status field not found" in result.content[0].text.lower()

    @pytest.mark.asyncio
    async def test_update_task_field_option_not_found(self):
        """Test update_task when status option is not found."""
        mock_arguments = {
            "task_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "status": "In Progress",  # Valid enum value but not in project options
        }

        mock_client = AsyncMock()

        # Only provide fields response since we're not updating content
        mock_fields_response = {
            "node": {
                "id": "PVTI_lADOBQfyVc0FoQzgBVgC",
                "project": {
                    "id": "PVT_kwDOBQfyVc0FoQ",
                    "fields": {
                        "nodes": [
                            {
                                "id": "FIELD_STATUS_ID",
                                "name": "Status",
                                "dataType": "SINGLE_SELECT",
                                "options": [
                                    {"id": "OPT_TODO", "name": "Todo"},
                                    {"id": "OPT_DONE", "name": "Done"},
                                    # Note: "In Progress" is not in the project's available options
                                ],
                            },
                        ]
                    },
                },
            }
        }

        mock_client.query.return_value = mock_fields_response

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            from github_project_manager_mcp.handlers.task_handlers import (
                update_task_handler,
            )

            result = await update_task_handler(mock_arguments)

            assert result.isError is True
            assert (
                "option" in result.content[0].text.lower()
                and "not found" in result.content[0].text.lower()
            )

    @pytest.mark.asyncio
    async def test_update_task_api_exception(self):
        """Test update_task with unexpected API exception."""
        mock_arguments = {
            "task_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "title": "New Title",
        }

        mock_client = AsyncMock()
        mock_client.query.side_effect = Exception("API connection failed")

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            from github_project_manager_mcp.handlers.task_handlers import (
                update_task_handler,
            )

            result = await update_task_handler(mock_arguments)

            assert result.isError is True
            assert "unexpected error" in result.content[0].text.lower()


class TestDeleteTaskHandler:
    """Test delete_task handler functionality."""

    @pytest.mark.asyncio
    async def test_delete_task_success(self):
        """Test successful task deletion."""
        mock_arguments = {
            "project_id": "PVT_kwDOBQfyVc0FoQ",
            "task_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "confirm": True,
        }

        mock_client = AsyncMock()
        mock_response = {
            "data": {
                "deleteProjectV2Item": {"deletedItemId": "PVTI_lADOBQfyVc0FoQzgBVgC"}
            }
        }

        mock_client.mutate.return_value = mock_response

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            from github_project_manager_mcp.handlers.task_handlers import (
                delete_task_handler,
            )

            result = await delete_task_handler(mock_arguments)

            assert result.isError is False
            assert "✅ Task successfully deleted" in result.content[0].text
            assert "PVTI_lADOBQfyVc0FoQzgBVgC" in result.content[0].text
            mock_client.mutate.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_task_missing_project_id(self):
        """Test delete_task with missing project_id."""
        mock_arguments = {
            "task_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "confirm": True,
        }

        from github_project_manager_mcp.handlers.task_handlers import (
            delete_task_handler,
        )

        result = await delete_task_handler(mock_arguments)

        assert result.isError is True
        assert "project_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_delete_task_empty_project_id(self):
        """Test delete_task with empty project_id."""
        mock_arguments = {
            "project_id": "   ",
            "task_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "confirm": True,
        }

        from github_project_manager_mcp.handlers.task_handlers import (
            delete_task_handler,
        )

        result = await delete_task_handler(mock_arguments)

        assert result.isError is True
        assert "project_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_delete_task_missing_task_item_id(self):
        """Test delete_task with missing task_item_id."""
        mock_arguments = {
            "project_id": "PVT_kwDOBQfyVc0FoQ",
            "confirm": True,
        }

        from github_project_manager_mcp.handlers.task_handlers import (
            delete_task_handler,
        )

        result = await delete_task_handler(mock_arguments)

        assert result.isError is True
        assert "task_item_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_delete_task_empty_task_item_id(self):
        """Test delete_task with empty task_item_id."""
        mock_arguments = {
            "project_id": "PVT_kwDOBQfyVc0FoQ",
            "task_item_id": "",
            "confirm": True,
        }

        from github_project_manager_mcp.handlers.task_handlers import (
            delete_task_handler,
        )

        result = await delete_task_handler(mock_arguments)

        assert result.isError is True
        assert "task_item_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_delete_task_missing_confirmation(self):
        """Test delete_task with missing confirmation."""
        mock_arguments = {
            "project_id": "PVT_kwDOBQfyVc0FoQ",
            "task_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
        }

        from github_project_manager_mcp.handlers.task_handlers import (
            delete_task_handler,
        )

        result = await delete_task_handler(mock_arguments)

        assert result.isError is True
        assert "must explicitly confirm" in result.content[0].text
        assert "cannot be undone" in result.content[0].text

    @pytest.mark.asyncio
    async def test_delete_task_confirmation_false(self):
        """Test delete_task with confirmation set to false."""
        mock_arguments = {
            "project_id": "PVT_kwDOBQfyVc0FoQ",
            "task_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "confirm": False,
        }

        from github_project_manager_mcp.handlers.task_handlers import (
            delete_task_handler,
        )

        result = await delete_task_handler(mock_arguments)

        assert result.isError is True
        assert "must explicitly confirm" in result.content[0].text
        assert "cannot be undone" in result.content[0].text

    @pytest.mark.asyncio
    async def test_delete_task_github_client_not_initialized(self):
        """Test delete_task when GitHub client is not initialized."""
        mock_arguments = {
            "project_id": "PVT_kwDOBQfyVc0FoQ",
            "task_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "confirm": True,
        }

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = None

            from github_project_manager_mcp.handlers.task_handlers import (
                delete_task_handler,
            )

            result = await delete_task_handler(mock_arguments)

            assert result.isError is True
            assert "not initialized" in result.content[0].text.lower()

    @pytest.mark.asyncio
    async def test_delete_task_graphql_errors(self):
        """Test delete_task with GraphQL API errors."""
        mock_arguments = {
            "project_id": "PVT_kwDOBQfyVc0FoQ",
            "task_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "confirm": True,
        }

        mock_client = AsyncMock()
        mock_error_response = {
            "errors": [{"message": "Task not found"}],
        }

        mock_client.mutate.return_value = mock_error_response

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            from github_project_manager_mcp.handlers.task_handlers import (
                delete_task_handler,
            )

            result = await delete_task_handler(mock_arguments)

            assert result.isError is True
            assert "Task not found" in result.content[0].text

    @pytest.mark.asyncio
    async def test_delete_task_no_deleted_item_id(self):
        """Test delete_task when no deleted item ID is returned."""
        mock_arguments = {
            "project_id": "PVT_kwDOBQfyVc0FoQ",
            "task_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "confirm": True,
        }

        mock_client = AsyncMock()
        mock_response = {"data": {"deleteProjectV2Item": {"deletedItemId": None}}}

        mock_client.mutate.return_value = mock_response

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            from github_project_manager_mcp.handlers.task_handlers import (
                delete_task_handler,
            )

            result = await delete_task_handler(mock_arguments)

            assert result.isError is True
            assert "Failed to delete task" in result.content[0].text
            assert "no deleted item ID returned" in result.content[0].text

    @pytest.mark.asyncio
    async def test_delete_task_api_exception(self):
        """Test delete_task with API exception."""
        mock_arguments = {
            "project_id": "PVT_kwDOBQfyVc0FoQ",
            "task_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "confirm": True,
        }

        mock_client = AsyncMock()
        mock_client.mutate.side_effect = Exception("API Connection Failed")

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            from github_project_manager_mcp.handlers.task_handlers import (
                delete_task_handler,
            )

            result = await delete_task_handler(mock_arguments)

            assert result.isError is True
            assert "Error deleting task" in result.content[0].text

    @pytest.mark.asyncio
    async def test_delete_task_direct_response_format(self):
        """Test delete_task with direct response format (no nested data key)."""
        mock_arguments = {
            "project_id": "PVT_kwDOBQfyVc0FoQ",
            "task_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "confirm": True,
        }

        mock_client = AsyncMock()
        mock_response = {
            "deleteProjectV2Item": {"deletedItemId": "PVTI_lADOBQfyVc0FoQzgBVgC"}
        }

        mock_client.mutate.return_value = mock_response

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            from github_project_manager_mcp.handlers.task_handlers import (
                delete_task_handler,
            )

            result = await delete_task_handler(mock_arguments)

            assert result.isError is False
            assert "✅ Task successfully deleted" in result.content[0].text
            assert "PVTI_lADOBQfyVc0FoQzgBVgC" in result.content[0].text


class TestCompleteTaskHandler:
    """Test cases for the complete_task_handler function."""

    @pytest.mark.asyncio
    async def test_complete_task_success(self):
        """Test successful task completion."""
        mock_client = AsyncMock()

        # Mock successful fields response showing current status and project info
        mock_fields_response = {
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
                                "options": [
                                    {"id": "OPT_TODO", "name": "Todo"},
                                    {"id": "OPT_IN_PROGRESS", "name": "In Progress"},
                                    {"id": "OPT_DONE", "name": "Done"},
                                ],
                            },
                        ]
                    },
                },
                "fieldValues": {
                    "nodes": [
                        {
                            "field": {"name": "Status"},
                            "optionId": "OPT_IN_PROGRESS",
                            "singleSelectOption": {"name": "In Progress"},
                        }
                    ]
                },
            }
        }

        # Mock successful update response
        mock_update_response = {
            "updateProjectV2ItemFieldValue": {
                "projectV2Item": {
                    "id": "PVTI_task123",
                    "updatedAt": "2024-01-01T10:30:00Z",
                }
            }
        }

        mock_client.query.return_value = mock_fields_response
        mock_client.mutate.return_value = mock_update_response

        with patch(
            "src.github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await complete_task_handler(
                {
                    "task_item_id": "PVTI_task123",
                }
            )

        assert not result.isError
        assert "Task completed successfully!" in result.content[0].text
        assert "PVTI_task123" in result.content[0].text
        assert "**New Status:** Done" in result.content[0].text

    @pytest.mark.asyncio
    async def test_complete_task_already_complete(self):
        """Test completing a task that is already complete."""
        mock_client = AsyncMock()

        # Mock response with already complete task
        mock_fields_response = {
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
                                "options": [
                                    {"id": "OPT_TODO", "name": "Todo"},
                                    {"id": "OPT_IN_PROGRESS", "name": "In Progress"},
                                    {"id": "OPT_DONE", "name": "Done"},
                                ],
                            },
                        ]
                    },
                },
                "fieldValues": {
                    "nodes": [
                        {
                            "field": {"name": "Status"},
                            "optionId": "OPT_DONE",
                            "singleSelectOption": {"name": "Done"},
                        }
                    ]
                },
            }
        }

        mock_client.query.return_value = mock_fields_response

        with patch(
            "src.github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await complete_task_handler(
                {
                    "task_item_id": "PVTI_task123",
                }
            )

        assert not result.isError
        assert "Task is already complete!" in result.content[0].text
        assert "**Status:** Done" in result.content[0].text

    @pytest.mark.asyncio
    async def test_complete_task_missing_task_item_id(self):
        """Test error handling when task_item_id is missing."""
        result = await complete_task_handler({})

        assert result.isError
        assert "task_item_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_complete_task_empty_task_item_id(self):
        """Test error handling when task_item_id is empty."""
        result = await complete_task_handler(
            {
                "task_item_id": "   ",
            }
        )

        assert result.isError
        assert "task_item_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_complete_task_github_client_not_initialized(self):
        """Test error handling when GitHub client is not initialized."""
        with patch(
            "src.github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=None,
        ):
            result = await complete_task_handler(
                {
                    "task_item_id": "PVTI_task123",
                }
            )

        assert result.isError
        assert "GitHub client not initialized" in result.content[0].text

    @pytest.mark.asyncio
    async def test_complete_task_not_found(self):
        """Test error handling when task is not found."""
        mock_client = AsyncMock()
        mock_response = {"node": None}
        mock_client.query.return_value = mock_response

        with patch(
            "src.github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await complete_task_handler(
                {
                    "task_item_id": "PVTI_invalid",
                }
            )

        assert result.isError
        assert "Task not found" in result.content[0].text

    @pytest.mark.asyncio
    async def test_complete_task_no_status_field(self):
        """Test error handling when task has no status field."""
        mock_client = AsyncMock()
        mock_response = {
            "node": {
                "id": "PVTI_task123",
                "project": {
                    "id": "PVT_project123",
                    "fields": {
                        "nodes": [
                            {
                                "id": "FIELD_PRIORITY_ID",
                                "name": "Priority",
                                "dataType": "SINGLE_SELECT",
                                "options": [
                                    {"id": "OPT_LOW", "name": "Low"},
                                    {"id": "OPT_HIGH", "name": "High"},
                                ],
                            },
                        ]
                    },
                },
                "fieldValues": {"nodes": []},
            }
        }
        mock_client.query.return_value = mock_response

        with patch(
            "src.github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await complete_task_handler(
                {
                    "task_item_id": "PVTI_task123",
                }
            )

        assert result.isError
        assert "Status field not found" in result.content[0].text

    @pytest.mark.asyncio
    async def test_complete_task_graphql_query_error(self):
        """Test error handling when GraphQL query fails."""
        mock_client = AsyncMock()
        mock_client.query.side_effect = Exception(
            "GraphQL query error: Invalid task ID"
        )

        with patch(
            "src.github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await complete_task_handler(
                {
                    "task_item_id": "PVTI_invalid",
                }
            )

        assert result.isError
        assert "Failed to fetch task status" in result.content[0].text
        assert "GraphQL query error: Invalid task ID" in result.content[0].text

    @pytest.mark.asyncio
    async def test_complete_task_update_mutation_error(self):
        """Test error handling when update mutation fails."""
        mock_client = AsyncMock()

        # Mock successful query response
        mock_fields_response = {
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
                                "options": [
                                    {"id": "OPT_TODO", "name": "Todo"},
                                    {"id": "OPT_IN_PROGRESS", "name": "In Progress"},
                                    {"id": "OPT_DONE", "name": "Done"},
                                ],
                            },
                        ]
                    },
                },
                "fieldValues": {
                    "nodes": [
                        {
                            "field": {"name": "Status"},
                            "optionId": "OPT_IN_PROGRESS",
                            "singleSelectOption": {"name": "In Progress"},
                        }
                    ]
                },
            }
        }

        mock_client.query.return_value = mock_fields_response
        mock_client.mutate.side_effect = Exception(
            "GraphQL mutation error: Permission denied"
        )

        with patch(
            "src.github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await complete_task_handler(
                {
                    "task_item_id": "PVTI_task123",
                }
            )

        assert result.isError
        assert "Failed to fetch task status" in result.content[0].text
        assert "GraphQL mutation error: Permission denied" in result.content[0].text

    @pytest.mark.asyncio
    async def test_complete_task_no_update_response(self):
        """Test error handling when update mutation returns no response."""
        mock_client = AsyncMock()

        # Mock successful query response
        mock_fields_response = {
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
                                "options": [
                                    {"id": "OPT_TODO", "name": "Todo"},
                                    {"id": "OPT_IN_PROGRESS", "name": "In Progress"},
                                    {"id": "OPT_DONE", "name": "Done"},
                                ],
                            },
                        ]
                    },
                },
                "fieldValues": {
                    "nodes": [
                        {
                            "field": {"name": "Status"},
                            "optionId": "OPT_IN_PROGRESS",
                            "singleSelectOption": {"name": "In Progress"},
                        }
                    ]
                },
            }
        }

        mock_client.query.return_value = mock_fields_response
        mock_client.mutate.return_value = None

        with patch(
            "src.github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await complete_task_handler(
                {
                    "task_item_id": "PVTI_task123",
                }
            )

        assert result.isError
        assert (
            "No response data received from completion operation"
            in result.content[0].text
        )

    @pytest.mark.asyncio
    async def test_complete_task_invalid_update_response_format(self):
        """Test error handling when update response format is unexpected."""
        mock_client = AsyncMock()

        # Mock successful query response
        mock_fields_response = {
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
                                "options": [
                                    {"id": "OPT_TODO", "name": "Todo"},
                                    {"id": "OPT_IN_PROGRESS", "name": "In Progress"},
                                    {"id": "OPT_DONE", "name": "Done"},
                                ],
                            },
                        ]
                    },
                },
                "fieldValues": {
                    "nodes": [
                        {
                            "field": {"name": "Status"},
                            "optionId": "OPT_IN_PROGRESS",
                            "singleSelectOption": {"name": "In Progress"},
                        }
                    ]
                },
            }
        }

        mock_client.query.return_value = mock_fields_response
        mock_client.mutate.return_value = {"unexpected": "format"}

        with patch(
            "src.github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await complete_task_handler(
                {
                    "task_item_id": "PVTI_task123",
                }
            )

        assert result.isError
        assert (
            "Invalid response format from completion operation"
            in result.content[0].text
        )

    @pytest.mark.asyncio
    async def test_complete_task_api_exception(self):
        """Test error handling for general API exceptions."""
        mock_client = AsyncMock()
        mock_client.query.side_effect = RuntimeError("Network timeout")

        with patch(
            "src.github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await complete_task_handler(
                {
                    "task_item_id": "PVTI_task123",
                }
            )

        assert result.isError
        assert "Failed to fetch task status" in result.content[0].text
        assert "Network timeout" in result.content[0].text

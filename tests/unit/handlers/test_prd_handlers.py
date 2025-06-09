"""
Unit tests for PRD (Product Requirements Document) handlers.

This module provides comprehensive test coverage for PRD management
operations in GitHub Projects v2.
"""

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from github_project_manager_mcp.handlers.prd_handlers import (
    PRD_TOOL_HANDLERS,
    PRD_TOOLS,
    add_prd_to_project_handler,
    list_prds_in_project_handler,
    update_prd_handler,
)


class TestAddPRDToProjectTool:
    """Test cases for add_prd_to_project MCP tool."""

    def test_tool_definition(self):
        """Test that add_prd_to_project tool is properly defined."""
        add_prd_tool = None
        for tool in PRD_TOOLS:
            if tool.name == "add_prd_to_project":
                add_prd_tool = tool
                break

        assert (
            add_prd_tool is not None
        ), "add_prd_to_project tool not found in PRD_TOOLS"
        assert add_prd_tool.description is not None
        assert (
            "PRD" in add_prd_tool.description
            or "Product Requirements Document" in add_prd_tool.description
        )

        # Check input schema
        assert add_prd_tool.inputSchema is not None
        schema = add_prd_tool.inputSchema
        assert schema.get("type") == "object"

        # Required fields
        required = schema.get("required", [])
        assert "project_id" in required
        assert "title" in required

        # Properties
        properties = schema.get("properties", {})
        assert "project_id" in properties
        assert "title" in properties
        assert "description" in properties
        assert "status" in properties
        assert "priority" in properties

    @pytest.mark.asyncio
    async def test_add_prd_to_project_success(self):
        """Test successful PRD addition to project."""
        mock_arguments = {
            "project_id": "PVT_kwDOBQfyVc0FoQ",
            "title": "User Authentication System",
            "description": "Implement OAuth 2.0 authentication with Google and GitHub providers",
            "status": "In Progress",
            "priority": "High",
        }

        # Mock GitHub client and response
        mock_client = AsyncMock()
        mock_response = {
            "data": {
                "addProjectV2DraftIssue": {
                    "projectItem": {
                        "id": "PVTI_lADOBQfyVc0FoQzgBVgC",
                        "title": "User Authentication System",
                        "body": "Implement OAuth 2.0 authentication with Google and GitHub providers",
                        "createdAt": "2025-01-01T12:00:00Z",
                        "updatedAt": "2025-01-01T12:00:00Z",
                        "position": 1,
                        "archived": False,
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
                            ]
                        },
                    }
                }
            }
        }

        mock_client.mutate.return_value = mock_response

        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            result = await add_prd_to_project_handler(mock_arguments)

            assert result.isError is False
            assert len(result.content) == 1

            content = result.content[0].text
            assert "successfully added" in content.lower()
            assert "User Authentication System" in content
            assert "PVTI_lADOBQfyVc0FoQzgBVgC" in content
            assert "In Progress" in content
            assert "High" in content

    @pytest.mark.asyncio
    async def test_add_prd_to_project_missing_required_params(self):
        """Test add_prd_to_project with missing required parameters."""
        test_cases = [
            # Missing project_id
            {"title": "Test PRD", "description": "Test description"},
            # Missing title
            {"project_id": "PVT_kwDOBQfyVc0FoQ", "description": "Test description"},
            # Empty project_id
            {"project_id": "", "title": "Test PRD"},
            # Empty title
            {"project_id": "PVT_kwDOBQfyVc0FoQ", "title": ""},
        ]

        for args in test_cases:
            result = await add_prd_to_project_handler(args)

            assert result.isError is True
            assert len(result.content) == 1
            assert (
                "required" in result.content[0].text.lower()
                or "missing" in result.content[0].text.lower()
            )

    @pytest.mark.asyncio
    async def test_add_prd_to_project_invalid_status(self):
        """Test add_prd_to_project with invalid status value."""
        mock_arguments = {
            "project_id": "PVT_kwDOBQfyVc0FoQ",
            "title": "Test PRD",
            "description": "Test description",
            "status": "Invalid Status",
        }

        result = await add_prd_to_project_handler(mock_arguments)

        assert result.isError is True
        assert "invalid status" in result.content[0].text.lower()

    @pytest.mark.asyncio
    async def test_add_prd_to_project_invalid_priority(self):
        """Test add_prd_to_project with invalid priority value."""
        mock_arguments = {
            "project_id": "PVT_kwDOBQfyVc0FoQ",
            "title": "Test PRD",
            "description": "Test description",
            "priority": "Invalid Priority",
        }

        result = await add_prd_to_project_handler(mock_arguments)

        assert result.isError is True
        assert "invalid priority" in result.content[0].text.lower()

    @pytest.mark.asyncio
    async def test_add_prd_to_project_with_defaults(self):
        """Test add_prd_to_project with default status and priority."""
        mock_arguments = {
            "project_id": "PVT_kwDOBQfyVc0FoQ",
            "title": "Simple PRD",
            "description": "Basic PRD with defaults",
        }

        # Mock GitHub client and response
        mock_client = AsyncMock()
        mock_response = {
            "data": {
                "addProjectV2DraftIssue": {
                    "projectItem": {
                        "id": "PVTI_lADOBQfyVc0FoQzgBVgD",
                        "title": "Simple PRD",
                        "body": "Basic PRD with defaults",
                        "createdAt": "2025-01-01T12:00:00Z",
                        "fieldValues": {"nodes": []},
                    }
                }
            }
        }

        mock_client.mutate.return_value = mock_response

        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            result = await add_prd_to_project_handler(mock_arguments)

            assert result.isError is False
            assert "Simple PRD" in result.content[0].text
            # Should use defaults: Backlog status, Medium priority
            content = result.content[0].text
            assert "Backlog" in content or "Medium" in content  # Defaults applied

    @pytest.mark.asyncio
    async def test_add_prd_to_project_client_not_initialized(self):
        """Test add_prd_to_project when GitHub client is not initialized."""
        mock_arguments = {"project_id": "PVT_kwDOBQfyVc0FoQ", "title": "Test PRD"}

        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = None

            result = await add_prd_to_project_handler(mock_arguments)

            assert result.isError is True
            assert "not initialized" in result.content[0].text.lower()

    @pytest.mark.asyncio
    async def test_add_prd_to_project_invalid_project_id(self):
        """Test add_prd_to_project with invalid project ID format."""
        mock_arguments = {"project_id": "invalid-project-id", "title": "Test PRD"}

        mock_client = AsyncMock()
        mock_client.mutate.side_effect = Exception("Invalid project ID format")

        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            result = await add_prd_to_project_handler(mock_arguments)

            assert result.isError is True
            assert "error" in result.content[0].text.lower()

    @pytest.mark.asyncio
    async def test_add_prd_to_project_api_error(self):
        """Test add_prd_to_project with API error response."""
        mock_arguments = {"project_id": "PVT_kwDOBQfyVc0FoQ", "title": "Test PRD"}

        mock_client = AsyncMock()
        mock_error_response = {
            "errors": [{"message": "Project not found", "type": "NOT_FOUND"}]
        }
        mock_client.mutate.return_value = mock_error_response

        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            result = await add_prd_to_project_handler(mock_arguments)

            assert result.isError is True
            assert "Project not found" in result.content[0].text

    @pytest.mark.asyncio
    async def test_add_prd_to_project_with_acceptance_criteria(self):
        """Test add_prd_to_project with acceptance criteria and technical requirements."""
        mock_arguments = {
            "project_id": "PVT_kwDOBQfyVc0FoQ",
            "title": "Advanced PRD",
            "description": "Complex feature implementation",
            "acceptance_criteria": "Given user clicks login, when credentials are valid, then user is authenticated",
            "technical_requirements": "React frontend, Node.js backend, PostgreSQL database",
            "business_value": "Increase user retention by 25%",
            "status": "This Sprint",
            "priority": "Critical",
        }

        # Mock GitHub client and response
        mock_client = AsyncMock()
        mock_response = {
            "data": {
                "addProjectV2DraftIssue": {
                    "projectItem": {
                        "id": "PVTI_lADOBQfyVc0FoQzgBVgE",
                        "title": "Advanced PRD",
                        "body": "Complex feature implementation\n\n**Acceptance Criteria:**\nGiven user clicks login, when credentials are valid, then user is authenticated\n\n**Technical Requirements:**\nReact frontend, Node.js backend, PostgreSQL database\n\n**Business Value:**\nIncrease user retention by 25%",
                        "createdAt": "2025-01-01T12:00:00Z",
                        "fieldValues": {
                            "nodes": [
                                {
                                    "field": {"name": "Status"},
                                    "singleSelectOption": {"name": "This Sprint"},
                                },
                                {
                                    "field": {"name": "Priority"},
                                    "singleSelectOption": {"name": "Critical"},
                                },
                            ]
                        },
                    }
                }
            }
        }

        mock_client.mutate.return_value = mock_response

        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            result = await add_prd_to_project_handler(mock_arguments)

            assert result.isError is False
            content = result.content[0].text
            assert "Advanced PRD" in content
            assert "This Sprint" in content
            assert "Critical" in content
            assert "Acceptance Criteria" in content or "acceptance criteria" in content


class TestPRDHandlerRegistration:
    """Test cases for PRD handler registration and tool definitions."""

    def test_prd_tools_list(self):
        """Test that PRD_TOOLS contains expected tools."""
        tool_names = [tool.name for tool in PRD_TOOLS]

        assert "add_prd_to_project" in tool_names
        assert "list_prds_in_project" in tool_names
        assert "delete_prd_from_project" in tool_names
        assert "update_prd" in tool_names
        assert "update_prd_status" in tool_names
        assert "complete_prd" in tool_names
        assert (
            len(PRD_TOOLS) == 6
        )  # add_prd, list_prds, delete_prd, update_prd, update_prd_status, complete_prd

        # Verify all tools have required attributes
        for tool in PRD_TOOLS:
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "inputSchema")
            assert tool.name is not None
            assert tool.description is not None
            assert tool.inputSchema is not None

    def test_prd_tool_handlers_mapping(self):
        """Test that PRD_TOOL_HANDLERS contains handlers for all tools."""
        tool_names = [tool.name for tool in PRD_TOOLS]
        handler_names = list(PRD_TOOL_HANDLERS.keys())

        # All tools should have corresponding handlers
        for tool_name in tool_names:
            assert tool_name in handler_names, f"No handler found for tool: {tool_name}"

        # All handlers should be callable
        for handler_name, handler_func in PRD_TOOL_HANDLERS.items():
            assert callable(handler_func), f"Handler {handler_name} is not callable"

    def test_add_prd_to_project_handler_exists(self):
        """Test that add_prd_to_project handler is properly registered."""
        assert "add_prd_to_project" in PRD_TOOL_HANDLERS
        handler = PRD_TOOL_HANDLERS["add_prd_to_project"]
        assert handler == add_prd_to_project_handler

    def test_list_prds_in_project_handler_exists(self):
        """Test that list_prds_in_project handler is properly registered."""
        assert "list_prds_in_project" in PRD_TOOL_HANDLERS
        handler = PRD_TOOL_HANDLERS["list_prds_in_project"]
        assert handler == list_prds_in_project_handler

    def test_update_prd_handler_exists(self):
        """Test that update_prd handler is properly registered."""
        assert "update_prd" in PRD_TOOL_HANDLERS
        handler = PRD_TOOL_HANDLERS["update_prd"]
        assert handler == update_prd_handler


class TestListPrdsInProjectHandler:
    """Test cases for list_prds_in_project_handler."""

    @pytest.mark.asyncio
    async def test_list_prds_success_with_draft_issues(self):
        """Test successful PRD listing with draft issues."""
        # Mock successful query response with draft issues
        mock_result = {
            "node": {
                "title": "Test Project",
                "items": {
                    "totalCount": 2,
                    "pageInfo": {
                        "hasNextPage": False,
                        "hasPreviousPage": False,
                        "startCursor": "cursor_start",
                        "endCursor": "cursor_end",
                    },
                    "nodes": [
                        {
                            "id": "PVTI_kwDOBQfyVc0FoQ1",
                            "createdAt": "2024-01-15T10:00:00Z",
                            "updatedAt": "2024-01-15T11:00:00Z",
                            "content": {
                                "id": "DI_kwDOBQfyVc0FoQ1",
                                "title": "User Authentication System",
                                "body": "Implement comprehensive user authentication with OAuth support",
                                "createdAt": "2024-01-15T10:00:00Z",
                                "updatedAt": "2024-01-15T11:00:00Z",
                                "assignees": {
                                    "totalCount": 1,
                                    "nodes": [
                                        {"login": "testuser", "name": "Test User"}
                                    ],
                                },
                            },
                            "fieldValues": {
                                "nodes": [
                                    {
                                        "text": "High",
                                        "field": {"name": "Priority"},
                                    },
                                    {
                                        "name": "In Progress",
                                        "field": {"name": "Status"},
                                    },
                                ]
                            },
                        },
                        {
                            "id": "PVTI_kwDOBQfyVc0FoQ2",
                            "createdAt": "2024-01-15T12:00:00Z",
                            "updatedAt": "2024-01-15T13:00:00Z",
                            "content": {
                                "id": "DI_kwDOBQfyVc0FoQ2",
                                "title": "API Documentation System",
                                "body": "Create comprehensive API documentation with examples",
                                "createdAt": "2024-01-15T12:00:00Z",
                                "updatedAt": "2024-01-15T13:00:00Z",
                                "assignees": {"totalCount": 0, "nodes": []},
                            },
                            "fieldValues": {
                                "nodes": [
                                    {
                                        "text": "Medium",
                                        "field": {"name": "Priority"},
                                    }
                                ]
                            },
                        },
                    ],
                },
            }
        }

        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.query.return_value = mock_result

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await list_prds_in_project_handler(
                {"project_id": "PVT_kwDOBQfyVc0FoQ"}
            )

            # Verify result
            assert not result.isError
            assert len(result.content) == 1
            response_text = result.content[0].text

            assert "📋 **PRDs in Project: Test Project**" in response_text
            assert "**Total Items:** 2" in response_text
            assert "**PRDs Found:** 2" in response_text
            assert "**1. User Authentication System**" in response_text
            assert "**2. API Documentation System**" in response_text
            assert "- **Type:** Draft Issue" in response_text
            assert "- **Priority:** High" in response_text
            assert "- **Status:** In Progress" in response_text
            assert "- **Assignees:** Test User (@testuser)" in response_text

            # Verify query was called with correct parameters
            mock_client.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_prds_success_with_regular_issues(self):
        """Test successful PRD listing with regular issues."""
        mock_result = {
            "node": {
                "title": "Test Project",
                "items": {
                    "totalCount": 1,
                    "pageInfo": {
                        "hasNextPage": False,
                        "hasPreviousPage": False,
                        "startCursor": "cursor_start",
                        "endCursor": "cursor_end",
                    },
                    "nodes": [
                        {
                            "id": "PVTI_kwDOBQfyVc0FoQ1",
                            "createdAt": "2024-01-15T10:00:00Z",
                            "updatedAt": "2024-01-15T11:00:00Z",
                            "content": {
                                "id": "I_kwDOBQfyVc0FoQ1",
                                "title": "Mobile App Development",
                                "body": "Develop cross-platform mobile application",
                                "number": 123,
                                "state": "OPEN",
                                "createdAt": "2024-01-15T10:00:00Z",
                                "updatedAt": "2024-01-15T11:00:00Z",
                                "assignees": {"totalCount": 0, "nodes": []},
                                "repository": {
                                    "name": "test-repo",
                                    "owner": {"login": "testorg"},
                                },
                            },
                            "fieldValues": {"nodes": []},
                        }
                    ],
                },
            }
        }

        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.query.return_value = mock_result

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await list_prds_in_project_handler(
                {"project_id": "PVT_kwDOBQfyVc0FoQ"}
            )

            # Verify result
            assert not result.isError
            response_text = result.content[0].text

            assert "**1. Mobile App Development**" in response_text
            assert "- **Type:** Issue" in response_text
            assert "- **Number:** 123" in response_text
            assert "- **State:** OPEN" in response_text
            assert "- **Repository:** testorg/test-repo" in response_text

    @pytest.mark.asyncio
    async def test_list_prds_success_empty_project(self):
        """Test successful PRD listing with empty project."""
        mock_result = {
            "node": {
                "title": "Empty Project",
                "items": {
                    "totalCount": 0,
                    "pageInfo": {
                        "hasNextPage": False,
                        "hasPreviousPage": False,
                        "startCursor": None,
                        "endCursor": None,
                    },
                    "nodes": [],
                },
            }
        }

        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.query.return_value = mock_result

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await list_prds_in_project_handler(
                {"project_id": "PVT_kwDOBQfyVc0FoQ"}
            )

            # Verify result
            assert not result.isError
            response_text = result.content[0].text

            assert "📋 **PRDs in Project: Empty Project**" in response_text
            assert "**Total Items:** 0" in response_text
            assert "**PRDs Found:** 0" in response_text
            assert "No PRDs found in this project." in response_text

    @pytest.mark.asyncio
    async def test_list_prds_success_with_pagination(self):
        """Test successful PRD listing with pagination info."""
        mock_result = {
            "node": {
                "title": "Test Project",
                "items": {
                    "totalCount": 50,
                    "pageInfo": {
                        "hasNextPage": True,
                        "hasPreviousPage": False,
                        "startCursor": "cursor_start",
                        "endCursor": "cursor_end_123",
                    },
                    "nodes": [
                        {
                            "id": "PVTI_kwDOBQfyVc0FoQ1",
                            "createdAt": "2024-01-15T10:00:00Z",
                            "updatedAt": "2024-01-15T11:00:00Z",
                            "content": {
                                "id": "DI_kwDOBQfyVc0FoQ1",
                                "title": "Test PRD",
                                "body": "Short description",
                                "createdAt": "2024-01-15T10:00:00Z",
                                "updatedAt": "2024-01-15T11:00:00Z",
                                "assignees": {"totalCount": 0, "nodes": []},
                            },
                            "fieldValues": {"nodes": []},
                        }
                    ],
                },
            }
        }

        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.query.return_value = mock_result

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await list_prds_in_project_handler(
                {"project_id": "PVT_kwDOBQfyVc0FoQ", "first": 10}
            )

            # Verify result
            assert not result.isError
            response_text = result.content[0].text

            assert "**Pagination Info:**" in response_text
            assert "- Has next page (use after: 'cursor_end_123')" in response_text

    @pytest.mark.asyncio
    async def test_list_prds_missing_project_id(self):
        """Test error when project_id is missing."""
        result = await list_prds_in_project_handler({})

        assert result.isError
        assert len(result.content) == 1
        assert (
            "Error: project_id is required to list PRDs in project"
            in result.content[0].text
        )

    @pytest.mark.asyncio
    async def test_list_prds_invalid_first_parameter(self):
        """Test error when first parameter is invalid."""
        result = await list_prds_in_project_handler(
            {"project_id": "PVT_kwDOBQfyVc0FoQ", "first": "invalid"}
        )

        assert result.isError
        assert (
            "Error: 'first' parameter must be a positive integer between 1 and 100"
            in result.content[0].text
        )

    @pytest.mark.asyncio
    async def test_list_prds_first_parameter_out_of_range(self):
        """Test error when first parameter is out of range."""
        result = await list_prds_in_project_handler(
            {"project_id": "PVT_kwDOBQfyVc0FoQ", "first": 150}
        )

        assert result.isError
        assert (
            "Error: 'first' parameter must be a positive integer between 1 and 100"
            in result.content[0].text
        )

    @pytest.mark.asyncio
    async def test_list_prds_github_client_not_initialized(self):
        """Test error when GitHub client is not initialized."""
        # Patch get_github_client to return None
        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=None,
        ):
            result = await list_prds_in_project_handler(
                {"project_id": "PVT_kwDOBQfyVc0FoQ"}
            )

            assert result.isError
            assert "Error: GitHub client not initialized" in result.content[0].text

    @pytest.mark.asyncio
    async def test_list_prds_github_api_error(self):
        """Test handling of GitHub API errors."""
        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.query.side_effect = Exception("API rate limit exceeded")

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await list_prds_in_project_handler(
                {"project_id": "PVT_kwDOBQfyVc0FoQ"}
            )

            assert result.isError
            assert (
                "Error listing PRDs in project: API rate limit exceeded"
                in result.content[0].text
            )

    @pytest.mark.asyncio
    async def test_list_prds_graphql_errors(self):
        """Test handling of GraphQL errors in response."""
        mock_result = {
            "errors": [
                {"message": "Project not found"},
                {"message": "Access denied"},
            ]
        }

        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.query.return_value = mock_result

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await list_prds_in_project_handler(
                {"project_id": "PVT_kwDOBQfyVc0FoQ"}
            )

            assert result.isError
            assert (
                "Error listing PRDs: GraphQL errors: Project not found; Access denied"
                in result.content[0].text
            )

    @pytest.mark.asyncio
    async def test_list_prds_project_not_found(self):
        """Test handling when project is not found."""
        mock_result = {"node": None}

        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.query.return_value = mock_result

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await list_prds_in_project_handler(
                {"project_id": "PVT_kwDOBQfyVc0FoQ"}
            )

            assert result.isError
            assert (
                "Error: Project with ID 'PVT_kwDOBQfyVc0FoQ' not found or not accessible"
                in result.content[0].text
            )

    @pytest.mark.asyncio
    async def test_list_prds_with_long_description(self):
        """Test PRD listing with long description that gets truncated."""
        long_description = "This is a very long PRD description that should be truncated when displayed in the list view to keep the output manageable and readable for users."

        mock_result = {
            "node": {
                "title": "Test Project",
                "items": {
                    "totalCount": 1,
                    "pageInfo": {
                        "hasNextPage": False,
                        "hasPreviousPage": False,
                        "startCursor": "cursor_start",
                        "endCursor": "cursor_end",
                    },
                    "nodes": [
                        {
                            "id": "PVTI_kwDOBQfyVc0FoQ1",
                            "createdAt": "2024-01-15T10:00:00Z",
                            "updatedAt": "2024-01-15T11:00:00Z",
                            "content": {
                                "id": "DI_kwDOBQfyVc0FoQ1",
                                "title": "Long Description PRD",
                                "body": long_description,
                                "createdAt": "2024-01-15T10:00:00Z",
                                "updatedAt": "2024-01-15T11:00:00Z",
                                "assignees": {"totalCount": 0, "nodes": []},
                            },
                            "fieldValues": {"nodes": []},
                        }
                    ],
                },
            }
        }

        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.query.return_value = mock_result

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await list_prds_in_project_handler(
                {"project_id": "PVT_kwDOBQfyVc0FoQ"}
            )

            # Verify result
            assert not result.isError
            response_text = result.content[0].text

            # Check that description is truncated (first 100 chars + "...")
            expected_truncated = long_description[:100] + "..."
            assert expected_truncated in response_text


class TestUpdatePrdHandler:
    """Test cases for update_prd_handler."""

    @pytest.mark.asyncio
    async def test_update_prd_success(self):
        """Test successful PRD update with all fields."""
        # Mock content ID query response
        mock_content_response = {
            "data": {"node": {"content": {"id": "MDHI_lADOBQfyVc4AYzgCzgC5wQk"}}}
        }

        # Mock successful update response
        mock_update_result = {
            "data": {
                "updateProjectV2DraftIssue": {
                    "draftIssue": {
                        "id": "MDHI_lADOBQfyVc4AYzgCzgC5wQk",
                        "title": "Updated Test PRD",
                        "body": "Updated comprehensive PRD description\n\n## Acceptance Criteria\nUpdated acceptance criteria\n\n## Technical Requirements\nUpdated technical requirements\n\n## Business Value\nUpdated business value",
                        "createdAt": "2024-01-15T10:00:00Z",
                        "updatedAt": "2024-01-15T11:30:00Z",
                        "assignees": {
                            "totalCount": 1,
                            "nodes": [
                                {
                                    "id": "MDQ6VXNlcjEyMzQ1",
                                    "login": "testuser",
                                    "name": "Test User",
                                }
                            ],
                        },
                        "projectV2Items": {
                            "totalCount": 1,
                            "nodes": [
                                {
                                    "id": "PVTI_kwDOBQfyVc0FoQ",
                                    "project": {
                                        "id": "PVT_kwDOBQfyVc0FoQ",
                                        "title": "Test Project",
                                    },
                                }
                            ],
                        },
                    }
                }
            }
        }

        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.query.return_value = mock_content_response
        mock_client.mutate.return_value = mock_update_result

        # Test with all update fields
        arguments = {
            "prd_item_id": "PVTI_kwDOBQfyVc0FoQ",
            "title": "Updated Test PRD",
            "body": "Updated comprehensive PRD description",
            "assignee_ids": ["MDQ6VXNlcjEyMzQ1"],
        }

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await update_prd_handler(arguments)

            # Verify both query and mutate were called
            mock_client.query.assert_called_once()
            mock_client.mutate.assert_called_once()

            # Check the content ID query
            query_args = mock_client.query.call_args[0][0]
            assert "PVTI_kwDOBQfyVc0FoQ" in query_args
            assert "DraftIssue" in query_args

            # Check the update mutation
            mutation_args = mock_client.mutate.call_args[0][0]
            assert "updateProjectV2DraftIssue" in mutation_args
            assert "MDHI_lADOBQfyVc4AYzgCzgC5wQk" in mutation_args  # The content ID
            assert "Updated Test PRD" in mutation_args
            assert "Updated comprehensive PRD description" in mutation_args

            # Verify success response
            assert not result.isError
            assert len(result.content) == 1
            response_text = result.content[0].text
            assert "✅ PRD successfully updated!" in response_text
            assert "Updated Test PRD" in response_text
            assert "**Updated:** 2024-01-15T11:30:00Z" in response_text
            assert "testuser" in response_text

    @pytest.mark.asyncio
    async def test_update_prd_partial_fields(self):
        """Test PRD update with only some fields."""
        # Mock content ID query response
        mock_content_response = {
            "data": {"node": {"content": {"id": "MDHI_lADOBQfyVc4AYzgCzgC5wQk"}}}
        }

        # Mock successful response with only title updated
        mock_result = {
            "data": {
                "updateProjectV2DraftIssue": {
                    "draftIssue": {
                        "id": "MDHI_lADOBQfyVc4AYzgCzgC5wQk",
                        "title": "Only Title Updated",
                        "body": "Original body content",
                        "createdAt": "2024-01-15T10:00:00Z",
                        "updatedAt": "2024-01-15T11:30:00Z",
                        "assignees": {"totalCount": 0, "nodes": []},
                        "projectV2Items": {
                            "totalCount": 1,
                            "nodes": [
                                {
                                    "id": "PVTI_kwDOBQfyVc0FoQ",
                                    "project": {
                                        "id": "PVT_kwDOBQfyVc0FoQ",
                                        "title": "Test Project",
                                    },
                                }
                            ],
                        },
                    }
                }
            }
        }

        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.query.return_value = mock_content_response
        mock_client.mutate.return_value = mock_result

        # Test with only title update
        arguments = {
            "prd_item_id": "PVTI_kwDOBQfyVc0FoQ",
            "title": "Only Title Updated",
        }

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await update_prd_handler(arguments)

            # Verify both query and mutate were called
            mock_client.query.assert_called_once()
            mock_client.mutate.assert_called_once()

            # Verify success response
            assert not result.isError
            assert len(result.content) == 1
            response_text = result.content[0].text
            assert "✅ PRD successfully updated!" in response_text
            assert "Only Title Updated" in response_text

    @pytest.mark.asyncio
    async def test_update_prd_missing_item_id(self):
        """Test update PRD with missing prd_item_id."""
        arguments = {"title": "Test Title"}

        result = await update_prd_handler(arguments)

        # Verify error response
        assert result.isError
        assert len(result.content) == 1
        assert "prd_item_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_update_prd_empty_item_id(self):
        """Test update PRD with empty prd_item_id."""
        arguments = {"prd_item_id": "", "title": "Test Title"}

        result = await update_prd_handler(arguments)

        # Verify error response
        assert result.isError
        assert len(result.content) == 1
        assert "prd_item_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_update_prd_no_updates_provided(self):
        """Test update PRD with no update fields provided."""
        arguments = {"prd_item_id": "PVTI_kwDOBQfyVc0FoQ"}

        result = await update_prd_handler(arguments)

        # Verify error response
        assert result.isError
        assert len(result.content) == 1
        assert (
            "At least one of title, body, or assignee_ids must be provided for update"
            in result.content[0].text
        )

    @pytest.mark.asyncio
    async def test_update_prd_github_client_not_initialized(self):
        """Test update PRD when GitHub client is not initialized."""
        # Mock get_github_client to return None
        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=None,
        ):
            arguments = {"prd_item_id": "PVTI_kwDOBQfyVc0FoQ", "title": "Test Title"}

            result = await update_prd_handler(arguments)

            # Verify error response
            assert result.isError
            assert len(result.content) == 1
            assert "GitHub client not initialized" in result.content[0].text

    @pytest.mark.asyncio
    async def test_update_prd_graphql_errors(self):
        """Test update PRD with GraphQL errors."""
        # Mock content ID query response
        mock_content_response = {
            "data": {"node": {"content": {"id": "MDHI_lADOBQfyVc4AYzgCzgC5wQk"}}}
        }

        # Mock response with errors in update step
        mock_error_result = {
            "errors": [
                {"message": "Draft issue not found"},
                {"message": "Insufficient permissions"},
            ]
        }

        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.query.return_value = mock_content_response
        mock_client.mutate.return_value = mock_error_result

        arguments = {"prd_item_id": "PVTI_kwDOBQfyVc0FoQ", "title": "Test Title"}

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await update_prd_handler(arguments)

            # Verify error response
            assert result.isError
            assert len(result.content) == 1
            error_text = result.content[0].text
            assert "GraphQL errors" in error_text
            assert "Draft issue not found" in error_text
            assert "Insufficient permissions" in error_text

    @pytest.mark.asyncio
    async def test_update_prd_graphql_errors_in_content_query(self):
        """Test update PRD with GraphQL errors in content ID query step."""
        # Mock response with errors in content query step
        mock_error_result = {
            "errors": [
                {"message": "Project item not found"},
                {"message": "Access denied"},
            ]
        }

        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.query.return_value = mock_error_result

        arguments = {"prd_item_id": "PVTI_kwDOBQfyVc0FoQ", "title": "Test Title"}

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await update_prd_handler(arguments)

            # Verify error response
            assert result.isError
            assert len(result.content) == 1
            error_text = result.content[0].text
            assert "Error getting PRD content ID" in error_text
            assert "Project item not found" in error_text

    @pytest.mark.asyncio
    async def test_update_prd_content_not_found(self):
        """Test update PRD when project item has no content."""
        # Mock content query response with node but no content
        mock_content_response = {
            "data": {"node": {"content": None}}  # Content exists but is null
        }

        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.query.return_value = mock_content_response

        arguments = {"prd_item_id": "PVTI_kwDOBQfyVc0FoQ", "title": "Test Title"}

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await update_prd_handler(arguments)

            # Verify error response
            assert result.isError
            assert len(result.content) == 1
            error_text = result.content[0].text
            assert "does not have content" in error_text

    @pytest.mark.asyncio
    async def test_update_prd_api_exception(self):
        """Test update PRD with API exception."""
        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.query.side_effect = Exception("API connection failed")

        arguments = {"prd_item_id": "PVTI_kwDOBQfyVc0FoQ", "title": "Test Title"}

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await update_prd_handler(arguments)

            # Verify error response
            assert result.isError
            assert len(result.content) == 1
            assert "API connection failed" in result.content[0].text

    @pytest.mark.asyncio
    async def test_update_prd_empty_response(self):
        """Test update PRD with empty response from API."""
        # Mock content ID query response
        mock_content_response = {
            "data": {"node": {"content": {"id": "MDHI_lADOBQfyVc4AYzgCzgC5wQk"}}}
        }

        # Mock empty response
        mock_result = {"data": {"updateProjectV2DraftIssue": {}}}

        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.query.return_value = mock_content_response
        mock_client.mutate.return_value = mock_result

        arguments = {"prd_item_id": "PVTI_kwDOBQfyVc0FoQ", "title": "Test Title"}

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await update_prd_handler(arguments)

            # Verify error response
            assert result.isError
            assert len(result.content) == 1
            assert "No draft issue data returned" in result.content[0].text

    @pytest.mark.asyncio
    async def test_update_prd_special_characters(self):
        """Test update PRD with special characters in text fields."""
        # Mock content ID query response
        mock_content_response = {
            "data": {"node": {"content": {"id": "MDHI_lADOBQfyVc4AYzgCzgC5wQk"}}}
        }

        # Mock successful response
        mock_result = {
            "data": {
                "updateProjectV2DraftIssue": {
                    "draftIssue": {
                        "id": "MDHI_lADOBQfyVc4AYzgCzgC5wQk",
                        "title": 'PRD with "quotes" & <html>',
                        "body": "Body with 'special' chars & symbols: @#$%",
                        "createdAt": "2024-01-15T10:00:00Z",
                        "updatedAt": "2024-01-15T11:30:00Z",
                        "assignees": {"totalCount": 0, "nodes": []},
                        "projectV2Items": {
                            "totalCount": 1,
                            "nodes": [
                                {
                                    "id": "PVTI_kwDOBQfyVc0FoQ",
                                    "project": {
                                        "id": "PVT_kwDOBQfyVc0FoQ",
                                        "title": "Test Project",
                                    },
                                }
                            ],
                        },
                    }
                }
            }
        }

        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.query.return_value = mock_content_response
        mock_client.mutate.return_value = mock_result

        arguments = {
            "prd_item_id": "PVTI_kwDOBQfyVc0FoQ",
            "title": 'PRD with "quotes" & <html>',
            "body": "Body with 'special' chars & symbols: @#$%",
        }

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            result = await update_prd_handler(arguments)

            # Verify both query and mutate were called
            mock_client.query.assert_called_once()
            mock_client.mutate.assert_called_once()

            # Verify success response
            assert not result.isError
            assert len(result.content) == 1
            response_text = result.content[0].text
            assert "✅ PRD successfully updated!" in response_text


class TestUpdatePrdStatusHandler:
    """Test cases for update_prd_status MCP tool."""

    @pytest.mark.asyncio
    async def test_update_prd_status_success(self):
        """Test successful PRD status update."""
        mock_arguments = {
            "prd_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "status": "In Progress",
            "priority": "High",
        }

        # Mock GitHub client and response
        mock_client = AsyncMock()

        # Mock project item details query response
        mock_project_response = {
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
                                    {"id": "OPT_BACKLOG", "name": "Backlog"},
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
                        ]
                    },
                },
            }
        }

        # Mock update field value responses
        mock_status_update_response = {
            "data": {
                "updateProjectV2ItemFieldValue": {
                    "projectV2Item": {
                        "id": "PVTI_lADOBQfyVc0FoQzgBVgC",
                        "updatedAt": "2025-01-01T12:30:00Z",
                    }
                }
            }
        }

        mock_priority_update_response = {
            "data": {
                "updateProjectV2ItemFieldValue": {
                    "projectV2Item": {
                        "id": "PVTI_lADOBQfyVc0FoQzgBVgC",
                        "updatedAt": "2025-01-01T12:31:00Z",
                    }
                }
            }
        }

        # Setup mock client call sequence
        mock_client.query.return_value = mock_project_response
        mock_client.mutate.side_effect = [
            mock_status_update_response,
            mock_priority_update_response,
        ]

        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            # Import the handler after patching
            from github_project_manager_mcp.handlers.prd_handlers import (
                update_prd_status_handler,
            )

            result = await update_prd_status_handler(mock_arguments)

            assert result.isError is False
            assert len(result.content) == 1

            content = result.content[0].text
            assert "successfully updated" in content.lower()
            assert "status" in content.lower()
            assert "priority" in content.lower()
            assert "In Progress" in content
            assert "High" in content

    @pytest.mark.asyncio
    async def test_update_prd_status_only(self):
        """Test updating only PRD status."""
        mock_arguments = {
            "prd_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "status": "Done",
        }

        # Mock GitHub client and response
        mock_client = AsyncMock()

        mock_project_response = {
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
                                    {"id": "OPT_BACKLOG", "name": "Backlog"},
                                    {"id": "OPT_IN_PROGRESS", "name": "In Progress"},
                                    {"id": "OPT_DONE", "name": "Done"},
                                ],
                            },
                        ]
                    },
                },
            }
        }

        mock_update_response = {
            "data": {
                "updateProjectV2ItemFieldValue": {
                    "projectV2Item": {
                        "id": "PVTI_lADOBQfyVc0FoQzgBVgC",
                        "updatedAt": "2025-01-01T12:30:00Z",
                    }
                }
            }
        }

        mock_client.query.return_value = mock_project_response
        mock_client.mutate.return_value = mock_update_response

        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            from github_project_manager_mcp.handlers.prd_handlers import (
                update_prd_status_handler,
            )

            result = await update_prd_status_handler(mock_arguments)

            assert result.isError is False
            assert "Done" in result.content[0].text

    @pytest.mark.asyncio
    async def test_update_prd_priority_only(self):
        """Test updating only PRD priority."""
        mock_arguments = {
            "prd_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "priority": "Low",
        }

        mock_client = AsyncMock()

        mock_project_response = {
            "node": {
                "id": "PVTI_lADOBQfyVc0FoQzgBVgC",
                "project": {
                    "id": "PVT_kwDOBQfyVc0FoQ",
                    "fields": {
                        "nodes": [
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
                        ]
                    },
                },
            }
        }

        mock_update_response = {
            "data": {
                "updateProjectV2ItemFieldValue": {
                    "projectV2Item": {
                        "id": "PVTI_lADOBQfyVc0FoQzgBVgC",
                        "updatedAt": "2025-01-01T12:30:00Z",
                    }
                }
            }
        }

        mock_client.query.return_value = mock_project_response
        mock_client.mutate.return_value = mock_update_response

        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            from github_project_manager_mcp.handlers.prd_handlers import (
                update_prd_status_handler,
            )

            result = await update_prd_status_handler(mock_arguments)

            assert result.isError is False
            assert "Low" in result.content[0].text

    @pytest.mark.asyncio
    async def test_update_prd_status_missing_item_id(self):
        """Test update_prd_status with missing PRD item ID."""
        mock_arguments = {
            "status": "In Progress",
        }

        from github_project_manager_mcp.handlers.prd_handlers import (
            update_prd_status_handler,
        )

        result = await update_prd_status_handler(mock_arguments)

        assert result.isError is True
        assert "required" in result.content[0].text.lower()
        assert "prd_item_id" in result.content[0].text.lower()

    @pytest.mark.asyncio
    async def test_update_prd_status_empty_item_id(self):
        """Test update_prd_status with empty PRD item ID."""
        mock_arguments = {
            "prd_item_id": "",
            "status": "In Progress",
        }

        from github_project_manager_mcp.handlers.prd_handlers import (
            update_prd_status_handler,
        )

        result = await update_prd_status_handler(mock_arguments)

        assert result.isError is True
        assert "required" in result.content[0].text.lower()

    @pytest.mark.asyncio
    async def test_update_prd_status_no_updates_provided(self):
        """Test update_prd_status with no update fields provided."""
        mock_arguments = {
            "prd_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
        }

        from github_project_manager_mcp.handlers.prd_handlers import (
            update_prd_status_handler,
        )

        result = await update_prd_status_handler(mock_arguments)

        assert result.isError is True
        assert "at least one update field" in result.content[0].text.lower()

    @pytest.mark.asyncio
    async def test_update_prd_status_invalid_status(self):
        """Test update_prd_status with invalid status value."""
        mock_arguments = {
            "prd_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "status": "Invalid Status",
        }

        from github_project_manager_mcp.handlers.prd_handlers import (
            update_prd_status_handler,
        )

        result = await update_prd_status_handler(mock_arguments)

        assert result.isError is True
        assert "invalid status" in result.content[0].text.lower()

    @pytest.mark.asyncio
    async def test_update_prd_status_invalid_priority(self):
        """Test update_prd_status with invalid priority value."""
        mock_arguments = {
            "prd_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "priority": "Invalid Priority",
        }

        from github_project_manager_mcp.handlers.prd_handlers import (
            update_prd_status_handler,
        )

        result = await update_prd_status_handler(mock_arguments)

        assert result.isError is True
        assert "invalid priority" in result.content[0].text.lower()

    @pytest.mark.asyncio
    async def test_update_prd_status_github_client_not_initialized(self):
        """Test update_prd_status when GitHub client is not initialized."""
        mock_arguments = {
            "prd_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "status": "In Progress",
        }

        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = None

            from github_project_manager_mcp.handlers.prd_handlers import (
                update_prd_status_handler,
            )

            result = await update_prd_status_handler(mock_arguments)

            assert result.isError is True
            assert "not initialized" in result.content[0].text.lower()

    @pytest.mark.asyncio
    async def test_update_prd_status_project_item_not_found(self):
        """Test update_prd_status when project item is not found."""
        mock_arguments = {
            "prd_item_id": "INVALID_ITEM_ID",
            "status": "In Progress",
        }

        mock_client = AsyncMock()
        mock_response = {"node": None}

        mock_client.query.return_value = mock_response

        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            from github_project_manager_mcp.handlers.prd_handlers import (
                update_prd_status_handler,
            )

            result = await update_prd_status_handler(mock_arguments)

            assert result.isError is True
            assert "not found" in result.content[0].text.lower()

    @pytest.mark.asyncio
    async def test_update_prd_status_field_not_found(self):
        """Test update_prd_status when status field is not found in project."""
        mock_arguments = {
            "prd_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "status": "In Progress",
        }

        mock_client = AsyncMock()
        mock_project_response = {
            "node": {
                "id": "PVTI_lADOBQfyVc0FoQzgBVgC",
                "project": {
                    "id": "PVT_kwDOBQfyVc0FoQ",
                    "fields": {"nodes": []},  # No fields found
                },
            }
        }

        mock_client.query.return_value = mock_project_response

        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            from github_project_manager_mcp.handlers.prd_handlers import (
                update_prd_status_handler,
            )

            result = await update_prd_status_handler(mock_arguments)

            assert result.isError is True
            assert "field not found" in result.content[0].text.lower()

    @pytest.mark.asyncio
    async def test_update_prd_status_option_not_found(self):
        """Test update_prd_status when status option is not found."""
        mock_arguments = {
            "prd_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "status": "In Progress",  # Valid status value for our enum
        }

        mock_client = AsyncMock()
        mock_project_response = {
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
                                    {"id": "OPT_BACKLOG", "name": "Backlog"},
                                    {"id": "OPT_DONE", "name": "Done"},
                                    # Note: "In Progress" is not in the project's available options
                                ],
                            },
                        ]
                    },
                },
            }
        }

        mock_client.query.return_value = mock_project_response

        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            from github_project_manager_mcp.handlers.prd_handlers import (
                update_prd_status_handler,
            )

            result = await update_prd_status_handler(mock_arguments)

            assert result.isError is True
            assert (
                "option" in result.content[0].text.lower()
                and "not found" in result.content[0].text.lower()
            )

    @pytest.mark.asyncio
    async def test_update_prd_status_graphql_error(self):
        """Test update_prd_status with GraphQL API errors."""
        mock_arguments = {
            "prd_item_id": "PVTI_lADOBQfyVc0FoQzgBVgC",
            "status": "In Progress",
        }

        mock_client = AsyncMock()
        mock_error_response = {
            "data": None,
            "errors": [{"message": "Invalid project item ID"}],
        }

        mock_client.query.return_value = mock_error_response

        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_client

            from github_project_manager_mcp.handlers.prd_handlers import (
                update_prd_status_handler,
            )

            result = await update_prd_status_handler(mock_arguments)

            assert result.isError is True
            assert "Invalid project item ID" in result.content[0].text


class TestCompletePrdHandler:
    """Test cases for the complete_prd_handler function."""

    @pytest.mark.asyncio
    async def test_complete_prd_success(self):
        """Test successful PRD completion."""
        mock_client = AsyncMock()

        # Mock successful field value response showing current status
        mock_fields_response = {
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
                                "options": [
                                    {"id": "OPT_BACKLOG", "name": "Backlog"},
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
                    "id": "PVTI_prd123",
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
        }

        mock_client.query.return_value = mock_fields_response
        mock_client.mutate.return_value = mock_update_response

        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            from github_project_manager_mcp.handlers.prd_handlers import (
                complete_prd_handler,
            )

            result = await complete_prd_handler(
                {
                    "prd_item_id": "PVTI_prd123",
                }
            )

        assert not result.isError
        assert "PRD completed successfully!" in result.content[0].text
        assert "**Status:** Done" in result.content[0].text

    @pytest.mark.asyncio
    async def test_complete_prd_already_complete(self):
        """Test completing a PRD that is already complete."""
        mock_client = AsyncMock()

        # Mock response with already complete PRD
        mock_fields_response = {
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
                                "options": [
                                    {"id": "OPT_BACKLOG", "name": "Backlog"},
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
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            from github_project_manager_mcp.handlers.prd_handlers import (
                complete_prd_handler,
            )

            result = await complete_prd_handler(
                {
                    "prd_item_id": "PVTI_prd123",
                }
            )

        assert not result.isError
        assert "PRD is already complete!" in result.content[0].text
        assert "**Status:** Done" in result.content[0].text

    @pytest.mark.asyncio
    async def test_complete_prd_missing_prd_item_id(self):
        """Test complete_prd with missing prd_item_id."""
        from github_project_manager_mcp.handlers.prd_handlers import (
            complete_prd_handler,
        )

        result = await complete_prd_handler({})

        assert result.isError
        assert "prd_item_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_complete_prd_empty_prd_item_id(self):
        """Test complete_prd with empty prd_item_id."""
        from github_project_manager_mcp.handlers.prd_handlers import (
            complete_prd_handler,
        )

        result = await complete_prd_handler({"prd_item_id": ""})

        assert result.isError
        assert "prd_item_id is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_complete_prd_github_client_not_initialized(self):
        """Test complete_prd when GitHub client is not initialized."""
        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=None,
        ):
            from github_project_manager_mcp.handlers.prd_handlers import (
                complete_prd_handler,
            )

            result = await complete_prd_handler(
                {
                    "prd_item_id": "PVTI_prd123",
                }
            )

        assert result.isError
        assert "GitHub client not initialized" in result.content[0].text

    @pytest.mark.asyncio
    async def test_complete_prd_not_found(self):
        """Test complete_prd when PRD is not found."""
        mock_client = AsyncMock()
        mock_client.query.return_value = {"node": None}

        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            from github_project_manager_mcp.handlers.prd_handlers import (
                complete_prd_handler,
            )

            result = await complete_prd_handler(
                {
                    "prd_item_id": "PVTI_invalid123",
                }
            )

        assert result.isError
        assert "PRD not found" in result.content[0].text

    @pytest.mark.asyncio
    async def test_complete_prd_no_status_field(self):
        """Test error handling when PRD has no status field."""
        mock_client = AsyncMock()
        mock_response = {
            "node": {
                "id": "PVTI_prd123",
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
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            from github_project_manager_mcp.handlers.prd_handlers import (
                complete_prd_handler,
            )

            result = await complete_prd_handler(
                {
                    "prd_item_id": "PVTI_prd123",
                }
            )

        assert result.isError
        assert "Status field not found" in result.content[0].text

    @pytest.mark.asyncio
    async def test_complete_prd_graphql_query_error(self):
        """Test error handling when GraphQL query fails."""
        mock_client = AsyncMock()
        mock_client.query.side_effect = Exception("GraphQL query failed")

        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            from github_project_manager_mcp.handlers.prd_handlers import (
                complete_prd_handler,
            )

            result = await complete_prd_handler(
                {
                    "prd_item_id": "PVTI_prd123",
                }
            )

        assert result.isError
        assert "Failed to fetch PRD status" in result.content[0].text
        assert "GraphQL query failed" in result.content[0].text

    @pytest.mark.asyncio
    async def test_complete_prd_update_mutation_error(self):
        """Test error handling when update mutation fails."""
        mock_client = AsyncMock()

        # Mock successful query response
        mock_fields_response = {
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
                                "options": [
                                    {"id": "OPT_BACKLOG", "name": "Backlog"},
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
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            from github_project_manager_mcp.handlers.prd_handlers import (
                complete_prd_handler,
            )

            result = await complete_prd_handler(
                {
                    "prd_item_id": "PVTI_prd123",
                }
            )

        assert result.isError
        assert "Failed to complete PRD" in result.content[0].text
        assert "GraphQL mutation error: Permission denied" in result.content[0].text

    @pytest.mark.asyncio
    async def test_complete_prd_no_update_response(self):
        """Test error handling when update mutation returns no response."""
        mock_client = AsyncMock()

        # Mock successful query response
        mock_fields_response = {
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
                                "options": [
                                    {"id": "OPT_BACKLOG", "name": "Backlog"},
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
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            from github_project_manager_mcp.handlers.prd_handlers import (
                complete_prd_handler,
            )

            result = await complete_prd_handler(
                {
                    "prd_item_id": "PVTI_prd123",
                }
            )

        assert result.isError
        assert (
            "No response data received from completion operation"
            in result.content[0].text
        )

    @pytest.mark.asyncio
    async def test_complete_prd_invalid_update_response_format(self):
        """Test error handling when update response format is unexpected."""
        mock_client = AsyncMock()

        # Mock successful query response
        mock_fields_response = {
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
                                "options": [
                                    {"id": "OPT_BACKLOG", "name": "Backlog"},
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
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            from github_project_manager_mcp.handlers.prd_handlers import (
                complete_prd_handler,
            )

            result = await complete_prd_handler(
                {
                    "prd_item_id": "PVTI_prd123",
                }
            )

        assert result.isError
        assert (
            "Invalid response format from completion operation"
            in result.content[0].text
        )

    @pytest.mark.asyncio
    async def test_complete_prd_api_exception(self):
        """Test error handling for general API exceptions."""
        mock_client = AsyncMock()
        mock_client.query.side_effect = Exception("Network error")

        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            from github_project_manager_mcp.handlers.prd_handlers import (
                complete_prd_handler,
            )

            result = await complete_prd_handler(
                {
                    "prd_item_id": "PVTI_prd123",
                }
            )

        assert result.isError
        assert "Failed to fetch PRD status" in result.content[0].text
        assert "Network error" in result.content[0].text

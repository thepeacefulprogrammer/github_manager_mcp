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
        assert len(PRD_TOOLS) >= 1  # At least add_prd_to_project for now

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

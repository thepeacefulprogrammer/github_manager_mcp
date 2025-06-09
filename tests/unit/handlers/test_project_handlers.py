"""
Unit tests for project handlers.

This module tests the MCP tool handlers for project management operations.
Following TDD principles - these tests define the expected behavior before implementation.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.types import CallToolResult, TextContent, Tool

from github_project_manager_mcp.handlers.project_handlers import (
    CREATE_PROJECT_TOOL,
    create_project_handler,
    get_owner_id_from_repository,
    initialize_github_client,
    validate_repository_format,
)


class TestCreateProjectTool:
    """Test cases for create_project MCP tool handler."""

    def test_tool_definition(self):
        """Test that create_project tool is properly defined."""
        # Verify the tool definition structure
        tool = CREATE_PROJECT_TOOL

        # Check basic properties
        assert tool.name == "create_project"
        assert "GitHub Projects v2" in tool.description
        assert "repository" in tool.description

        # Check input schema
        schema = tool.inputSchema
        assert schema["type"] == "object"

        # Check required fields
        required_fields = schema["required"]
        assert "name" in required_fields
        assert "description" in required_fields
        assert "repository" in required_fields

        # Check properties
        properties = schema["properties"]
        assert "name" in properties
        assert "description" in properties
        assert "repository" in properties
        assert "visibility" in properties

        # Check repository property description
        assert "owner/repo" in properties["repository"]["description"]

    @pytest.mark.asyncio
    async def test_create_project_success(self):
        """Test successful project creation."""
        # Mock inputs
        arguments = {
            "name": "Test Project",
            "description": "A test project for our application",
            "repository": "test-org/test-repo",
        }

        # Expected GitHub API responses
        mock_repo_data = {
            "repository": {
                "owner": {"id": "MDEyOk9yZ2FuaXphdGlvbjE=", "login": "test-org"}
            }
        }

        mock_project_data = {
            "createProjectV2": {
                "projectV2": {
                    "id": "PVT_kwDOBQfyVc0FoQ",
                    "number": 1,
                    "title": "Test Project",
                    "description": "A test project for our application",
                    "url": "https://github.com/orgs/test-org/projects/1",
                    "createdAt": "2024-01-01T00:00:00Z",
                    "owner": {"login": "test-org"},
                }
            }
        }

        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.query.return_value = mock_repo_data
        mock_client.mutate.return_value = mock_project_data

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.project_handlers.github_client",
            mock_client,
        ):
            result = await create_project_handler(arguments)

            # Verify the result
            assert not result.isError
            assert len(result.content) == 1
            assert result.content[0].type == "text"

            # Check success message content
            content_text = result.content[0].text
            assert "✅ Successfully created project!" in content_text
            assert "Test Project" in content_text
            assert "PVT_kwDOBQfyVc0FoQ" in content_text
            assert "test-org/test-repo" in content_text

            # Verify API calls were made
            mock_client.query.assert_called_once()
            mock_client.mutate.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_project_missing_required_params(self):
        """Test handling of missing required parameters."""
        # Test cases for missing name, description, and repository
        test_cases = [
            {},  # No parameters
            {"name": "Test"},  # Missing description and repository
            {"description": "Test desc"},  # Missing name and repository
            {"repository": "test/repo"},  # Missing name and description
        ]

        for arguments in test_cases:
            result = await create_project_handler(arguments)

            # Should return error result
            assert result.isError
            assert len(result.content) == 1
            assert result.content[0].type == "text"
            assert "Error:" in result.content[0].text
            assert "required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_create_project_invalid_repository_format(self):
        """Test handling of invalid repository format."""
        arguments = {
            "name": "Test Project",
            "description": "Test description",
            "repository": "invalid-repo-format",  # Should be "owner/repo"
        }

        # Mock the GitHub client to be available
        with patch(
            "github_project_manager_mcp.handlers.project_handlers.github_client",
            AsyncMock(),
        ):
            result = await create_project_handler(arguments)

            # Should validate repository format and return error
            assert result.isError
            assert len(result.content) == 1
            assert result.content[0].type == "text"
            assert "Invalid repository format" in result.content[0].text
            assert "Expected 'owner/repo'" in result.content[0].text


class TestRepositoryValidation:
    """Test cases for repository format validation."""

    def test_valid_repository_formats(self):
        """Test valid repository formats."""
        valid_formats = [
            "octocat/Hello-World",
            "owner/repo",
            "test-org/test-repo",
            "user123/project_name",
            "org-name/repo.name",
        ]

        for repo in valid_formats:
            assert validate_repository_format(repo), f"Should be valid: {repo}"

    def test_invalid_repository_formats(self):
        """Test invalid repository formats."""
        invalid_formats = [
            "",  # Empty string
            "single-part",  # No slash
            "/missing-owner",  # Missing owner
            "missing-repo/",  # Missing repo
            "too/many/parts",  # Too many parts
            None,  # None value
            123,  # Non-string
            "owner//double-slash",  # Empty repo part
        ]

        for repo in invalid_formats:
            assert not validate_repository_format(repo), f"Should be invalid: {repo}"


class TestListProjectsTool:
    """Test cases for list_projects MCP tool handler."""

    def test_list_projects_tool_definition(self):
        """Test that list_projects tool is properly defined."""
        from github_project_manager_mcp.handlers.project_handlers import (
            LIST_PROJECTS_TOOL,
        )

        # Check basic properties
        assert LIST_PROJECTS_TOOL.name == "list_projects"
        assert "list" in LIST_PROJECTS_TOOL.description.lower()
        assert "project" in LIST_PROJECTS_TOOL.description.lower()

        # Check input schema
        schema = LIST_PROJECTS_TOOL.inputSchema
        assert schema["type"] == "object"

        # Check properties exist
        properties = schema["properties"]
        assert "owner" in properties
        assert "first" in properties  # pagination
        assert "after" in properties  # pagination cursor

        # Check owner is required
        required_fields = schema.get("required", [])
        assert "owner" in required_fields

        # Check pagination fields are optional integers/strings
        assert properties["first"]["type"] == "integer"
        assert properties["after"]["type"] == "string"

    @pytest.mark.asyncio
    async def test_list_projects_success_no_pagination(self):
        """Test successful project listing without pagination."""
        arguments = {"owner": "test-org"}

        # Expected GitHub API response
        mock_response = {
            "user": {
                "projectsV2": {
                    "totalCount": 2,
                    "nodes": [
                        {
                            "id": "PVT_kwDOBQfyVc0FoQ",
                            "title": "Project Alpha",
                            "description": "First test project",
                            "url": "https://github.com/orgs/test-org/projects/1",
                            "createdAt": "2024-01-01T00:00:00Z",
                            "updatedAt": "2024-01-02T00:00:00Z",
                            "number": 1,
                            "viewerCanUpdate": True,
                        },
                        {
                            "id": "PVT_kwDOBQfyVc0FoR",
                            "title": "Project Beta",
                            "description": "Second test project",
                            "url": "https://github.com/orgs/test-org/projects/2",
                            "createdAt": "2024-01-03T00:00:00Z",
                            "updatedAt": "2024-01-04T00:00:00Z",
                            "number": 2,
                            "viewerCanUpdate": False,
                        },
                    ],
                }
            }
        }

        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.query.return_value = mock_response

        from github_project_manager_mcp.handlers.project_handlers import (
            list_projects_handler,
        )

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.project_handlers.github_client",
            mock_client,
        ):
            result = await list_projects_handler(arguments)

            # Verify the result
            assert not result.isError
            assert len(result.content) == 1
            assert result.content[0].type == "text"

            # Check response content
            content_text = result.content[0].text
            assert "Projects for test-org" in content_text
            assert "Total: 2 projects" in content_text
            assert "Project Alpha" in content_text
            assert "Project Beta" in content_text
            assert "PVT_kwDOBQfyVc0FoQ" in content_text
            assert "PVT_kwDOBQfyVc0FoR" in content_text

            # Verify API call was made
            mock_client.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_projects_success_with_pagination(self):
        """Test successful project listing with pagination parameters."""
        arguments = {"owner": "test-org", "first": 10, "after": "cursor123"}

        # Expected GitHub API response with pagination info
        mock_response = {
            "user": {
                "projectsV2": {
                    "totalCount": 25,
                    "pageInfo": {
                        "hasNextPage": True,
                        "hasPreviousPage": True,
                        "startCursor": "cursor123",
                        "endCursor": "cursor133",
                    },
                    "nodes": [
                        {
                            "id": "PVT_kwDOBQfyVc0FoQ",
                            "title": "Project Alpha",
                            "description": "Test project",
                            "url": "https://github.com/orgs/test-org/projects/1",
                            "createdAt": "2024-01-01T00:00:00Z",
                            "updatedAt": "2024-01-02T00:00:00Z",
                            "number": 1,
                            "viewerCanUpdate": True,
                        }
                    ],
                }
            }
        }

        mock_client = AsyncMock()
        mock_client.query.return_value = mock_response

        from github_project_manager_mcp.handlers.project_handlers import (
            list_projects_handler,
        )

        with patch(
            "github_project_manager_mcp.handlers.project_handlers.github_client",
            mock_client,
        ):
            result = await list_projects_handler(arguments)

            # Verify the result
            assert not result.isError
            assert len(result.content) == 1

            content_text = result.content[0].text
            # Should include pagination info
            assert "Total: 25 projects" in content_text
            assert "Showing 1 projects" in content_text
            assert "Has next page: True" in content_text
            assert "Next cursor: cursor133" in content_text

    @pytest.mark.asyncio
    async def test_list_projects_empty_result(self):
        """Test project listing when no projects exist."""
        arguments = {"owner": "empty-org"}

        # Empty response
        mock_response = {"user": {"projectsV2": {"totalCount": 0, "nodes": []}}}

        mock_client = AsyncMock()
        mock_client.query.return_value = mock_response

        from github_project_manager_mcp.handlers.project_handlers import (
            list_projects_handler,
        )

        with patch(
            "github_project_manager_mcp.handlers.project_handlers.github_client",
            mock_client,
        ):
            result = await list_projects_handler(arguments)

            # Verify the result
            assert not result.isError
            assert len(result.content) == 1

            content_text = result.content[0].text
            assert "No projects found" in content_text
            assert "empty-org" in content_text

    @pytest.mark.asyncio
    async def test_list_projects_missing_owner(self):
        """Test handling of missing owner parameter."""
        arguments = {}

        from github_project_manager_mcp.handlers.project_handlers import (
            list_projects_handler,
        )

        result = await list_projects_handler(arguments)

        # Should return error result
        assert result.isError
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        assert "Error:" in result.content[0].text
        assert "owner" in result.content[0].text.lower()
        assert "required" in result.content[0].text.lower()

    @pytest.mark.asyncio
    async def test_list_projects_client_not_initialized(self):
        """Test handling when GitHub client is not initialized."""
        arguments = {"owner": "test-org"}

        from github_project_manager_mcp.handlers.project_handlers import (
            list_projects_handler,
        )

        # Ensure github_client is None
        with patch(
            "github_project_manager_mcp.handlers.project_handlers.github_client", None
        ):
            result = await list_projects_handler(arguments)

            assert result.isError
            assert len(result.content) == 1
            assert "GitHub client not initialized" in result.content[0].text

    @pytest.mark.asyncio
    async def test_list_projects_api_error(self):
        """Test handling of GitHub API errors."""
        arguments = {"owner": "test-org"}

        # Mock client that raises exception
        mock_client = AsyncMock()
        mock_client.query.side_effect = Exception("API Error: Rate limit exceeded")

        from github_project_manager_mcp.handlers.project_handlers import (
            list_projects_handler,
        )

        with patch(
            "github_project_manager_mcp.handlers.project_handlers.github_client",
            mock_client,
        ):
            result = await list_projects_handler(arguments)

            assert result.isError
            assert len(result.content) == 1
            assert "API Error" in result.content[0].text

    @pytest.mark.asyncio
    async def test_list_projects_user_not_found(self):
        """Test handling when user/organization is not found."""
        arguments = {"owner": "nonexistent-user"}

        # Response with null user
        mock_response = {"user": None}

        mock_client = AsyncMock()
        mock_client.query.return_value = mock_response

        from github_project_manager_mcp.handlers.project_handlers import (
            list_projects_handler,
        )

        with patch(
            "github_project_manager_mcp.handlers.project_handlers.github_client",
            mock_client,
        ):
            result = await list_projects_handler(arguments)

            assert result.isError
            assert len(result.content) == 1
            assert "User not found" in result.content[0].text
            assert "nonexistent-user" in result.content[0].text


class TestProjectHandlerRegistration:
    """Test cases for project handler registration with MCP server."""

    def test_project_tools_list(self):
        """Test that PROJECT_TOOLS contains the expected tools."""
        from github_project_manager_mcp.handlers.project_handlers import PROJECT_TOOLS

        # Should contain create_project tool
        tool_names = [tool.name for tool in PROJECT_TOOLS]
        assert "create_project" in tool_names

    def test_project_tool_handlers_mapping(self):
        """Test that PROJECT_TOOL_HANDLERS contains the expected mappings."""
        from github_project_manager_mcp.handlers.project_handlers import (
            PROJECT_TOOL_HANDLERS,
        )

        # Should contain create_project handler
        assert "create_project" in PROJECT_TOOL_HANDLERS
        assert callable(PROJECT_TOOL_HANDLERS["create_project"])

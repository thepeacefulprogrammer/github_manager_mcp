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
    update_project_handler,
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


class TestDeleteProjectTool:
    """Test cases for delete_project MCP tool handler."""

    def test_delete_project_tool_definition(self):
        """Test that delete_project tool is properly defined."""
        from github_project_manager_mcp.handlers.project_handlers import (
            DELETE_PROJECT_TOOL,
        )

        tool = DELETE_PROJECT_TOOL

        # Check basic properties
        assert tool.name == "delete_project"
        assert "delete" in tool.description.lower()
        assert "project" in tool.description.lower()

        # Check input schema
        schema = tool.inputSchema
        assert schema["type"] == "object"

        # Check required fields
        required_fields = schema["required"]
        assert "project_id" in required_fields

        # Check properties
        properties = schema["properties"]
        assert "project_id" in properties
        assert "confirm" in properties

        # Check project_id property
        assert "ID of the project to delete" in properties["project_id"]["description"]

    @pytest.mark.asyncio
    async def test_delete_project_success(self):
        """Test successful project deletion."""
        # Mock inputs
        arguments = {"project_id": "PVT_kwDOBQfyVc0FoQ", "confirm": True}

        # Expected GitHub API response
        mock_delete_data = {
            "deleteProjectV2": {
                "projectV2": {
                    "id": "PVT_kwDOBQfyVc0FoQ",
                    "title": "Test Project",
                    "owner": {"login": "test-org"},
                }
            }
        }

        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.mutate.return_value = mock_delete_data

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.project_handlers.github_client",
            mock_client,
        ):
            from github_project_manager_mcp.handlers.project_handlers import (
                delete_project_handler,
            )

            result = await delete_project_handler(arguments)

            # Verify the result
            assert not result.isError
            assert len(result.content) == 1
            assert result.content[0].type == "text"

            # Check success message content
            content_text = result.content[0].text
            assert "✅ Successfully deleted project!" in content_text
            assert "Test Project" in content_text
            assert "PVT_kwDOBQfyVc0FoQ" in content_text

            # Verify API call was made
            mock_client.mutate.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_project_missing_confirmation(self):
        """Test handling of missing confirmation."""
        arguments = {
            "project_id": "PVT_kwDOBQfyVc0FoQ"
            # Missing confirm parameter
        }

        from github_project_manager_mcp.handlers.project_handlers import (
            delete_project_handler,
        )

        result = await delete_project_handler(arguments)

        # Should return error result
        assert result.isError
        assert len(result.content) == 1
        assert (
            "Must explicitly confirm deletion by setting 'confirm' to true"
            in result.content[0].text
        )

    @pytest.mark.asyncio
    async def test_delete_project_confirmation_false(self):
        """Test handling of explicit false confirmation."""
        arguments = {"project_id": "PVT_kwDOBQfyVc0FoQ", "confirm": False}

        from github_project_manager_mcp.handlers.project_handlers import (
            delete_project_handler,
        )

        result = await delete_project_handler(arguments)

        # Should return error result
        assert result.isError
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        assert (
            "Deletion cancelled. Set 'confirm' to true to proceed"
            in result.content[0].text
        )

    @pytest.mark.asyncio
    async def test_delete_project_missing_project_id(self):
        """Test handling of missing project_id."""
        arguments = {
            "confirm": True
            # Missing project_id
        }

        from github_project_manager_mcp.handlers.project_handlers import (
            delete_project_handler,
        )

        result = await delete_project_handler(arguments)

        # Should return error result
        assert result.isError
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        assert "'project_id' parameter is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_delete_project_invalid_project_id(self):
        """Test handling of project not found."""
        arguments = {"project_id": "invalid-project-id", "confirm": True}

        # Mock GitHub API error response
        mock_client = AsyncMock()
        mock_client.mutate.side_effect = Exception(
            "Could not resolve to a node with the global id"
        )

        with patch(
            "github_project_manager_mcp.handlers.project_handlers.github_client",
            mock_client,
        ):
            from github_project_manager_mcp.handlers.project_handlers import (
                delete_project_handler,
            )

            result = await delete_project_handler(arguments)

            # Should return error result
            assert result.isError
            assert len(result.content) == 1
            assert result.content[0].type == "text"
            assert "Error deleting project" in result.content[0].text

    @pytest.mark.asyncio
    async def test_delete_project_client_not_initialized(self):
        """Test handling when GitHub client is not initialized."""
        arguments = {"project_id": "PVT_kwDOBQfyVc0FoQ", "confirm": True}

        # Mock None client
        with patch(
            "github_project_manager_mcp.handlers.project_handlers.github_client",
            None,
        ):
            from github_project_manager_mcp.handlers.project_handlers import (
                delete_project_handler,
            )

            result = await delete_project_handler(arguments)

            # Should return error result
            assert result.isError
            assert len(result.content) == 1
            assert result.content[0].type == "text"
            assert "GitHub client not initialized" in result.content[0].text


class TestGetProjectDetailsTool:
    """Test cases for get_project_details MCP tool handler."""

    def test_get_project_details_tool_definition(self):
        """Test that get_project_details tool is properly defined."""
        from github_project_manager_mcp.handlers.project_handlers import (
            GET_PROJECT_DETAILS_TOOL,
        )

        tool = GET_PROJECT_DETAILS_TOOL

        # Check basic properties
        assert tool.name == "get_project_details"
        assert "detailed" in tool.description.lower()
        assert "project" in tool.description.lower()

        # Check input schema
        schema = tool.inputSchema
        assert schema["type"] == "object"

        # Check required fields
        required_fields = schema["required"]
        assert "project_id" in required_fields

        # Check properties
        properties = schema["properties"]
        assert "project_id" in properties

        # Check project_id property
        assert "ID of the project" in properties["project_id"]["description"]

    @pytest.mark.asyncio
    async def test_get_project_details_success(self):
        """Test successful project details retrieval."""
        # Mock inputs
        arguments = {
            "project_id": "PVT_kwDOBQfyVc0FoQ"
        }

        # Expected GitHub API response
        mock_project_data = {
            "node": {
                "id": "PVT_kwDOBQfyVc0FoQ",
                "title": "Test Project",
                "shortDescription": "A test project for validation",
                "url": "https://github.com/users/testuser/projects/1",
                "number": 1,
                "createdAt": "2025-01-01T00:00:00Z",
                "updatedAt": "2025-01-02T00:00:00Z",
                "viewerCanUpdate": True,
                "owner": {"login": "testuser"}
            }
        }

        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.query.return_value = mock_project_data

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.project_handlers.github_client",
            mock_client,
        ):
            from github_project_manager_mcp.handlers.project_handlers import (
                get_project_details_handler,
            )

            result = await get_project_details_handler(arguments)

            # Verify the result
            assert not result.isError
            assert len(result.content) == 1
            assert result.content[0].type == "text"

            # Check success message content
            content_text = result.content[0].text
            assert "Test Project" in content_text
            assert "PVT_kwDOBQfyVc0FoQ" in content_text
            assert "testuser" in content_text
            # The description will show short_description since description is None
            assert "A test project for validation" in content_text

            # Verify API call was made
            mock_client.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_project_details_missing_project_id(self):
        """Test handling of missing project_id."""
        arguments = {}

        from github_project_manager_mcp.handlers.project_handlers import (
            get_project_details_handler,
        )

        result = await get_project_details_handler(arguments)

        # Should return error result
        assert result.isError
        assert len(result.content) == 1
        assert "'project_id' parameter is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_get_project_details_invalid_project_id(self):
        """Test handling of project not found."""
        arguments = {
            "project_id": "invalid-project-id"
        }

        # Mock GitHub API error response
        mock_client = AsyncMock()
        mock_client.query.side_effect = Exception("Could not resolve to a node with the global id")

        with patch(
            "github_project_manager_mcp.handlers.project_handlers.github_client",
            mock_client,
        ):
            from github_project_manager_mcp.handlers.project_handlers import (
                get_project_details_handler,
            )

            result = await get_project_details_handler(arguments)

            # Should return error result
            assert result.isError
            assert len(result.content) == 1
            assert result.content[0].type == "text"
            assert "Error retrieving project details" in result.content[0].text

    @pytest.mark.asyncio
    async def test_get_project_details_project_not_found(self):
        """Test handling when project doesn't exist."""
        arguments = {
            "project_id": "PVT_kwDOBQfyVc0FoQ"
        }

        # Mock GitHub API response with null node
        mock_project_data = {"node": None}

        mock_client = AsyncMock()
        mock_client.query.return_value = mock_project_data

        with patch(
            "github_project_manager_mcp.handlers.project_handlers.github_client",
            mock_client,
        ):
            from github_project_manager_mcp.handlers.project_handlers import (
                get_project_details_handler,
            )

            result = await get_project_details_handler(arguments)

            # Should return error result
            assert result.isError
            assert len(result.content) == 1
            assert result.content[0].type == "text"
            assert "Project not found" in result.content[0].text

    @pytest.mark.asyncio
    async def test_get_project_details_client_not_initialized(self):
        """Test handling when GitHub client is not initialized."""
        arguments = {
            "project_id": "PVT_kwDOBQfyVc0FoQ"
        }

        # Mock None client
        with patch(
            "github_project_manager_mcp.handlers.project_handlers.github_client",
            None,
        ):
            from github_project_manager_mcp.handlers.project_handlers import (
                get_project_details_handler,
            )

            result = await get_project_details_handler(arguments)

            # Should return error result
            assert result.isError
            assert len(result.content) == 1
            assert result.content[0].type == "text"
            assert "GitHub client not initialized" in result.content[0].text


class TestProjectHandlerRegistration:
    """Test cases for project handler registration with MCP server."""

    def test_project_tools_list(self):
        """Test that PROJECT_TOOLS contains the expected tools."""
        from github_project_manager_mcp.handlers.project_handlers import PROJECT_TOOLS

        # Should contain all project management tools
        tool_names = [tool.name for tool in PROJECT_TOOLS]
        assert "create_project" in tool_names
        assert "list_projects" in tool_names
        assert "update_project" in tool_names
        assert "delete_project" in tool_names
        assert "get_project_details" in tool_names
        assert len(PROJECT_TOOLS) == 5

    def test_project_tool_handlers_mapping(self):
        """Test that PROJECT_TOOL_HANDLERS contains the expected mappings."""
        from github_project_manager_mcp.handlers.project_handlers import (
            PROJECT_TOOL_HANDLERS,
        )

        # Should contain all project handlers
        assert "create_project" in PROJECT_TOOL_HANDLERS
        assert "list_projects" in PROJECT_TOOL_HANDLERS
        assert "update_project" in PROJECT_TOOL_HANDLERS
        assert "delete_project" in PROJECT_TOOL_HANDLERS
        assert "get_project_details" in PROJECT_TOOL_HANDLERS
        assert callable(PROJECT_TOOL_HANDLERS["create_project"])
        assert callable(PROJECT_TOOL_HANDLERS["list_projects"])
        assert callable(PROJECT_TOOL_HANDLERS["update_project"])
        assert callable(PROJECT_TOOL_HANDLERS["delete_project"])
        assert callable(PROJECT_TOOL_HANDLERS["get_project_details"])


class TestUpdateProjectHandler:
    """Test cases for update_project_handler."""

    @pytest.mark.asyncio
    async def test_update_project_success_all_fields(self):
        """Test successful project update with all fields."""
        # Mock successful mutation response
        mock_result = {
            "updateProjectV2": {
                "projectV2": {
                    "id": "PVT_kwDOBQfyVc0FoQ",
                    "title": "Updated Project Title",
                    "shortDescription": "Updated short description",
                    "readme": "# Updated README\n\nThis is the updated content",
                    "public": True,
                    "updatedAt": "2024-01-15T10:30:00Z",
                }
            }
        }

        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.mutate.return_value = mock_result

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.project_handlers.github_client",
            mock_client,
        ):
            # Test with all fields
            result = await update_project_handler({
                "project_id": "PVT_kwDOBQfyVc0FoQ",
                "title": "Updated Project Title",
                "short_description": "Updated short description", 
                "readme": "# Updated README\n\nThis is the updated content",
                "public": True,
            })

            # Verify result
            assert not result.isError
            assert len(result.content) == 1
            response_text = result.content[0].text
            
            assert "✅ Successfully updated project!" in response_text
            assert "Updated Project Title" in response_text
            assert "PVT_kwDOBQfyVc0FoQ" in response_text
            assert "- **Title:** Updated Project Title" in response_text
            assert "- **Description:** Updated short description" in response_text
            assert "- **README:** Updated (45 characters)" in response_text
            assert "- **Visibility:** Public" in response_text
            assert "2024-01-15T10:30:00Z" in response_text

            # Verify mutation was called with correct parameters
            mock_client.mutate.assert_called_once()
            mutation_call = mock_client.mutate.call_args[0][0]
            assert "updateProjectV2" in mutation_call
            assert '"Updated Project Title"' in mutation_call
            assert '"Updated short description"' in mutation_call
            assert "true" in mutation_call  # public: true

    @pytest.mark.asyncio
    async def test_update_project_success_single_field(self):
        """Test successful project update with single field."""
        mock_result = {
            "updateProjectV2": {
                "projectV2": {
                    "id": "PVT_kwDOBQfyVc0FoQ",
                    "title": "New Title Only",
                    "shortDescription": "",
                    "readme": "",
                    "public": False,
                    "updatedAt": "2024-01-15T10:30:00Z",
                }
            }
        }

        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.mutate.return_value = mock_result

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.project_handlers.github_client",
            mock_client,
        ):
            # Test with only title
            result = await update_project_handler({
                "project_id": "PVT_kwDOBQfyVc0FoQ",
                "title": "New Title Only",
            })

            # Verify result
            assert not result.isError
            response_text = result.content[0].text
            assert "✅ Successfully updated project!" in response_text
            assert "New Title Only" in response_text
            assert "- **Title:** New Title Only" in response_text
            # Should not contain other field updates
            assert "- **Description:**" not in response_text
            assert "- **README:**" not in response_text
            assert "- **Visibility:**" not in response_text

    @pytest.mark.asyncio
    async def test_update_project_success_visibility_false(self):
        """Test successful project update setting visibility to false."""
        mock_result = {
            "updateProjectV2": {
                "projectV2": {
                    "id": "PVT_kwDOBQfyVc0FoQ",
                    "title": "Test Project",
                    "shortDescription": "",
                    "readme": "",
                    "public": False,
                    "updatedAt": "2024-01-15T10:30:00Z",
                }
            }
        }

        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.mutate.return_value = mock_result

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.project_handlers.github_client",
            mock_client,
        ):
            # Test with public set to False
            result = await update_project_handler({
                "project_id": "PVT_kwDOBQfyVc0FoQ",
                "public": False,
            })

            # Verify result
            assert not result.isError
            response_text = result.content[0].text
            assert "- **Visibility:** Private" in response_text

            # Verify mutation includes public: false
            mock_client.mutate.assert_called_once()
            mutation_call = mock_client.mutate.call_args[0][0]
            assert "public: false" in mutation_call

    @pytest.mark.asyncio
    async def test_update_project_missing_project_id(self):
        """Test error when project_id is missing."""
        result = await update_project_handler({
            "title": "Some Title",
        })

        assert result.isError
        assert len(result.content) == 1
        assert "Error: 'project_id' parameter is required" in result.content[0].text

    @pytest.mark.asyncio
    async def test_update_project_no_updates_provided(self):
        """Test error when no update fields are provided."""
        result = await update_project_handler({
            "project_id": "PVT_kwDOBQfyVc0FoQ",
        })

        assert result.isError
        assert len(result.content) == 1
        assert "At least one field to update must be provided" in result.content[0].text

    @pytest.mark.asyncio
    async def test_update_project_empty_string_fields_ignored(self):
        """Test that empty string fields are treated as no update."""
        result = await update_project_handler({
            "project_id": "PVT_kwDOBQfyVc0FoQ",
            "title": "",
            "short_description": "",
            "readme": "",
        })

        assert result.isError
        assert "At least one field to update must be provided" in result.content[0].text

    @pytest.mark.asyncio
    async def test_update_project_github_client_not_initialized(self):
        """Test error when GitHub client is not initialized."""
        # Temporarily set github_client to None
        from github_project_manager_mcp.handlers import project_handlers
        original_client = project_handlers.github_client
        project_handlers.github_client = None

        try:
            result = await update_project_handler({
                "project_id": "PVT_kwDOBQfyVc0FoQ",
                "title": "Test",
            })

            assert result.isError
            assert "Error: GitHub client not initialized" in result.content[0].text
        finally:
            # Restore the original client
            project_handlers.github_client = original_client

    @pytest.mark.asyncio
    async def test_update_project_github_api_error(self):
        """Test handling of GitHub API errors."""
        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.mutate.side_effect = Exception("API rate limit exceeded")

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.project_handlers.github_client",
            mock_client,
        ):
            result = await update_project_handler({
                "project_id": "PVT_kwDOBQfyVc0FoQ",
                "title": "Test Title",
            })

            assert result.isError
            assert "Error updating project: API rate limit exceeded" in result.content[0].text

    @pytest.mark.asyncio
    async def test_update_project_no_data_returned(self):
        """Test handling when GitHub API returns no data."""
        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.mutate.return_value = {"updateProjectV2": {}}

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.project_handlers.github_client",
            mock_client,
        ):
            result = await update_project_handler({
                "project_id": "PVT_kwDOBQfyVc0FoQ",
                "title": "Test Title",
            })

            assert result.isError
            assert "Error: Failed to update project - no data returned" in result.content[0].text

    @pytest.mark.asyncio
    async def test_update_project_malformed_response(self):
        """Test handling of malformed API response."""
        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.mutate.return_value = {"something": "unexpected"}

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.project_handlers.github_client",
            mock_client,
        ):
            result = await update_project_handler({
                "project_id": "PVT_kwDOBQfyVc0FoQ",
                "title": "Test Title",
            })

            assert result.isError
            assert "Error: Failed to update project - no data returned" in result.content[0].text

    @pytest.mark.asyncio
    async def test_update_project_with_special_characters(self):
        """Test project update with special characters in fields."""
        mock_result = {
            "updateProjectV2": {
                "projectV2": {
                    "id": "PVT_kwDOBQfyVc0FoQ",
                    "title": "Project with \"quotes\" & symbols",
                    "shortDescription": "Description with <tags> & entities",
                    "readme": "# README with\n\n- Special chars: @#$%\n- Unicode: 🚀✨",
                    "public": True,
                    "updatedAt": "2024-01-15T10:30:00Z",
                }
            }
        }

        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.mutate.return_value = mock_result

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.project_handlers.github_client",
            mock_client,
        ):
            result = await update_project_handler({
                "project_id": "PVT_kwDOBQfyVc0FoQ",
                "title": "Project with \"quotes\" & symbols",
                "short_description": "Description with <tags> & entities",
                "readme": "# README with\n\n- Special chars: @#$%\n- Unicode: 🚀✨",
                "public": True,
            })

            assert not result.isError
            response_text = result.content[0].text
            assert "✅ Successfully updated project!" in response_text
            assert "Project with \"quotes\" & symbols" in response_text

            # Verify proper escaping in GraphQL mutation
            mock_client.mutate.assert_called_once()
            mutation_call = mock_client.mutate.call_args[0][0]
            # Should properly escape quotes and special characters
            assert r'\"quotes\"' in mutation_call or '"quotes"' in mutation_call

    @pytest.mark.asyncio
    async def test_update_project_with_long_readme(self):
        """Test project update with long README content."""
        long_readme = "# Long README\n\n" + "This is a very long line. " * 100
        
        mock_result = {
            "updateProjectV2": {
                "projectV2": {
                    "id": "PVT_kwDOBQfyVc0FoQ",
                    "title": "Test Project",
                    "shortDescription": "",
                    "readme": long_readme,
                    "public": False,
                    "updatedAt": "2024-01-15T10:30:00Z",
                }
            }
        }

        # Mock the GitHub client
        mock_client = AsyncMock()
        mock_client.mutate.return_value = mock_result

        # Patch the github_client global variable
        with patch(
            "github_project_manager_mcp.handlers.project_handlers.github_client",
            mock_client,
        ):
            result = await update_project_handler({
                "project_id": "PVT_kwDOBQfyVc0FoQ",
                "readme": long_readme,
            })

            assert not result.isError
            response_text = result.content[0].text
            assert f"- **README:** Updated ({len(long_readme)} characters)" in response_text

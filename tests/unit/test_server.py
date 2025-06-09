"""
Unit tests for the main MCP server implementation.

This module tests the core MCP server functionality including initialization,
tool registration, transport handling, and server lifecycle management.
Following TDD principles - these tests define the expected behavior before implementation.
"""

import asyncio
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    CallToolResult,
    GetPromptResult,
    InitializeResult,
    ListPromptsResult,
    ListResourcesResult,
    ListToolsResult,
    TextContent,
    Tool,
)

from github_project_manager_mcp.server import (
    GitHubProjectManagerServer,
    create_server,
    main,
)


class TestGitHubProjectManagerServer:
    """Test cases for GitHubProjectManagerServer class."""

    def test_server_initialization(self):
        """Test that server initializes properly with required components."""
        server = GitHubProjectManagerServer()

        # Check that server has the necessary attributes
        assert hasattr(server, "mcp_server")
        assert hasattr(server, "github_token")
        assert hasattr(server, "initialized")

        # Check initial state
        assert server.initialized is False
        assert server.github_token is None
        assert server.mcp_server is not None

    @pytest.mark.asyncio
    async def test_server_initialization_with_token(self):
        """Test server initialization with GitHub token."""
        token = "ghp_test_token_123"
        server = GitHubProjectManagerServer()

        with patch(
            "github_project_manager_mcp.server.load_github_token", return_value=token
        ):
            with patch(
                "github_project_manager_mcp.server.initialize_github_client"
            ) as mock_init:
                await server.initialize()

                # Verify initialization
                assert server.initialized is True
                assert server.github_token == token
                mock_init.assert_called_once_with(token)

    @pytest.mark.asyncio
    async def test_server_initialization_without_token_raises_error(self):
        """Test that server initialization fails without GitHub token."""
        server = GitHubProjectManagerServer()

        with patch(
            "github_project_manager_mcp.server.load_github_token", return_value=None
        ):
            with pytest.raises(ValueError) as exc_info:
                await server.initialize()

            assert "GitHub token not found" in str(exc_info.value)
            assert server.initialized is False

    def test_server_registers_project_tools(self):
        """Test that server registers all project management tools."""
        server = GitHubProjectManagerServer()

        # Check that tools are registered
        tools = server.get_available_tools()
        tool_names = [tool.name for tool in tools]

        assert "create_project" in tool_names
        assert "list_projects" in tool_names
        assert len(tools) >= 2  # At least the tools we've implemented

    def test_server_has_tool_handlers(self):
        """Test that server has handlers for all registered tools."""
        server = GitHubProjectManagerServer()

        tools = server.get_available_tools()
        for tool in tools:
            assert server.has_tool_handler(tool.name)

    @pytest.mark.asyncio
    async def test_call_tool_handler_success(self):
        """Test successful tool execution."""
        server = GitHubProjectManagerServer()

        # Mock the handler
        mock_result = CallToolResult(
            content=[TextContent(type="text", text="Success!")], isError=False
        )

        with patch.object(server, "get_tool_handler") as mock_get_handler:
            mock_handler = AsyncMock(return_value=mock_result)
            mock_get_handler.return_value = mock_handler

            result = await server.call_tool("create_project", {"name": "test"})

            assert result == mock_result
            mock_handler.assert_called_once_with({"name": "test"})

    @pytest.mark.asyncio
    async def test_call_tool_handler_unknown_tool(self):
        """Test handling of unknown tool calls."""
        server = GitHubProjectManagerServer()

        result = await server.call_tool("unknown_tool", {})

        assert result.isError is True
        assert "Unknown tool" in result.content[0].text

    @pytest.mark.asyncio
    async def test_call_tool_handler_exception(self):
        """Test handling of exceptions in tool handlers."""
        server = GitHubProjectManagerServer()

        with patch.object(server, "get_tool_handler") as mock_get_handler:
            mock_handler = AsyncMock(side_effect=Exception("Handler error"))
            mock_get_handler.return_value = mock_handler

            result = await server.call_tool("create_project", {"name": "test"})

            assert result.isError is True
            assert "Handler error" in result.content[0].text


class TestServerFactoryFunction:
    """Test cases for the create_server factory function."""

    @pytest.mark.asyncio
    async def test_create_server_with_stdio_transport(self):
        """Test server creation with stdio transport."""
        with patch(
            "github_project_manager_mcp.server.stdio.stdio_server"
        ) as mock_stdio:
            mock_stdio.return_value.__aenter__ = AsyncMock()
            mock_stdio.return_value.__aexit__ = AsyncMock()

            server = await create_server(transport="stdio")

            assert isinstance(server, GitHubProjectManagerServer)
            mock_stdio.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_server_with_sse_transport(self):
        """Test server creation with SSE transport."""
        with patch(
            "github_project_manager_mcp.server.sse.SseServerTransport"
        ) as mock_sse:
            mock_sse.return_value.__aenter__ = AsyncMock()
            mock_sse.return_value.__aexit__ = AsyncMock()

            server = await create_server(transport="sse", host="localhost", port=3001)

            assert isinstance(server, GitHubProjectManagerServer)
            mock_sse.assert_called_once_with("http://localhost:3001/sse")

    @pytest.mark.asyncio
    async def test_create_server_invalid_transport(self):
        """Test server creation with invalid transport."""
        with pytest.raises(ValueError) as exc_info:
            await create_server(transport="invalid")

        assert "Invalid transport" in str(exc_info.value)


class TestServerLifecycle:
    """Test cases for server lifecycle management."""

    @pytest.mark.asyncio
    async def test_server_startup_and_shutdown(self):
        """Test complete server startup and shutdown cycle."""
        server = GitHubProjectManagerServer()

        with patch(
            "github_project_manager_mcp.server.load_github_token",
            return_value="test_token",
        ):
            with patch("github_project_manager_mcp.server.initialize_github_client"):
                # Test startup
                await server.initialize()
                assert server.initialized is True

                # Test shutdown
                await server.shutdown()
                # For now, shutdown might not change initialized state, but it should run without error

    @pytest.mark.asyncio
    async def test_server_handles_multiple_initialization_calls(self):
        """Test that multiple initialization calls are handled gracefully."""
        server = GitHubProjectManagerServer()

        with patch(
            "github_project_manager_mcp.server.load_github_token",
            return_value="test_token",
        ):
            with patch("github_project_manager_mcp.server.initialize_github_client"):
                # First initialization
                await server.initialize()
                assert server.initialized is True

                # Second initialization should not raise error
                await server.initialize()
                assert server.initialized is True


class TestMainFunction:
    """Test cases for the main entry point function."""

    @pytest.mark.asyncio
    async def test_main_function_with_default_args(self):
        """Test main function execution with default arguments."""
        with patch("github_project_manager_mcp.server.create_server") as mock_create:
            mock_server = MagicMock()
            mock_server.run = AsyncMock()
            mock_create.return_value = mock_server

            await main()

            mock_create.assert_called_once_with(transport="stdio")
            mock_server.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_function_with_sse_transport(self):
        """Test main function execution with SSE transport."""
        with patch("github_project_manager_mcp.server.create_server") as mock_create:
            mock_server = MagicMock()
            mock_server.run = AsyncMock()
            mock_create.return_value = mock_server

            await main(transport="sse", host="localhost", port=3001)

            mock_create.assert_called_once_with(
                transport="sse", host="localhost", port=3001
            )
            mock_server.run.assert_called_once()


class TestServerIntegration:
    """Integration test cases for server with real components."""

    @pytest.mark.asyncio
    async def test_server_tool_integration(self):
        """Test that server integrates properly with actual tool handlers."""
        server = GitHubProjectManagerServer()

        # Check that we can get the actual tools
        tools = server.get_available_tools()
        assert len(tools) > 0

        # Check that create_project tool is available
        create_project_tool = next(
            (t for t in tools if t.name == "create_project"), None
        )
        assert create_project_tool is not None
        assert create_project_tool.description is not None
        assert create_project_tool.inputSchema is not None

        # Check that list_projects tool is available
        list_projects_tool = next((t for t in tools if t.name == "list_projects"), None)
        assert list_projects_tool is not None
        assert list_projects_tool.description is not None
        assert list_projects_tool.inputSchema is not None

    @pytest.mark.asyncio
    async def test_server_mcp_protocol_compliance(self):
        """Test that server follows MCP protocol specifications."""
        server = GitHubProjectManagerServer()

        # Test initialize
        init_result = await server.handle_initialize()
        assert isinstance(init_result, InitializeResult)
        assert init_result.serverInfo is not None
        assert init_result.capabilities is not None

        # Test list tools
        tools_result = await server.handle_list_tools()
        assert isinstance(tools_result, ListToolsResult)
        assert len(tools_result.tools) > 0

        # Test that prompts and resources are empty for now
        prompts_result = await server.handle_list_prompts()
        assert isinstance(prompts_result, ListPromptsResult)

        resources_result = await server.handle_list_resources()
        assert isinstance(resources_result, ListResourcesResult)

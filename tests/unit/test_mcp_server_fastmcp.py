"""
Unit tests for GitHub Project Manager MCP FastMCP Server.

Tests the main server initialization, configuration, tool registration,
and error handling for the FastMCP server implementation.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


class TestGitHubProjectManagerMCPFastServer:
    """Test suite for GitHubProjectManagerMCPFastServer class."""

    @pytest.fixture
    def mock_fastmcp(self):
        """Mock FastMCP class."""
        with patch("github_project_manager_mcp.mcp_server_fastmcp.FastMCP") as mock:
            mock_instance = Mock()
            mock_instance.tool = Mock()
            mock_instance.tools = []
            mock_instance.run = Mock()
            mock.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def mock_github_client(self):
        """Mock GitHubClient class."""
        with patch(
            "github_project_manager_mcp.mcp_server_fastmcp.GitHubClient"
        ) as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def mock_load_github_token(self):
        """Mock load_github_token function."""
        with patch(
            "github_project_manager_mcp.mcp_server_fastmcp.load_github_token"
        ) as mock:
            mock.return_value = "test_token"
            yield mock

    @pytest.fixture
    def mock_initialize_handlers(self):
        """Mock all handler initialization functions."""
        with patch(
            "github_project_manager_mcp.mcp_server_fastmcp.initialize_github_client"
        ) as mock1, patch(
            "github_project_manager_mcp.mcp_server_fastmcp.initialize_prd_github_client"
        ) as mock2, patch(
            "github_project_manager_mcp.mcp_server_fastmcp.initialize_task_github_client"
        ) as mock3, patch(
            "github_project_manager_mcp.mcp_server_fastmcp.initialize_subtask_github_client"
        ) as mock4:
            yield mock1, mock2, mock3, mock4

    @pytest.fixture
    def mock_load_dotenv(self):
        """Mock load_dotenv function."""
        with patch("github_project_manager_mcp.mcp_server_fastmcp.load_dotenv") as mock:
            yield mock

    def test_server_initialization_success(self, mock_fastmcp, mock_load_dotenv):
        """Test successful server initialization."""
        from github_project_manager_mcp.mcp_server_fastmcp import (
            GitHubProjectManagerMCPFastServer,
        )

        # Test server creation
        server = GitHubProjectManagerMCPFastServer()

        # Verify basic initialization
        assert server.config is not None
        assert "mcp_server" in server.config
        assert "github" in server.config
        assert "logging" in server.config

        # Verify FastMCP was created
        assert server.mcp is not None

        # Verify async components are not yet initialized
        assert server._async_initialized is False
        assert server.github_client is None

    def test_server_initialization_with_config_path(
        self, mock_fastmcp, mock_load_dotenv
    ):
        """Test server initialization with custom config path."""
        from github_project_manager_mcp.mcp_server_fastmcp import (
            GitHubProjectManagerMCPFastServer,
        )

        server = GitHubProjectManagerMCPFastServer(config_path="/custom/config.yaml")

        # Should still use default config since YAML loading isn't implemented
        assert server.config is not None
        assert server.config["github"]["base_url"] == "https://api.github.com/graphql"

    def test_load_config_default(self, mock_fastmcp, mock_load_dotenv):
        """Test _load_config method with default configuration."""
        from github_project_manager_mcp.mcp_server_fastmcp import (
            GitHubProjectManagerMCPFastServer,
        )

        server = GitHubProjectManagerMCPFastServer()
        config = server._load_config()

        # Verify default config structure
        assert "mcp_server" in config
        assert "github" in config
        assert "logging" in config
        assert config["github"]["base_url"] == "https://api.github.com/graphql"
        assert config["logging"]["level"] == "DEBUG"

    def test_setup_logging(self, mock_fastmcp, mock_load_dotenv):
        """Test _setup_logging method."""
        from github_project_manager_mcp.mcp_server_fastmcp import (
            GitHubProjectManagerMCPFastServer,
        )

        server = GitHubProjectManagerMCPFastServer()

        # Should not raise any exceptions
        server._setup_logging()

        # Verify logging level was set
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_init_sync_components(self, mock_fastmcp, mock_load_dotenv):
        """Test _init_sync_components method."""
        from github_project_manager_mcp.mcp_server_fastmcp import (
            GitHubProjectManagerMCPFastServer,
        )

        server = GitHubProjectManagerMCPFastServer()
        server._init_sync_components()

        # Verify GitHub config was set
        assert server.github_config is not None
        assert "base_url" in server.github_config

        # Verify async initialization flags
        assert server._async_initialized is False
        assert server.github_client is None

    @pytest.mark.asyncio
    async def test_ensure_async_initialized_success(
        self,
        mock_fastmcp,
        mock_load_dotenv,
        mock_github_client,
        mock_load_github_token,
        mock_initialize_handlers,
    ):
        """Test successful async initialization."""
        from github_project_manager_mcp.mcp_server_fastmcp import (
            GitHubProjectManagerMCPFastServer,
        )

        server = GitHubProjectManagerMCPFastServer()

        # Call async initialization
        await server._ensure_async_initialized()

        # Verify initialization completed
        assert server._async_initialized is True
        assert server.github_client is not None

        # Verify token was loaded
        mock_load_github_token.assert_called_once()

        # Verify handlers were initialized
        mock1, mock2, mock3, mock4 = mock_initialize_handlers
        mock1.assert_called_once_with("test_token")
        mock2.assert_called_once_with("test_token")
        mock3.assert_called_once_with("test_token")
        mock4.assert_called_once_with("test_token")

    @pytest.mark.asyncio
    async def test_ensure_async_initialized_no_token(
        self, mock_fastmcp, mock_load_dotenv
    ):
        """Test async initialization with no GitHub token."""
        from github_project_manager_mcp.mcp_server_fastmcp import (
            GitHubProjectManagerMCPFastServer,
        )

        with patch(
            "github_project_manager_mcp.mcp_server_fastmcp.load_github_token"
        ) as mock_token:
            mock_token.return_value = None

            server = GitHubProjectManagerMCPFastServer()
            await server._ensure_async_initialized()

            # Should complete without error but with no GitHub client
            assert server._async_initialized is True
            assert server.github_client is None

    @pytest.mark.asyncio
    async def test_ensure_async_initialized_error_handling(
        self, mock_fastmcp, mock_load_dotenv
    ):
        """Test async initialization error handling."""
        from github_project_manager_mcp.mcp_server_fastmcp import (
            GitHubProjectManagerMCPFastServer,
        )

        with patch(
            "github_project_manager_mcp.mcp_server_fastmcp.load_github_token"
        ) as mock_token:
            mock_token.side_effect = Exception("Token loading failed")

            server = GitHubProjectManagerMCPFastServer()

            # Should raise the exception
            with pytest.raises(Exception, match="Token loading failed"):
                await server._ensure_async_initialized()

    @pytest.mark.asyncio
    async def test_ensure_async_initialized_idempotent(
        self,
        mock_fastmcp,
        mock_load_dotenv,
        mock_github_client,
        mock_load_github_token,
        mock_initialize_handlers,
    ):
        """Test that async initialization is idempotent."""
        from github_project_manager_mcp.mcp_server_fastmcp import (
            GitHubProjectManagerMCPFastServer,
        )

        server = GitHubProjectManagerMCPFastServer()

        # Call multiple times
        await server._ensure_async_initialized()
        await server._ensure_async_initialized()
        await server._ensure_async_initialized()

        # Should only initialize once
        mock_load_github_token.assert_called_once()

    def test_register_tools(self, mock_fastmcp, mock_load_dotenv):
        """Test tool registration."""
        from github_project_manager_mcp.mcp_server_fastmcp import (
            GitHubProjectManagerMCPFastServer,
        )

        server = GitHubProjectManagerMCPFastServer()

        # Tool decorator should be called multiple times for different tools
        assert mock_fastmcp.tool.call_count > 0

        # Verify the mock FastMCP instance is properly set up
        assert server.mcp is mock_fastmcp

    @pytest.mark.asyncio
    async def test_test_connection_tool(self, mock_fastmcp, mock_load_dotenv):
        """Test the test_connection tool functionality."""
        from github_project_manager_mcp.mcp_server_fastmcp import (
            GitHubProjectManagerMCPFastServer,
        )

        server = GitHubProjectManagerMCPFastServer()

        # Find the test_connection tool function
        tool_calls = mock_fastmcp.tool.call_args_list
        test_connection_func = None

        for call in tool_calls:
            # The tool decorator is called with the function as argument
            if call[0]:  # If there are positional arguments
                func = call[0][0]
                if hasattr(func, "__name__") and func.__name__ == "test_connection":
                    test_connection_func = func
                    break

        if test_connection_func:
            # Test the function
            result = await test_connection_func("test message")
            assert "GitHub Project Manager MCP Server is running" in result
            assert "test message" in result

    def test_server_initialization_fastmcp_import_error(self, mock_load_dotenv):
        """Test server initialization when FastMCP import fails."""
        with patch(
            "github_project_manager_mcp.mcp_server_fastmcp.FastMCP"
        ) as mock_fastmcp:
            mock_fastmcp.side_effect = ImportError("FastMCP not found")

            from github_project_manager_mcp.mcp_server_fastmcp import (
                GitHubProjectManagerMCPFastServer,
            )

            # Should raise the import error during initialization
            with pytest.raises(ImportError, match="FastMCP not found"):
                GitHubProjectManagerMCPFastServer()

    def test_logging_setup_with_custom_level(self, mock_fastmcp, mock_load_dotenv):
        """Test logging setup with custom level."""
        from github_project_manager_mcp.mcp_server_fastmcp import (
            GitHubProjectManagerMCPFastServer,
        )

        server = GitHubProjectManagerMCPFastServer()

        # Modify config to use INFO level
        server.config["logging"]["level"] = "INFO"
        server._setup_logging()

        # Verify logging level was set correctly
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO

    def test_github_config_initialization(self, mock_fastmcp, mock_load_dotenv):
        """Test GitHub configuration initialization."""
        from github_project_manager_mcp.mcp_server_fastmcp import (
            GitHubProjectManagerMCPFastServer,
        )

        server = GitHubProjectManagerMCPFastServer()

        # Verify GitHub config was extracted correctly
        assert server.github_config["base_url"] == "https://api.github.com/graphql"


class TestMainFunction:
    """Test suite for the main() function."""

    @pytest.fixture
    def mock_server_class(self):
        """Mock the GitHubProjectManagerMCPFastServer class."""
        with patch(
            "github_project_manager_mcp.mcp_server_fastmcp.GitHubProjectManagerMCPFastServer"
        ) as mock:
            mock_instance = Mock()
            mock_instance.mcp = Mock()
            mock_instance.mcp.run = Mock()
            mock.return_value = mock_instance
            yield mock

    @pytest.fixture
    def mock_argparse(self):
        """Mock argparse."""
        with patch(
            "github_project_manager_mcp.mcp_server_fastmcp.argparse.ArgumentParser"
        ) as mock:
            parser_instance = Mock()
            args_instance = Mock()
            args_instance.debug = False
            args_instance.config = None
            parser_instance.parse_args.return_value = args_instance
            mock.return_value = parser_instance
            yield parser_instance, args_instance

    def test_main_success(self, mock_server_class, mock_argparse):
        """Test successful main function execution."""
        from github_project_manager_mcp.mcp_server_fastmcp import main

        parser_mock, args_mock = mock_argparse

        # Call main
        main()

        # Verify argument parsing
        parser_mock.add_argument.assert_any_call(
            "--debug", action="store_true", help="Enable debug logging"
        )
        parser_mock.add_argument.assert_any_call(
            "--config", type=str, help="Path to configuration file"
        )
        parser_mock.parse_args.assert_called_once()

        # Verify server creation and startup
        mock_server_class.assert_called_once_with(config_path=None)
        mock_server_class.return_value.mcp.run.assert_called_once()

    def test_main_with_debug_flag(self, mock_server_class, mock_argparse):
        """Test main function with debug flag."""
        from github_project_manager_mcp.mcp_server_fastmcp import main

        parser_mock, args_mock = mock_argparse
        args_mock.debug = True

        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            main()

            # Verify debug logging was enabled
            mock_logger.setLevel.assert_called_with(logging.DEBUG)

    def test_main_with_config_path(self, mock_server_class, mock_argparse):
        """Test main function with custom config path."""
        from github_project_manager_mcp.mcp_server_fastmcp import main

        parser_mock, args_mock = mock_argparse
        args_mock.config = "/custom/config.yaml"

        main()

        # Verify server was created with custom config path
        mock_server_class.assert_called_once_with(config_path="/custom/config.yaml")

    def test_main_keyboard_interrupt(self, mock_server_class, mock_argparse):
        """Test main function handling KeyboardInterrupt."""
        from github_project_manager_mcp.mcp_server_fastmcp import main

        parser_mock, args_mock = mock_argparse
        mock_server_class.return_value.mcp.run.side_effect = KeyboardInterrupt()

        # Should not raise exception
        main()

        # Server should still be created
        mock_server_class.assert_called_once()

    def test_main_server_error(self, mock_server_class, mock_argparse):
        """Test main function handling server errors."""
        from github_project_manager_mcp.mcp_server_fastmcp import main

        parser_mock, args_mock = mock_argparse
        mock_server_class.side_effect = Exception("Server initialization failed")

        # Should exit with error code 1
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    def test_main_server_run_error(self, mock_server_class, mock_argparse):
        """Test main function handling server run errors."""
        from github_project_manager_mcp.mcp_server_fastmcp import main

        parser_mock, args_mock = mock_argparse
        mock_server_class.return_value.mcp.run.side_effect = Exception(
            "Server run failed"
        )

        # Should exit with error code 1
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1


class TestServerToolIntegration:
    """Test suite for server tool integration."""

    @pytest.fixture
    def server_with_mocks(self):
        """Create server instance with necessary mocks."""
        with patch(
            "github_project_manager_mcp.mcp_server_fastmcp.FastMCP"
        ) as mock_fastmcp, patch(
            "github_project_manager_mcp.mcp_server_fastmcp.load_dotenv"
        ):

            mock_instance = Mock()
            mock_instance.tool = Mock()
            mock_instance.tools = []
            mock_fastmcp.return_value = mock_instance

            from github_project_manager_mcp.mcp_server_fastmcp import (
                GitHubProjectManagerMCPFastServer,
            )

            server = GitHubProjectManagerMCPFastServer()

            yield server, mock_instance

    @pytest.mark.asyncio
    async def test_tool_error_handling_no_github_client(self, server_with_mocks):
        """Test that tools handle missing GitHub client gracefully."""
        server, mock_fastmcp = server_with_mocks

        # Ensure GitHub client is not initialized
        server.github_client = None
        server._async_initialized = True

        # Find a tool function (like create_project) and test it
        tool_calls = mock_fastmcp.tool.call_args_list
        for call in tool_calls:
            if call[0]:  # If there are positional arguments
                func = call[0][0]
                if hasattr(func, "__name__") and "project" in func.__name__:
                    # Test the function with minimal args
                    if func.__name__ == "create_project":
                        result = await func("test", "repo")
                        assert "GitHub client not initialized" in result
                        break

    def test_tool_count_verification(self, server_with_mocks):
        """Test that the expected number of tools are registered."""
        server, mock_fastmcp = server_with_mocks

        # Verify that tool() decorator was called multiple times
        # We expect tools for: test_connection, create_project, list_projects,
        # delete_project, get_project_details, update_project, list_prds_in_project,
        # update_prd, add_prd_to_project, delete_prd_from_project, update_prd_status,
        # update_task, create_task, list_tasks, delete_task, add_subtask, list_subtasks
        expected_min_tools = 15  # Minimum expected tools
        assert mock_fastmcp.tool.call_count >= expected_min_tools

    def test_server_logging_integration(self, server_with_mocks):
        """Test that server properly integrates with logging system."""
        server, mock_fastmcp = server_with_mocks

        # Verify that logger is set up and accessible
        from github_project_manager_mcp.mcp_server_fastmcp import logger

        assert logger is not None
        assert logger.name == "github_project_manager_mcp.mcp_server_fastmcp"

"""
Main MCP server implementation for GitHub Project Manager.

This module implements the core MCP server that handles tool registration,
request routing, and transport management for GitHub Projects v2 integration.
"""

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional

from mcp import InitializeResult, ServerCapabilities
from mcp.server import NotificationOptions, Server, sse, stdio
from mcp.server.models import InitializationOptions
from mcp.types import (
    CallToolResult,
    Implementation,
    ListPromptsResult,
    ListResourcesResult,
    ListToolsResult,
    PromptsCapability,
    ResourcesCapability,
    TextContent,
    Tool,
    ToolsCapability,
)

from .handlers.project_handlers import (
    PROJECT_TOOL_HANDLERS,
    PROJECT_TOOLS,
    initialize_github_client,
)
from .utils.auth import load_github_token

logger = logging.getLogger(__name__)


class GitHubProjectManagerServer:
    """
    Main MCP server for GitHub Project Manager.

    This server provides MCP-compliant tool interfaces for managing GitHub Projects v2,
    including project creation, listing, task management, and workflow automation.
    """

    def __init__(self):
        """Initialize the GitHub Project Manager MCP server."""
        self.mcp_server = Server("github-project-manager")
        self.github_token: Optional[str] = None
        self.initialized: bool = False

        # Register MCP handlers
        self._register_mcp_handlers()

        logger.info("GitHubProjectManagerServer initialized")

    def _register_mcp_handlers(self):
        """Register MCP protocol handlers with the server."""

        @self.mcp_server.call_tool()
        async def call_tool_handler(
            name: str, arguments: Dict[str, Any]
        ) -> CallToolResult:
            """Handle MCP tool calls."""
            return await self.call_tool(name, arguments)

        @self.mcp_server.list_tools()
        async def list_tools_handler() -> ListToolsResult:
            """Handle MCP list_tools requests."""
            return await self.handle_list_tools()

        @self.mcp_server.list_prompts()
        async def list_prompts_handler() -> ListPromptsResult:
            """Handle MCP list_prompts requests."""
            return await self.handle_list_prompts()

        @self.mcp_server.list_resources()
        async def list_resources_handler() -> ListResourcesResult:
            """Handle MCP list_resources requests."""
            return await self.handle_list_resources()

        logger.debug("MCP handlers registered")

    async def initialize(self) -> None:
        """
        Initialize the server with GitHub authentication and setup.

        Raises:
            ValueError: If GitHub token is not found or invalid
        """
        if self.initialized:
            logger.info("Server already initialized")
            return

        # Load GitHub token
        self.github_token = load_github_token()
        if not self.github_token:
            raise ValueError(
                "GitHub token not found. Please set GITHUB_TOKEN environment variable."
            )

        # Initialize GitHub client for handlers
        initialize_github_client(self.github_token)

        self.initialized = True
        logger.info("Server initialized successfully")

    async def shutdown(self) -> None:
        """Shutdown the server and cleanup resources."""
        logger.info("Shutting down GitHub Project Manager server")
        # Add any cleanup logic here if needed

    def get_available_tools(self) -> List[Tool]:
        """Get all available MCP tools."""
        return PROJECT_TOOLS.copy()

    def has_tool_handler(self, tool_name: str) -> bool:
        """Check if a tool handler exists for the given tool name."""
        return tool_name in PROJECT_TOOL_HANDLERS

    def get_tool_handler(
        self, tool_name: str
    ) -> Optional[Callable[[Dict[str, Any]], Awaitable[CallToolResult]]]:
        """Get the handler function for a tool."""
        return PROJECT_TOOL_HANDLERS.get(tool_name)

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> CallToolResult:
        """
        Execute a tool call.

        Args:
            name: Tool name to execute
            arguments: Tool arguments

        Returns:
            CallToolResult with execution results
        """
        try:
            # Check if tool exists
            if not self.has_tool_handler(name):
                return CallToolResult(
                    content=[
                        TextContent(type="text", text=f"Error: Unknown tool '{name}'")
                    ],
                    isError=True,
                )

            # Get and execute handler
            handler = self.get_tool_handler(name)
            if handler is None:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Error: No handler found for tool '{name}'",
                        )
                    ],
                    isError=True,
                )

            logger.info(f"Executing tool '{name}' with arguments: {arguments}")
            result = await handler(arguments)

            logger.debug(f"Tool '{name}' execution completed")
            return result

        except Exception as e:
            logger.error(f"Error executing tool '{name}': {e}", exc_info=True)
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text=f"Error executing tool '{name}': {str(e)}"
                    )
                ],
                isError=True,
            )

    async def handle_initialize(self) -> InitializeResult:
        """Handle MCP initialize requests."""
        return InitializeResult(
            protocolVersion="2024-11-05",
            serverInfo=Implementation(name="github-project-manager", version="1.0.0"),
            capabilities=ServerCapabilities(
                tools=ToolsCapability(listChanged=True),
                prompts=PromptsCapability(listChanged=True),
                resources=ResourcesCapability(listChanged=True, subscribe=False),
            ),
        )

    async def handle_list_tools(self) -> ListToolsResult:
        """Handle MCP list_tools requests."""
        tools = self.get_available_tools()
        logger.debug(f"Returning {len(tools)} available tools")
        return ListToolsResult(tools=tools)

    async def handle_list_prompts(self) -> ListPromptsResult:
        """Handle MCP list_prompts requests."""
        # For now, no prompts are available
        return ListPromptsResult(prompts=[])

    async def handle_list_resources(self) -> ListResourcesResult:
        """Handle MCP list_resources requests."""
        # For now, no resources are available
        return ListResourcesResult(resources=[])


async def create_server(
    transport: str = "stdio", **kwargs
) -> GitHubProjectManagerServer:
    """
    Factory function to create and configure a GitHub Project Manager server.

    Args:
        transport: Transport type ("stdio" or "sse")
        **kwargs: Additional transport configuration

    Returns:
        Configured GitHubProjectManagerServer instance

    Raises:
        ValueError: If transport type is invalid
    """
    if transport not in ["stdio", "sse"]:
        raise ValueError(f"Invalid transport: {transport}. Must be 'stdio' or 'sse'")

    server = GitHubProjectManagerServer()

    logger.info(f"Created GitHub Project Manager server with {transport} transport")
    return server


async def main(transport: str = "stdio", **kwargs) -> None:
    """
    Main entry point for the GitHub Project Manager MCP server.

    Args:
        transport: Transport type ("stdio" or "sse")
        **kwargs: Additional configuration options
    """
    try:
        server = await create_server(transport=transport, **kwargs)
        await server.initialize()
        logger.info("GitHub Project Manager MCP server started")

        # Keep server running
        if transport == "stdio":
            # For stdio, we'd typically run with the MCP library's stdio handler
            pass
        elif transport == "sse":
            # For SSE, we'd set up HTTP server
            pass

    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GitHub Project Manager MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport type to use",
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host for SSE transport (default: localhost)",
    )
    parser.add_argument(
        "--port", type=int, default=3001, help="Port for SSE transport (default: 3001)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level (default: INFO)",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the server
    asyncio.run(main(transport=args.transport, host=args.host, port=args.port))

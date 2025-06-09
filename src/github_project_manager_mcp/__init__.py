"""
GitHub Project Manager MCP Server

A Model Context Protocol (MCP) server for GitHub project management,
enabling automated PRD, task, and subtask management workflows.
"""

from typing import List

__version__ = "0.1.0"
__author__ = "GitHub Project Manager MCP"
__email__ = "dev@example.com"
__description__ = (
    "A Model Context Protocol (MCP) server for GitHub project management, "
    "enabling automated PRD, task, and subtask management workflows"
)

# Package information
__title__ = "github-project-manager-mcp"
__license__ = "MIT"
__copyright__ = "2024, GitHub Project Manager MCP"

# FastMCP server is the main implementation (mcp_server_fastmcp.py)
# Legacy server.py has been removed for simplicity
main = None

__all__: List[str] = [
    "__version__",
    "__author__",
    "__email__",
    "__description__",
    "__title__",
    "__license__",
    "__copyright__",
    "main",
]

"""
MCP Tool Handlers

This module contains the MCP tool handlers for various GitHub project
management operations.
"""

from typing import List

# Import handlers when they're available
try:
    from .project_handlers import (
        PROJECT_TOOL_HANDLERS,
        PROJECT_TOOLS,
        initialize_github_client,
    )

    PROJECT_IMPORTS = [
        "PROJECT_TOOLS",
        "PROJECT_TOOL_HANDLERS",
        "initialize_github_client",
    ]
except ImportError:
    PROJECT_IMPORTS = []

# try:
#     from .prd_handlers import *
#     from .task_handlers import *
#     from .subtask_handlers import *
# except ImportError:
#     # Handler modules not yet implemented
#     pass

__all__: List[str] = PROJECT_IMPORTS + [
    # Will be populated as more handlers are implemented
]

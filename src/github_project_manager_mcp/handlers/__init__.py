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

try:
    from .project_search_handlers import (
        SEARCH_PROJECT_TOOL_HANDLERS,
        SEARCH_PROJECT_TOOLS,
    )

    SEARCH_IMPORTS = [
        "SEARCH_PROJECT_TOOLS",
        "SEARCH_PROJECT_TOOL_HANDLERS",
    ]
except ImportError:
    SEARCH_IMPORTS = []

# try:
#     from .prd_handlers import *
#     from .task_handlers import *
#     from .subtask_handlers import *
# except ImportError:
#     # Handler modules not yet implemented
#     pass

__all__: List[str] = (
    PROJECT_IMPORTS
    + SEARCH_IMPORTS
    + [
        # Will be populated as more handlers are implemented
    ]
)

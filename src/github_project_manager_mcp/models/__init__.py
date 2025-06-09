"""
Data Models

This module contains the data models for GitHub project management entities.
"""

from typing import List

# Import models when they're available
try:
    from .project import (
        Project,
        ProjectField,
        ProjectFieldConfiguration,
        ProjectFieldIteration,
        ProjectFieldOption,
        ProjectVisibility,
    )

    PROJECT_IMPORTS = [
        "Project",
        "ProjectVisibility",
        "ProjectField",
        "ProjectFieldOption",
        "ProjectFieldIteration",
        "ProjectFieldConfiguration",
    ]
except ImportError:
    PROJECT_IMPORTS = []

# try:
#     from .prd import *
#     from .task import *
#     from .subtask import *
# except ImportError:
#     # Model modules not yet implemented
#     pass

__all__: List[str] = [
    *PROJECT_IMPORTS,
    # Will be populated as models are implemented
]

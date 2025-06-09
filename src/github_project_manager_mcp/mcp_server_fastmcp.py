#!/usr/bin/env python3
"""
GitHub Project Manager MCP Server using FastMCP

This is a FastMCP server implementation that should work well with Cursor.
"""

import argparse
import asyncio
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Configure file logging first
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"mcp_server_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Setup both file and console logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stderr),  # Log to stderr, not stdout
    ],
)
logger = logging.getLogger(__name__)

# Log startup information
logger.info("=" * 60)
logger.info("GITHUB PROJECT MANAGER MCP SERVER STARTUP")
logger.info("=" * 60)
logger.info(f"Python executable: {sys.executable}")
logger.info(f"Python version: {sys.version}")
logger.info(f"Python path: {sys.path}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"Project root: {project_root}")
logger.info(f"Log file: {log_file}")
logger.info(f"Environment variables:")
for key, value in os.environ.items():
    if "PYTHON" in key.upper() or "PATH" in key.upper() or "GITHUB" in key.upper():
        logger.info(
            f"  {key}: {value[:50]}..." if len(value) > 50 else f"  {key}: {value}"
        )

try:
    from mcp.server.fastmcp import FastMCP

    logger.info("Successfully imported FastMCP")
except ImportError as e:
    logger.error(f"Failed to import FastMCP: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    sys.exit(1)

try:
    from dotenv import load_dotenv

    logger.info("Successfully imported dotenv")
except ImportError as e:
    logger.error(f"Failed to import dotenv: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    sys.exit(1)

# Import our modules
try:
    from github_project_manager_mcp.github_client import GitHubClient

    logger.info("Successfully imported GitHubClient")
except ImportError as e:
    logger.error(f"Failed to import GitHubClient: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    sys.exit(1)

try:
    from github_project_manager_mcp.handlers.project_handlers import (
        create_project_handler,
        delete_project_handler,
        get_project_details_handler,
        initialize_github_client,
        list_projects_handler,
        update_project_handler,
    )

    logger.info("Successfully imported project handlers")
except ImportError as e:
    logger.error(f"Failed to import project handlers: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    sys.exit(1)

try:
    from github_project_manager_mcp.handlers.prd_handlers import (
        add_prd_to_project_handler,
        delete_prd_from_project_handler,
    )
    from github_project_manager_mcp.handlers.prd_handlers import (
        initialize_github_client as initialize_prd_github_client,
    )
    from github_project_manager_mcp.handlers.prd_handlers import (
        list_prds_in_project_handler,
        update_prd_handler,
        update_prd_status_handler,
    )

    logger.info("Successfully imported PRD handlers")
except ImportError as e:
    logger.error(f"Failed to import PRD handlers: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    sys.exit(1)

try:
    from github_project_manager_mcp.handlers.task_handlers import (
        create_task_handler,
        delete_task_handler,
    )
    from github_project_manager_mcp.handlers.task_handlers import (
        initialize_github_client as initialize_task_github_client,
    )
    from github_project_manager_mcp.handlers.task_handlers import (
        list_tasks_handler,
        update_task_handler,
    )

    logger.info("Successfully imported task handlers")
except ImportError as e:
    logger.error(f"Failed to import task handlers: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    sys.exit(1)

try:
    from github_project_manager_mcp.handlers.subtask_handlers import add_subtask_handler
    from github_project_manager_mcp.handlers.subtask_handlers import (
        initialize_github_client as initialize_subtask_github_client,
    )
    from github_project_manager_mcp.handlers.subtask_handlers import (
        list_subtasks_handler,
    )

    logger.info("Successfully imported subtask handlers")
except ImportError as e:
    logger.error(f"Failed to import subtask handlers: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    sys.exit(1)

try:
    from github_project_manager_mcp.utils.auth import load_github_token

    logger.info("Successfully imported auth utils")
except ImportError as e:
    logger.error(f"Failed to import auth utils: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    sys.exit(1)

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded")


class GitHubProjectManagerMCPFastServer:
    """GitHub Project Manager MCP Server using FastMCP."""

    def __init__(self, config_path: str = None):
        logger.info("Initializing GitHubProjectManagerMCPFastServer...")

        try:
            self.config = self._load_config(config_path)
            logger.info(f"Configuration loaded: {self.config}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

        try:
            self._setup_logging()
            logger.info("Logging setup complete")
        except Exception as e:
            logger.error(f"Failed to setup logging: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

        try:
            # Initialize FastMCP Server
            self.mcp = FastMCP("github-project-manager-mcp")
            logger.info("FastMCP server created successfully")
        except Exception as e:
            logger.error(f"Failed to create FastMCP server: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

        try:
            # Initialize components that can be done synchronously
            self._init_sync_components()
            logger.info("Sync components initialized")
        except Exception as e:
            logger.error(f"Failed to initialize sync components: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

        try:
            # Register tools
            self._register_tools()
            logger.info("All MCP tools registered successfully with FastMCP")
        except Exception as e:
            logger.error(f"Failed to register tools: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

        logger.info("GitHubProjectManagerMCPFastServer initialization complete")

    def _load_config(self, config_path: str = None) -> dict:
        """Load configuration from file or use defaults."""
        logger.info("Loading config...")

        # For now, use default config since we don't have YAML yet
        config = {
            "mcp_server": {"host": "localhost", "port": 8000},
            "github": {"base_url": "https://api.github.com/graphql"},
            "logging": {"level": "DEBUG"},
        }
        logger.info(f"Using default config: {config}")
        return config

    def _setup_logging(self):
        """Setup logging based on configuration."""
        log_config = self.config.get("logging", {})
        level = getattr(logging, log_config.get("level", "DEBUG"))

        logging.getLogger().setLevel(level)
        logger.info("GitHub Project Manager MCP Server logging initialized")

    def _init_sync_components(self):
        """Initialize components that can be done synchronously."""
        logger.info("Initializing GitHub Project Manager MCP FastMCP Server...")

        # Initialize GitHub client configuration
        self.github_config = self.config.get(
            "github", {"base_url": "https://api.github.com/graphql"}
        )
        logger.info(f"GitHub config: {self.github_config}")

        # Mark that async components need initialization
        self._async_initialized = False
        self.github_client = None

        logger.info(
            "GitHub Project Manager FastMCP server sync initialization complete"
        )

    async def _ensure_async_initialized(self):
        """Ensure async components are initialized (lazy initialization)."""
        if self._async_initialized:
            return

        logger.info("Initializing async components...")

        try:
            # Load GitHub token
            github_token = load_github_token()
            if not github_token:
                logger.warning("No GitHub token found. Some operations may fail.")
            else:
                logger.info("GitHub token loaded successfully")

            # Initialize GitHub client
            if github_token:
                self.github_client = GitHubClient(
                    token=github_token,
                    base_url=self.github_config.get("base_url"),
                    rate_limit_enabled=True,
                )
                # Also initialize the global client for handlers
                initialize_github_client(github_token)
                initialize_prd_github_client(github_token)
                initialize_task_github_client(github_token)
                initialize_subtask_github_client(github_token)
                logger.info(
                    "GitHub client initialized successfully for project, PRD, task, and subtask handlers"
                )
            else:
                logger.warning("GitHub client not initialized - no token available")

            self._async_initialized = True
            logger.info("Async components initialization complete")

        except Exception as e:
            logger.error(f"Failed to initialize async components: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def _register_tools(self):
        """Register all MCP tools with FastMCP."""
        logger.info("Registering MCP tools...")

        # Test connection tool
        @self.mcp.tool()
        async def test_connection(message: str = "No message provided") -> str:
            """Test the MCP server connection."""
            logger.info(f"Test connection called with message: {message}")
            return f"GitHub Project Manager MCP Server is running! Received: {message}"

        # Create project tool
        @self.mcp.tool()
        async def create_project(
            name: str,
            repository: str,
            description: str = "",
            visibility: str = "PRIVATE",
        ) -> str:
            """Create a new GitHub project for a repository."""
            logger.info(
                f"Create project called: name={name}, description={description}, repository={repository}, visibility={visibility}"
            )

            try:
                await self._ensure_async_initialized()

                if not self.github_client:
                    return '{"success": false, "error": "GitHub client not initialized - check token configuration"}'

                # Call the existing create project handler
                args = {
                    "name": name,
                    "description": description,
                    "repository": repository,
                    "visibility": visibility,
                }

                result = await create_project_handler(args)
                logger.info(f"Create project result: {result}")

                # Extract text content from CallToolResult
                if hasattr(result, "content") and result.content:
                    return result.content[0].text
                else:
                    return str(result)

            except Exception as e:
                logger.error(f"Error in create_project: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return f'{{"success": false, "error": "Failed to create project: {str(e)}"}}'

        # List projects tool
        @self.mcp.tool()
        async def list_projects(owner: str, limit: int = 10, after: str = None) -> str:
            """List GitHub projects for a user or organization."""
            logger.info(
                f"List projects called: owner={owner}, limit={limit}, after={after}"
            )

            try:
                await self._ensure_async_initialized()

                if not self.github_client:
                    return '{"success": false, "error": "GitHub client not initialized - check token configuration"}'

                # Call the existing list projects handler
                args = {
                    "owner": owner,
                    "first": limit,  # Note: the handler expects 'first', not 'limit'
                }
                if after:
                    args["after"] = after

                result = await list_projects_handler(args)
                logger.info(f"List projects result: {result}")

                # Extract text content from CallToolResult
                if hasattr(result, "content") and result.content:
                    return result.content[0].text
                else:
                    return str(result)

            except Exception as e:
                logger.error(f"Error in list_projects: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return f'{{"success": false, "error": "Failed to list projects: {str(e)}"}}'

        # Delete project tool
        @self.mcp.tool()
        async def delete_project(project_id: str, confirm: bool) -> str:
            """Delete a GitHub project by ID. This action is permanent and cannot be undone."""
            logger.info(
                f"Delete project called: project_id={project_id}, confirm={confirm}"
            )

            try:
                await self._ensure_async_initialized()

                if not self.github_client:
                    return '{"success": false, "error": "GitHub client not initialized - check token configuration"}'

                # Call the existing delete project handler
                args = {
                    "project_id": project_id,
                    "confirm": confirm,
                }

                result = await delete_project_handler(args)
                logger.info(f"Delete project result: {result}")

                # Extract text content from CallToolResult
                if hasattr(result, "content") and result.content:
                    return result.content[0].text
                else:
                    return str(result)

            except Exception as e:
                logger.error(f"Error in delete_project: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return f'{{"success": false, "error": "Failed to delete project: {str(e)}"}}'

        # Get project details tool
        @self.mcp.tool()
        async def get_project_details(project_id: str) -> str:
            """Retrieve detailed information about a GitHub Project v2 by ID."""
            logger.info(f"Get project details called: project_id={project_id}")

            try:
                await self._ensure_async_initialized()

                if not self.github_client:
                    return '{"success": false, "error": "GitHub client not initialized - check token configuration"}'

                # Call the existing get project details handler
                args = {
                    "project_id": project_id,
                }

                result = await get_project_details_handler(args)
                logger.info(f"Get project details result: {result}")

                # Extract text content from CallToolResult
                if hasattr(result, "content") and result.content:
                    return result.content[0].text
                else:
                    return str(result)

            except Exception as e:
                logger.error(f"Error in get_project_details: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return f'{{"success": false, "error": "Failed to get project details: {str(e)}"}}'

        # Update project tool
        @self.mcp.tool()
        async def update_project(
            project_id: str,
            title: str = None,
            short_description: str = None,
            readme: str = None,
            public: bool = None,
        ) -> str:
            """Update a GitHub Projects v2 project metadata including name, description, visibility, and README."""
            logger.info(
                f"Update project called: project_id={project_id}, title={title}, short_description={short_description}, public={public}"
            )

            try:
                await self._ensure_async_initialized()

                if not self.github_client:
                    return '{"success": false, "error": "GitHub client not initialized - check token configuration"}'

                # Call the existing update project handler
                args = {
                    "project_id": project_id,
                }

                # Add optional fields if provided
                if title:
                    args["title"] = title
                if short_description:
                    args["short_description"] = short_description
                if readme:
                    args["readme"] = readme
                if public is not None:
                    args["public"] = public

                result = await update_project_handler(args)
                logger.info(f"Update project result: {result}")

                # Extract text content from CallToolResult
                if hasattr(result, "content") and result.content:
                    return result.content[0].text
                else:
                    return str(result)

            except Exception as e:
                logger.error(f"Error in update_project: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return f'{{"success": false, "error": "Failed to update project: {str(e)}"}}'

        # List PRDs in project tool
        @self.mcp.tool()
        async def list_prds_in_project(
            project_id: str, first: int = 25, after: str = None
        ) -> str:
            """List all Product Requirements Documents (PRDs) within a GitHub project with filtering and pagination support."""
            logger.info(
                f"List PRDs in project called: project_id={project_id}, first={first}, after={after}"
            )

            try:
                await self._ensure_async_initialized()

                if not self.github_client:
                    return '{"success": false, "error": "GitHub client not initialized - check token configuration"}'

                # Call the existing list PRDs in project handler
                args = {
                    "project_id": project_id,
                    "first": first,
                }

                # Add optional after cursor if provided
                if after:
                    args["after"] = after

                result = await list_prds_in_project_handler(args)
                logger.info(f"List PRDs in project result: {result}")

                # Extract text content from CallToolResult
                if hasattr(result, "content") and result.content:
                    return result.content[0].text
                else:
                    return str(result)

            except Exception as e:
                logger.error(f"Error in list_prds_in_project: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return f'{{"success": false, "error": "Failed to list PRDs in project: {str(e)}"}}'

        # Update PRD tool
        @self.mcp.tool()
        async def update_prd(
            prd_item_id: str,
            title: str = None,
            body: str = None,
            assignee_ids: list = None,
        ) -> str:
            """Update a Product Requirements Document (PRD) in a GitHub project."""
            logger.info(
                f"Update PRD called: prd_item_id={prd_item_id}, title={title}, body={body}, assignee_ids={assignee_ids}"
            )

            try:
                await self._ensure_async_initialized()

                if not self.github_client:
                    return '{"success": false, "error": "GitHub client not initialized - check token configuration"}'

                # Call the existing update PRD handler
                args = {
                    "prd_item_id": prd_item_id,
                }

                # Add optional parameters if provided
                if title is not None:
                    args["title"] = title
                if body is not None:
                    args["body"] = body
                if assignee_ids is not None:
                    args["assignee_ids"] = assignee_ids

                result = await update_prd_handler(args)

                if result.isError:
                    return f'{{"success": false, "error": "{result.content[0].text}"}}'

                return f'{{"success": true, "result": "{result.content[0].text}"}}'

            except Exception as e:
                logger.error(f"Error in update_prd tool: {e}", exc_info=True)
                return f'{{"success": false, "error": "Internal error: {str(e)}"}}'

        # Add PRD to project tool
        @self.mcp.tool()
        async def add_prd_to_project(
            project_id: str,
            title: str,
            description: str = "",
            acceptance_criteria: str = "",
            technical_requirements: str = "",
            business_value: str = "",
            status: str = "Backlog",
            priority: str = "Medium",
        ) -> str:
            """Add a new Product Requirements Document (PRD) to a GitHub project as a draft issue with comprehensive metadata including acceptance criteria, technical requirements, and business value."""
            logger.info(
                f"Add PRD to project called: project_id={project_id}, title={title}, status={status}, priority={priority}"
            )

            try:
                await self._ensure_async_initialized()

                if not self.github_client:
                    return '{"success": false, "error": "GitHub client not initialized - check token configuration"}'

                # Call the existing add PRD to project handler
                args = {
                    "project_id": project_id,
                    "title": title,
                    "description": description,
                    "status": status,
                    "priority": priority,
                }

                # Add optional fields if provided
                if acceptance_criteria:
                    args["acceptance_criteria"] = acceptance_criteria
                if technical_requirements:
                    args["technical_requirements"] = technical_requirements
                if business_value:
                    args["business_value"] = business_value

                result = await add_prd_to_project_handler(args)
                logger.info(f"Add PRD to project result: {result}")

                # Extract text content from CallToolResult
                if hasattr(result, "content") and result.content:
                    return result.content[0].text
                else:
                    return str(result)

            except Exception as e:
                logger.error(f"Error in add_prd_to_project: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return f'{{"success": false, "error": "Failed to add PRD to project: {str(e)}"}}'

        # Delete PRD from project tool
        @self.mcp.tool()
        async def delete_prd_from_project(
            project_id: str, project_item_id: str, confirm: bool
        ) -> str:
            """Delete a Product Requirements Document (PRD) from a GitHub project. This action is permanent and cannot be undone."""
            logger.info(
                f"Delete PRD from project called: project_id={project_id}, project_item_id={project_item_id}, confirm={confirm}"
            )

            try:
                await self._ensure_async_initialized()

                if not self.github_client:
                    return '{"success": false, "error": "GitHub client not initialized - check token configuration"}'

                # Call the existing delete PRD from project handler
                args = {
                    "project_id": project_id,
                    "project_item_id": project_item_id,
                    "confirm": confirm,
                }

                result = await delete_prd_from_project_handler(args)
                logger.info(f"Delete PRD from project result: {result}")

                # Extract text content from CallToolResult
                if hasattr(result, "content") and result.content:
                    return result.content[0].text
                else:
                    return str(result)

            except Exception as e:
                logger.error(f"Error in delete_prd_from_project: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return f'{{"success": false, "error": "Failed to delete PRD from project: {str(e)}"}}'

        # Update PRD status tool
        @self.mcp.tool()
        async def update_prd_status(
            prd_item_id: str,
            status: str = None,
            priority: str = None,
        ) -> str:
            """Update the status and/or priority fields of a Product Requirements Document (PRD) in a GitHub project using the Projects v2 field value update API."""
            logger.info(
                f"Update PRD status called: prd_item_id={prd_item_id}, status={status}, priority={priority}"
            )

            try:
                await self._ensure_async_initialized()

                if not self.github_client:
                    return '{"success": false, "error": "GitHub client not initialized - check token configuration"}'

                # Call the existing update PRD status handler
                args = {
                    "prd_item_id": prd_item_id,
                }
                if status is not None:
                    args["status"] = status
                if priority is not None:
                    args["priority"] = priority

                result = await update_prd_status_handler(args)
                logger.info(f"Update PRD status result: {result}")

                # Extract text content from CallToolResult
                if hasattr(result, "content") and result.content:
                    return result.content[0].text
                else:
                    return str(result)

            except Exception as e:
                logger.error(f"Error in update_prd_status: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return f'{{"success": false, "error": "Failed to update PRD status: {str(e)}"}}'

        # Update task tool
        @self.mcp.tool()
        async def update_task(
            task_item_id: str,
            title: str = None,
            description: str = None,
            status: str = None,
            priority: str = None,
            estimated_hours: int = None,
            actual_hours: int = None,
        ) -> str:
            """Update a Task's content (title, description) and/or project field values (status, priority, estimated_hours, actual_hours)."""
            logger.info(
                f"Update task called: task_item_id={task_item_id}, title={title}, description={description}, status={status}, priority={priority}, estimated_hours={estimated_hours}, actual_hours={actual_hours}"
            )

            try:
                await self._ensure_async_initialized()

                if not self.github_client:
                    return '{"success": false, "error": "GitHub client not initialized - check token configuration"}'

                # Call the existing update task handler
                args = {
                    "task_item_id": task_item_id,
                }
                if title is not None:
                    args["title"] = title
                if description is not None:
                    args["description"] = description
                if status is not None:
                    args["status"] = status
                if priority is not None:
                    args["priority"] = priority
                if estimated_hours is not None:
                    args["estimated_hours"] = estimated_hours
                if actual_hours is not None:
                    args["actual_hours"] = actual_hours

                result = await update_task_handler(args)
                logger.info(f"Update task result: {result}")

                # Extract text content from CallToolResult
                if hasattr(result, "content") and result.content:
                    return result.content[0].text
                else:
                    return str(result)

            except Exception as e:
                logger.error(f"Error in update_task: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return (
                    f'{{"success": false, "error": "Failed to update task: {str(e)}"}}'
                )

        # Create task tool
        @self.mcp.tool()
        async def create_task(
            project_id: str,
            parent_prd_id: str,
            title: str,
            description: str = "",
            priority: str = "Medium",
            estimated_hours: int = None,
        ) -> str:
            """Create a new task and associate it with a parent PRD in a GitHub project. Tasks represent specific work items that need to be completed as part of a larger Product Requirements Document (PRD)."""
            logger.info(
                f"Create task called: project_id={project_id}, parent_prd_id={parent_prd_id}, title={title}, description={description}, priority={priority}, estimated_hours={estimated_hours}"
            )

            try:
                await self._ensure_async_initialized()

                if not self.github_client:
                    return '{"success": false, "error": "GitHub client not initialized - check token configuration"}'

                # Call the existing create task handler
                args = {
                    "project_id": project_id,
                    "parent_prd_id": parent_prd_id,
                    "title": title,
                    "description": description,
                    "priority": priority,
                }
                if estimated_hours is not None:
                    args["estimated_hours"] = estimated_hours

                result = await create_task_handler(args)
                logger.info(f"Create task result: {result}")

                # Extract text content from CallToolResult
                if hasattr(result, "content") and result.content:
                    return result.content[0].text
                else:
                    return str(result)

            except Exception as e:
                logger.error(f"Error in create_task: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return (
                    f'{{"success": false, "error": "Failed to create task: {str(e)}"}}'
                )

        # List tasks tool
        @self.mcp.tool()
        async def list_tasks(
            project_id: str,
            parent_prd_id: str = None,
            first: int = 25,
            after: str = None,
        ) -> str:
            """List tasks in a GitHub project with optional filtering by parent PRD. Supports pagination and returns detailed information about each task including status, priority, parent PRD, and metadata."""
            logger.info(
                f"List tasks called: project_id={project_id}, parent_prd_id={parent_prd_id}, first={first}, after={after}"
            )

            try:
                await self._ensure_async_initialized()

                if not self.github_client:
                    return '{"success": false, "error": "GitHub client not initialized - check token configuration"}'

                # Call the existing list tasks handler
                args = {
                    "project_id": project_id,
                    "first": first,
                }
                if parent_prd_id is not None:
                    args["parent_prd_id"] = parent_prd_id
                if after is not None:
                    args["after"] = after

                result = await list_tasks_handler(args)
                logger.info(f"List tasks result: {result}")

                # Extract text content from CallToolResult
                if hasattr(result, "content") and result.content:
                    return result.content[0].text
                else:
                    return str(result)

            except Exception as e:
                logger.error(f"Error in list_tasks: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return (
                    f'{{"success": false, "error": "Failed to list tasks: {str(e)}"}}'
                )

        # Delete task tool
        @self.mcp.tool()
        async def delete_task(project_id: str, task_item_id: str, confirm: bool) -> str:
            """Delete a task from a GitHub project. This action is permanent and cannot be undone."""
            logger.info(
                f"Delete task called: project_id={project_id}, task_item_id={task_item_id}, confirm={confirm}"
            )

            try:
                await self._ensure_async_initialized()

                if not self.github_client:
                    return '{"success": false, "error": "GitHub client not initialized - check token configuration"}'

                # Call the existing delete task handler
                args = {
                    "project_id": project_id,
                    "task_item_id": task_item_id,
                    "confirm": confirm,
                }

                result = await delete_task_handler(args)
                logger.info(f"Delete task result: {result}")

                # Extract text content from CallToolResult
                if hasattr(result, "content") and result.content:
                    return result.content[0].text
                else:
                    return str(result)

            except Exception as e:
                logger.error(f"Error in delete_task: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return (
                    f'{{"success": false, "error": "Failed to delete task: {str(e)}"}}'
                )

        # Add subtask tool
        @self.mcp.tool()
        async def add_subtask(
            project_id: str,
            parent_task_id: str,
            title: str,
            description: str = "",
            order: int = 1,
        ) -> str:
            """Create a new subtask and associate it with a parent Task in a GitHub project. Subtasks represent specific work items within a larger Task."""
            logger.info(
                f"Add subtask called: project_id={project_id}, parent_task_id={parent_task_id}, title={title}, description={description}, order={order}"
            )

            try:
                await self._ensure_async_initialized()

                if not self.github_client:
                    return '{"success": false, "error": "GitHub client not initialized - check token configuration"}'

                # Call the existing add subtask handler
                args = {
                    "project_id": project_id,
                    "parent_task_id": parent_task_id,
                    "title": title,
                    "description": description,
                    "order": order,
                }

                result = await add_subtask_handler(args)
                logger.info(f"Add subtask result: {result}")

                # Extract text content from CallToolResult
                if hasattr(result, "content") and result.content:
                    return result.content[0].text
                else:
                    return str(result)

            except Exception as e:
                logger.error(f"Error in add_subtask: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return (
                    f'{{"success": false, "error": "Failed to add subtask: {str(e)}"}}'
                )

        @self.mcp.tool()
        async def list_subtasks(
            project_id: str,
            parent_task_id: str = None,
            first: int = 25,
            after: str = None,
        ) -> str:
            """List subtasks in a GitHub project with optional filtering by parent task. Supports pagination and returns detailed information about each subtask including status, parent task, and metadata."""
            logger.info(
                f"List subtasks called: project_id={project_id}, parent_task_id={parent_task_id}, first={first}, after={after}"
            )

            try:
                await self._ensure_async_initialized()

                if not self.github_client:
                    return '{"success": false, "error": "GitHub client not initialized - check token configuration"}'

                # Call the existing list subtasks handler
                args = {
                    "project_id": project_id,
                    "parent_task_id": parent_task_id,
                    "first": first,
                    "after": after,
                }

                result = await list_subtasks_handler(args)
                logger.info(f"List subtasks result: {result}")

                # Extract text content from CallToolResult
                if hasattr(result, "content") and result.content:
                    return result.content[0].text
                else:
                    return str(result)

            except Exception as e:
                logger.error(f"Error in list_subtasks: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return f'{{"success": false, "error": "Failed to list subtasks: {str(e)}"}}'

        # Log the total number of tools registered
        logger.info(
            f"Successfully registered {len(self.mcp.tools)} MCP tools with FastMCP"
        )


def main():
    """Main entry point for the FastMCP server."""
    parser = argparse.ArgumentParser(
        description="GitHub Project Manager MCP FastMCP Server"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--config", type=str, help="Path to configuration file")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Debug logging enabled")

    try:
        logger.info("Starting GitHub Project Manager FastMCP Server...")

        # Create and initialize the server
        server = GitHubProjectManagerMCPFastServer(config_path=args.config)
        logger.info("GitHub Project Manager MCP FastMCP Server initialized and ready")

        # Run the FastMCP server
        server.mcp.run()

    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()

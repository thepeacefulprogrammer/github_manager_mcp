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
    )

    logger.info("Successfully imported project handlers")
except ImportError as e:
    logger.error(f"Failed to import project handlers: {e}")
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
                logger.info("GitHub client initialized successfully")
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

        logger.info(
            f"Registered {len([test_connection, create_project, list_projects, delete_project, get_project_details])} MCP tools"
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

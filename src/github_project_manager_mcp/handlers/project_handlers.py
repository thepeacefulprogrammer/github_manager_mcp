"""
MCP tool handlers for project management operations.

This module implements MCP tool handlers for GitHub Projects v2 management,
including creating, listing, updating, and managing projects.
"""

import logging
import re
from typing import Any, Dict, Optional

from mcp.server.models import InitializationOptions
from mcp.types import CallToolResult, TextContent, Tool

from ..github_client import GitHubClient
from ..models.project import Project
from ..utils.query_builder import ProjectQueryBuilder
from ..utils.validation import ProjectValidator, ValidationError

logger = logging.getLogger(__name__)


# GitHub Client instance (will be initialized by the MCP server)
github_client: Optional[GitHubClient] = None
query_builder = ProjectQueryBuilder()
project_validator = ProjectValidator()


def initialize_github_client(token: str) -> None:
    """
    Initialize the GitHub client with authentication token.

    Args:
        token: GitHub Personal Access Token
    """
    global github_client
    github_client = GitHubClient(token=token, rate_limit_enabled=True)
    logger.info("GitHub client initialized for project handlers")


def validate_repository_format(repository: str) -> bool:
    """
    Validate repository format as 'owner/repo'.

    Args:
        repository: Repository string to validate

    Returns:
        True if format is valid, False otherwise
    """
    if not repository or not isinstance(repository, str):
        return False

    parts = repository.split("/")
    if len(parts) != 2:
        return False

    owner, repo = parts
    if not owner or not repo:
        return False

    return True


async def get_owner_id_from_repository(repository: str) -> str:
    """
    Get the GitHub node ID of the repository owner.

    Args:
        repository: Repository in format "owner/repo"

    Returns:
        GitHub node ID of the owner

    Raises:
        ValueError: If repository format is invalid or owner not found
    """
    # Validate repository format
    if not validate_repository_format(repository):
        raise ValueError(
            f"Invalid repository format: {repository}. Expected 'owner/repo'"
        )

    owner, repo_name = repository.split("/", 1)

    # GraphQL query to get owner ID
    query = f"""
    query {{
      repository(owner: "{owner}", name: "{repo_name}") {{
        owner {{
          id
          login
        }}
      }}
    }}
    """

    if not github_client:
        raise ValueError("GitHub client not initialized")

    try:
        result = await github_client.query(query)
        owner_data = result.get("repository", {}).get("owner", {})

        if not owner_data:
            raise ValueError(
                f"Repository not found or owner not accessible: {repository}"
            )

        owner_id = owner_data.get("id")
        if not owner_id:
            raise ValueError(f"Could not get owner ID for repository: {repository}")

        logger.debug(f"Found owner ID {owner_id} for repository {repository}")
        return owner_id

    except Exception as e:
        logger.error(f"Error getting owner ID for repository {repository}: {e}")
        raise ValueError(
            f"Failed to get owner information for repository {repository}: {str(e)}"
        )


# Tool definition for create_project
CREATE_PROJECT_TOOL = Tool(
    name="create_project",
    description="Create a new GitHub Projects v2 project for the specified repository",
    inputSchema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Name of the project"},
            "description": {
                "type": "string",
                "description": "Description of the project",
            },
            "repository": {
                "type": "string",
                "description": "Repository in format 'owner/repo' (e.g., 'octocat/Hello-World')",
            },
            "visibility": {
                "type": "string",
                "enum": ["PUBLIC", "PRIVATE"],
                "description": "Project visibility (optional, defaults to PRIVATE)",
            },
        },
        "required": ["name", "description", "repository"],
    },
)


# Tool definition for list_projects
LIST_PROJECTS_TOOL = Tool(
    name="list_projects",
    description="List GitHub Projects v2 projects for a user or organization with filtering and pagination support",
    inputSchema={
        "type": "object",
        "properties": {
            "owner": {
                "type": "string",
                "description": "Username or organization name to list projects for",
            },
            "first": {
                "type": "integer",
                "description": "Number of projects to fetch (pagination, max 100)",
                "minimum": 1,
                "maximum": 100,
            },
            "after": {
                "type": "string",
                "description": "Cursor for pagination to fetch projects after this point",
            },
        },
        "required": ["owner"],
    },
)


async def create_project_handler(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle create_project MCP tool calls.

    Args:
        arguments: Tool arguments containing name, description, repository, and optional visibility

    Returns:
        CallToolResult with success/error information
    """
    try:
        # Extract parameters
        name = arguments.get("name")
        description = arguments.get("description")
        repository = arguments.get("repository")
        visibility = arguments.get("visibility", "PRIVATE")

        # Comprehensive validation using ProjectValidator
        project_data = {
            "name": name,
            "description": description,
            "repository": repository,
            "visibility": visibility,
        }

        validation_result = project_validator.validate_project_creation(project_data)

        if not validation_result.is_valid:
            error_message = f"Validation failed: {', '.join(validation_result.errors)}"
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {error_message}")],
                isError=True,
            )

        # Log warnings if any
        if validation_result.warnings:
            logger.warning(
                f"Project creation warnings: {', '.join(validation_result.warnings)}"
            )

        if not github_client:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text="Error: GitHub client not initialized"
                    )
                ],
                isError=True,
            )

        logger.info(f"Creating project '{name}' for repository '{repository}'")

        # Get owner ID from repository (repository format already validated)
        try:
            owner_id = await get_owner_id_from_repository(repository)
        except ValueError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                isError=True,
            )

        # Build the GraphQL mutation
        mutation = query_builder.create_project(
            owner_id=owner_id, title=name, description=description
        )

        # Execute the mutation
        try:
            result = await github_client.mutate(mutation)
            project_data = result.get("createProjectV2", {}).get("projectV2", {})

            if not project_data:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text="Error: Failed to create project - no data returned",
                        )
                    ],
                    isError=True,
                )

            # Create a Project model instance for validation and response formatting
            project = Project.from_graphql(project_data)

            # Success response
            response_text = f"""✅ Successfully created project!

**Project Details:**
- **Name:** {project.title}
- **ID:** {project.id}
- **URL:** {project.url}
- **Description:** {project.description or 'No description'}
- **Created:** {project.created_at}
- **Repository:** {repository}

The project is now ready for use in GitHub Projects v2."""

            return CallToolResult(
                content=[TextContent(type="text", text=response_text)], isError=False
            )

        except Exception as e:
            logger.error(f"GitHub API error creating project: {e}")
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"Error creating project: {str(e)}")
                ],
                isError=True,
            )

    except Exception as e:
        logger.error(f"Unexpected error in create_project_handler: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Unexpected error: {str(e)}")],
            isError=True,
        )


async def list_projects_handler(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle list_projects MCP tool calls.

    Args:
        arguments: Tool arguments containing owner and optional pagination parameters

    Returns:
        CallToolResult with project list or error information
    """
    try:
        # Validate required arguments
        owner = arguments.get("owner")
        first = arguments.get("first")
        after = arguments.get("after")

        if not owner:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text="Error: 'owner' parameter is required"
                    )
                ],
                isError=True,
            )

        if not github_client:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text="Error: GitHub client not initialized"
                    )
                ],
                isError=True,
            )

        logger.info(
            f"Listing projects for owner '{owner}' with pagination: first={first}, after={after}"
        )

        # Build the GraphQL query
        query = query_builder.list_projects(owner=owner, first=first, after=after)

        # Execute the query
        try:
            result = await github_client.query(query)
            user_data = result.get("user")

            if not user_data:
                return CallToolResult(
                    content=[
                        TextContent(type="text", text=f"Error: User not found: {owner}")
                    ],
                    isError=True,
                )

            projects_data = user_data.get("projectsV2", {})
            total_count = projects_data.get("totalCount", 0)
            project_nodes = projects_data.get("nodes", [])
            page_info = projects_data.get("pageInfo", {})

            # Handle empty results
            if total_count == 0:
                response_text = f"No projects found for {owner}"
                return CallToolResult(
                    content=[TextContent(type="text", text=response_text)],
                    isError=False,
                )

            # Format the response
            response_lines = [
                f"# Projects for {owner}",
                f"Total: {total_count} projects",
                f"Showing {len(project_nodes)} projects",
                "",
            ]

            # Add pagination info if available
            if page_info:
                has_next = page_info.get("hasNextPage", False)
                next_cursor = page_info.get("endCursor")
                response_lines.extend(
                    [
                        f"Has next page: {has_next}",
                        f"Next cursor: {next_cursor}" if next_cursor else "",
                        "",
                    ]
                )

            # Add project details
            for i, project_node in enumerate(project_nodes, 1):
                # Convert to Project model for consistent formatting
                project = Project.from_graphql(project_node)

                # Extract viewer_can_update directly from the raw data if available
                viewer_can_update = project_node.get("viewerCanUpdate", "Unknown")

                response_lines.extend(
                    [
                        f"## {i}. {project.title}",
                        f"**ID:** {project.id}",
                        f"**URL:** {project.url}",
                        f"**Description:** {project.description or 'No description'}",
                        f"**Created:** {project.created_at}",
                        f"**Updated:** {project.updated_at}",
                        f"**Number:** #{project.number}",
                        f"**Can Update:** {viewer_can_update}",
                        "",
                    ]
                )

            response_text = "\n".join(response_lines)

            return CallToolResult(
                content=[TextContent(type="text", text=response_text)], isError=False
            )

        except Exception as e:
            logger.error(f"GitHub API error listing projects: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"API Error: {str(e)}")],
                isError=True,
            )

    except Exception as e:
        logger.error(f"Unexpected error in list_projects_handler: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Unexpected error: {str(e)}")],
            isError=True,
        )


# Delete project tool definition
DELETE_PROJECT_TOOL = Tool(
    name="delete_project",
    description="Delete a GitHub Project v2 by ID. This action is permanent and cannot be undone.",
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "ID of the project to delete (e.g., 'PVT_kwDOBQfyVc0FoQ')",
            },
            "confirm": {
                "type": "boolean",
                "description": "Must be true to confirm deletion. Required safety check.",
            },
        },
        "required": ["project_id", "confirm"],
    },
)


async def delete_project_handler(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle delete_project MCP tool calls.

    Args:
        arguments: Tool arguments containing project_id and confirmation

    Returns:
        CallToolResult with deletion status or error information
    """
    try:
        # Validate required arguments
        project_id = arguments.get("project_id")
        confirm = arguments.get("confirm")

        if not project_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text="Error: 'project_id' parameter is required"
                    )
                ],
                isError=True,
            )

        if confirm is None:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: Must explicitly confirm deletion by setting 'confirm' to true",
                    )
                ],
                isError=True,
            )

        if not confirm:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: Deletion cancelled. Set 'confirm' to true to proceed.",
                    )
                ],
                isError=True,
            )

        if not github_client:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text="Error: GitHub client not initialized"
                    )
                ],
                isError=True,
            )

        logger.info(f"Deleting project with ID: {project_id}")

        # Build the GraphQL mutation
        mutation = query_builder.delete_project(project_id=project_id)

        # Execute the mutation
        try:
            result = await github_client.mutate(mutation)
            project_data = result.get("deleteProjectV2", {}).get("projectV2", {})

            if not project_data:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text="Error: Failed to delete project - no data returned",
                        )
                    ],
                    isError=True,
                )

            # Extract project information from the response
            project_id_returned = project_data.get("id", project_id)
            project_title = project_data.get("title", "Unknown")
            owner_login = project_data.get("owner", {}).get("login", "Unknown")

            # Success response
            response_text = f"""✅ Successfully deleted project!

**Deleted Project:**
- **Name:** {project_title}
- **ID:** {project_id_returned}
- **Owner:** {owner_login}

The project has been permanently deleted and cannot be recovered."""

            return CallToolResult(
                content=[TextContent(type="text", text=response_text)], isError=False
            )

        except Exception as e:
            logger.error(f"GitHub API error deleting project: {e}")
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"Error deleting project: {str(e)}")
                ],
                isError=True,
            )

    except Exception as e:
        logger.error(f"Unexpected error in delete_project_handler: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Unexpected error: {str(e)}")],
            isError=True,
        )


# Get project details tool definition
GET_PROJECT_DETAILS_TOOL = Tool(
    name="get_project_details",
    description="Retrieve detailed information about a GitHub Project v2 by ID.",
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "ID of the project to retrieve details for (e.g., 'PVT_kwDOBQfyVc0FoQ')",
            },
        },
        "required": ["project_id"],
    },
)


async def get_project_details_handler(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle get_project_details MCP tool calls.

    Args:
        arguments: Tool arguments containing project_id

    Returns:
        CallToolResult with project details or error information
    """
    try:
        # Validate required arguments
        project_id = arguments.get("project_id")

        if not project_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text="Error: 'project_id' parameter is required"
                    )
                ],
                isError=True,
            )

        if not github_client:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text="Error: GitHub client not initialized"
                    )
                ],
                isError=True,
            )

        logger.info(f"Getting project details for ID: {project_id}")

        # Build the GraphQL query
        query = query_builder.get_project(project_id=project_id)

        # Execute the query
        try:
            result = await github_client.query(query)
            project_data = result.get("node")

            if not project_data:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Error: Project not found with ID: {project_id}",
                        )
                    ],
                    isError=True,
                )

            # Create a Project model instance for validation and response formatting
            project = Project.from_graphql(project_data)

            # Success response with detailed project information
            response_text = f"""# Project Details

**Basic Information:**
- **Name:** {project.title}
- **ID:** {project.id}
- **Number:** #{project.number}
- **URL:** {project.url}

**Description:**
{project.description or project.short_description or 'No description provided'}

**Metadata:**
- **Owner:** {project_data.get('owner', {}).get('login', 'Unknown')}
- **Created:** {project.created_at}
- **Updated:** {project.updated_at}
- **Can Update:** {project_data.get('viewerCanUpdate', 'Unknown')}

**Status:**
- **State:** Active
- **Visibility:** {project_data.get('visibility', 'Unknown')}

This project is ready for use and can be managed through GitHub Projects v2."""

            return CallToolResult(
                content=[TextContent(type="text", text=response_text)], isError=False
            )

        except Exception as e:
            logger.error(f"GitHub API error retrieving project details: {e}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error retrieving project details: {str(e)}",
                    )
                ],
                isError=True,
            )

    except Exception as e:
        logger.error(f"Unexpected error in get_project_details_handler: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Unexpected error: {str(e)}")],
            isError=True,
        )


# Update project tool definition
UPDATE_PROJECT_TOOL = Tool(
    name="update_project",
    description="Update a GitHub Projects v2 project metadata including name, description, visibility, and README",
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "ID of the project to update (e.g., 'PVT_kwDOBQfyVc0FoQ')",
            },
            "title": {
                "type": "string",
                "description": "New project title (optional)",
            },
            "short_description": {
                "type": "string",
                "description": "New project short description (optional)",
            },
            "readme": {
                "type": "string",
                "description": "New project README content in Markdown format (optional)",
            },
            "public": {
                "type": "boolean",
                "description": "Whether the project should be public (true) or private (false) (optional)",
            },
        },
        "required": ["project_id"],
    },
)


async def update_project_handler(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle update_project MCP tool calls.

    Args:
        arguments: Tool arguments containing project_id and optional update fields

    Returns:
        CallToolResult with success/error information
    """
    try:
        # Extract parameters
        project_id = arguments.get("project_id")
        title = arguments.get("title")
        short_description = arguments.get("short_description")
        readme = arguments.get("readme")
        public = arguments.get("public")

        # Basic project_id validation
        if not project_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text="Error: 'project_id' parameter is required"
                    )
                ],
                isError=True,
            )

        # Comprehensive validation using ProjectValidator
        update_data = {
            "title": title,
            "short_description": short_description,
            "readme": readme,
            "public": public,
        }

        validation_result = project_validator.validate_project_update(update_data)

        if not validation_result.is_valid:
            error_message = f"Validation failed: {', '.join(validation_result.errors)}"
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {error_message}")],
                isError=True,
            )

        # Log warnings if any
        if validation_result.warnings:
            logger.warning(
                f"Project update warnings: {', '.join(validation_result.warnings)}"
            )

        if not github_client:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text="Error: GitHub client not initialized"
                    )
                ],
                isError=True,
            )

        logger.info(f"Updating project with ID: {project_id}")

        # Build the GraphQL mutation
        mutation = query_builder.update_project(
            project_id=project_id,
            title=title,
            short_description=short_description,
            readme=readme,
            public=public,
        )

        # Execute the mutation
        try:
            result = await github_client.mutate(mutation)
            project_data = result.get("updateProjectV2", {}).get("projectV2", {})

            if not project_data:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text="Error: Failed to update project - no data returned",
                        )
                    ],
                    isError=True,
                )

            # Extract updated project information from the response
            updated_title = project_data.get("title", "Unknown")
            updated_short_description = project_data.get(
                "shortDescription", "No description"
            )
            updated_readme = project_data.get("readme", "No README")
            updated_public = project_data.get("public", False)
            updated_at = project_data.get("updatedAt", "Unknown")

            # Build response showing what was updated
            updates = []
            if title:
                updates.append(f"- **Title:** {updated_title}")
            if short_description:
                updates.append(f"- **Description:** {updated_short_description}")
            if readme:
                updates.append(
                    f"- **README:** Updated ({len(updated_readme)} characters)"
                )
            if public is not None:
                visibility = "Public" if updated_public else "Private"
                updates.append(f"- **Visibility:** {visibility}")

            updates_text = "\n".join(updates) if updates else "- No changes made"

            # Success response
            response_text = f"""✅ Successfully updated project!

**Project:** {updated_title}
**ID:** {project_id}

**Updated Fields:**
{updates_text}

**Last Updated:** {updated_at}

The project has been successfully updated with the new settings."""

            return CallToolResult(
                content=[TextContent(type="text", text=response_text)], isError=False
            )

        except Exception as e:
            logger.error(f"GitHub API error updating project: {e}")
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"Error updating project: {str(e)}")
                ],
                isError=True,
            )

    except Exception as e:
        logger.error(f"Unexpected error in update_project_handler: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Unexpected error: {str(e)}")],
            isError=True,
        )


# All available project management tools
PROJECT_TOOLS = [
    CREATE_PROJECT_TOOL,
    LIST_PROJECTS_TOOL,
    UPDATE_PROJECT_TOOL,
    DELETE_PROJECT_TOOL,
    GET_PROJECT_DETAILS_TOOL,
]

# Tool handlers mapping
PROJECT_TOOL_HANDLERS = {
    "create_project": create_project_handler,
    "list_projects": list_projects_handler,
    "update_project": update_project_handler,
    "delete_project": delete_project_handler,
    "get_project_details": get_project_details_handler,
}

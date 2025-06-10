"""
MCP handlers for project search and filtering functionality.

Provides MCP tool handlers for searching GitHub Projects v2 with
advanced filtering capabilities including text search, visibility
filters, date ranges, and result sorting.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from mcp.types import CallToolResult, TextContent, Tool

from ..github_client import GitHubClient
from ..utils.project_search import (
    ProjectSearchFilter,
    ProjectSearchManager,
    ProjectSearchQueryBuilder,
)

logger = logging.getLogger(__name__)

# GitHub Client instance (will be initialized by the MCP server)
github_client: Optional[GitHubClient] = None

# Global search manager instance
search_manager: Optional[ProjectSearchManager] = None

# Track the client used to create the search manager for consistency
_search_manager_client_id: Optional[id] = None


def initialize_github_client(token: str) -> None:
    """
    Initialize the GitHub client with authentication token.

    Args:
        token: GitHub Personal Access Token
    """
    global github_client, search_manager, _search_manager_client_id
    github_client = GitHubClient(token=token, rate_limit_enabled=True)

    # Reset search manager when client changes to ensure consistency
    search_manager = None
    _search_manager_client_id = None

    logger.info("GitHub client initialized for project search handlers")


def _ensure_search_manager_initialized() -> None:
    """
    Ensure search manager is initialized with the current GitHub client.

    This function handles:
    - Lazy initialization of search manager
    - Recreation when GitHub client changes
    - Thread-safe access patterns
    """
    global search_manager, _search_manager_client_id

    if not github_client:
        raise ValueError("GitHub client not initialized")

    current_client_id = id(github_client)

    # Check if we need to create or recreate the search manager
    if search_manager is None or _search_manager_client_id != current_client_id:
        try:
            search_manager = ProjectSearchManager(github_client)
            _search_manager_client_id = current_client_id
            logger.info(
                f"Search manager initialized with client ID: {current_client_id}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize search manager: {str(e)}")
            raise RuntimeError(f"Error initializing search functionality: {str(e)}")


def _classify_and_format_error(error: Exception) -> str:
    """
    Classify the error and return a user-friendly error message.

    Args:
        error: The exception that occurred

    Returns:
        User-friendly error message string
    """
    error_msg = str(error).lower()

    # Search manager initialization errors (check first before other patterns)
    if any(
        keyword in error_msg
        for keyword in [
            "error initializing search functionality",
            "search manager",
            "initializing search",
        ]
    ):
        return (
            "Error initializing search functionality. "
            "Please check your GitHub token and try again."
        )

    # Authentication/Token errors
    elif any(
        keyword in error_msg
        for keyword in [
            "bad credentials",
            "unauthorized",
            "invalid token",
            "expired token",
        ]
    ):
        return (
            "Authentication failed: Invalid or expired GitHub token. "
            "Please check your GitHub token and make sure your token has the required permissions (project:read, read:org)."
        )

    # Rate limit errors
    elif any(keyword in error_msg for keyword in ["rate limit", "api rate limit"]):
        return (
            "GitHub API rate limit exceeded. Please wait a few minutes and try again. "
            "Consider using a personal access token for higher limits."
        )

    # Permission errors
    elif any(
        keyword in error_msg
        for keyword in [
            "resource not accessible",
            "permission denied",
            "insufficient privileges",
        ]
    ):
        return (
            "Permission denied: Your GitHub token does not have required permissions. "
            "Make sure your token includes 'project:read' and 'read:org' scopes."
        )

    # Client reinitialization errors (check before network errors)
    elif any(
        keyword in error_msg for keyword in ["client changed", "operation interrupted"]
    ):
        return (
            "Search operation was interrupted due to configuration changes. "
            "Please try again."
        )

    # Network/Connection errors
    elif any(
        keyword in error_msg
        for keyword in ["connection", "timeout", "network", "unreachable"]
    ):
        return (
            "Network connection error: Unable to connect to GitHub API. "
            "Check your internet connection and try again."
        )

    # Generic unexpected errors
    else:
        return (
            "An unexpected error occurred while searching projects. "
            "Please try again. If the problem persists, check your GitHub token and network connection."
        )


async def search_projects_handler(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle search_projects tool calls.

    Search for GitHub Projects v2 using various filter criteria including
    text search, visibility, dates, and ownership filters.

    Args:
        arguments: Tool arguments containing search parameters

    Returns:
        CallToolResult with search results or error message
    """
    try:
        # Check GitHub client
        if not github_client:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: GitHub client not initialized. Please check your GitHub token.",
                    )
                ],
                isError=True,
            )

        # Ensure search manager is properly initialized
        try:
            _ensure_search_manager_initialized()
        except Exception as e:
            error_message = _classify_and_format_error(e)
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=error_message,
                    )
                ],
                isError=True,
            )

        # Extract search parameters
        query = arguments.get("query", "")
        visibility = arguments.get("visibility")
        owner = arguments.get("owner")
        created_after = arguments.get("created_after")
        created_before = arguments.get("created_before")
        updated_after = arguments.get("updated_after")
        updated_before = arguments.get("updated_before")
        limit = arguments.get("limit", 25)
        sort_by = arguments.get("sort_by", "updated")
        sort_order = arguments.get("sort_order", "desc")

        # Validate limit
        try:
            limit = int(limit)
            if not (1 <= limit <= 100):
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text", text="Error: 'limit' must be between 1 and 100"
                        )
                    ],
                    isError=True,
                )
        except (ValueError, TypeError):
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text="Error: 'limit' must be a valid integer"
                    )
                ],
                isError=True,
            )

        # Parse date parameters
        def parse_date(date_str: str, param_name: str) -> Optional[datetime]:
            if not date_str:
                return None
            try:
                # Support ISO format with or without timezone
                if date_str.endswith("Z"):
                    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                elif "+" in date_str or date_str.endswith("T"):
                    return datetime.fromisoformat(date_str)
                else:
                    # Assume date only, add time and UTC timezone
                    return datetime.fromisoformat(f"{date_str}T00:00:00+00:00")
            except ValueError:
                raise ValueError(
                    f"Invalid date format for '{param_name}'. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)"
                )

        try:
            created_after_dt = (
                parse_date(created_after, "created_after") if created_after else None
            )
            created_before_dt = (
                parse_date(created_before, "created_before") if created_before else None
            )
            updated_after_dt = (
                parse_date(updated_after, "updated_after") if updated_after else None
            )
            updated_before_dt = (
                parse_date(updated_before, "updated_before") if updated_before else None
            )
        except ValueError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                isError=True,
            )

        # Create search filter
        try:
            search_filter = ProjectSearchFilter(
                query=query,
                visibility=visibility,
                owner=owner,
                created_after=created_after_dt,
                created_before=created_before_dt,
                updated_after=updated_after_dt,
                updated_before=updated_before_dt,
                limit=limit,
                sort_by=sort_by,
                sort_order=sort_order,
            )
        except ValueError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                isError=True,
            )

        # Perform search
        try:
            result = await search_manager.search_projects(search_filter)

            # Format response
            if not result.projects:
                response_text = "🔍 **No projects found**\n\n"
                if query:
                    response_text += f"No projects matching '{query}' were found"
                else:
                    response_text += "No projects found with the specified criteria"
                if result.search_time_ms < 1000:
                    response_text += f" (searched in {result.search_time_ms:.1f}ms)"
                else:
                    response_text += f" (searched in {result.search_time_ms/1000:.1f}s)"
            else:
                response_text = f"🔍 **Found {result.total_count} project(s)**"
                if result.search_time_ms < 1000:
                    response_text += f" (searched in {result.search_time_ms:.1f}ms)\n\n"
                else:
                    response_text += (
                        f" (searched in {result.search_time_ms/1000:.1f}s)\n\n"
                    )

                for i, project in enumerate(result.projects, 1):
                    response_text += f"**{i}. {project['title']}**\n"
                    response_text += f"   • ID: `{project['id']}`\n"
                    if project.get("shortDescription"):
                        response_text += (
                            f"   • Description: {project['shortDescription']}\n"
                        )
                    response_text += f"   • Visibility: {'Public' if project.get('public') else 'Private'}\n"
                    if project.get("owner"):
                        response_text += f"   • Owner: {project['owner']}\n"
                    if project.get("createdAt"):
                        created_date = project["createdAt"][:10]  # Extract date part
                        response_text += f"   • Created: {created_date}\n"
                    if project.get("updatedAt"):
                        updated_date = project["updatedAt"][:10]  # Extract date part
                        response_text += f"   • Updated: {updated_date}\n"
                    response_text += "\n"

                if result.has_next_page:
                    response_text += f"📄 *Showing first {len(result.projects)} of {result.total_count} results*\n"
                    response_text += "*Use pagination parameters to see more results*"

            return CallToolResult(
                content=[TextContent(type="text", text=response_text)],
                isError=False,
            )

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            error_message = _classify_and_format_error(e)
            return CallToolResult(
                content=[TextContent(type="text", text=error_message)],
                isError=True,
            )

    except Exception as e:
        logger.error(f"Unexpected error in search_projects_handler: {str(e)}")
        error_message = _classify_and_format_error(e)
        return CallToolResult(
            content=[TextContent(type="text", text=error_message)],
            isError=True,
        )


async def search_projects_advanced_handler(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle search_projects_advanced tool calls.

    Advanced project search with query builder syntax for complex
    search criteria and boolean logic.

    Args:
        arguments: Tool arguments containing advanced search parameters

    Returns:
        CallToolResult with search results or error message
    """
    try:
        # Check GitHub client
        if not github_client:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: GitHub client not initialized. Please check your GitHub token.",
                    )
                ],
                isError=True,
            )

        # Ensure search manager is properly initialized
        try:
            _ensure_search_manager_initialized()
        except Exception as e:
            error_message = _classify_and_format_error(e)
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=error_message,
                    )
                ],
                isError=True,
            )

        # Extract search builder parameters
        builder_config = arguments.get("search_config", {})

        # Build search using fluent interface
        try:
            builder = ProjectSearchQueryBuilder()

            if "query" in builder_config:
                builder = builder.query(builder_config["query"])

            if builder_config.get("public"):
                builder = builder.public()
            elif builder_config.get("private"):
                builder = builder.private()

            if "owner" in builder_config:
                builder = builder.owner(builder_config["owner"])

            if "created_after" in builder_config:
                date_str = builder_config["created_after"]
                date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                builder = builder.created_after(date_obj)

            if "created_before" in builder_config:
                date_str = builder_config["created_before"]
                date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                builder = builder.created_before(date_obj)

            if "updated_after" in builder_config:
                date_str = builder_config["updated_after"]
                date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                builder = builder.updated_after(date_obj)

            if "updated_before" in builder_config:
                date_str = builder_config["updated_before"]
                date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                builder = builder.updated_before(date_obj)

            if "limit" in builder_config:
                builder = builder.limit(int(builder_config["limit"]))

            # Sort configuration
            sort_config = builder_config.get("sort", {})
            if sort_config.get("by") == "created":
                builder = builder.sort_by_created(sort_config.get("ascending", False))
            elif sort_config.get("by") == "name":
                builder = builder.sort_by_name(sort_config.get("ascending", True))
            else:
                builder = builder.sort_by_updated(sort_config.get("ascending", False))

            search_filter = builder.build()

        except Exception as e:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text=f"Error building search query: {str(e)}"
                    )
                ],
                isError=True,
            )

        # Perform search using the built filter
        try:
            result = await search_manager.search_projects(search_filter)

            # Format response (same as basic search)
            if not result.projects:
                response_text = "🔍 **No projects found**\n\n"
                response_text += (
                    "No projects found with the specified advanced criteria"
                )
                if result.search_time_ms < 1000:
                    response_text += f" (searched in {result.search_time_ms:.1f}ms)"
                else:
                    response_text += f" (searched in {result.search_time_ms/1000:.1f}s)"
            else:
                response_text = f"🔍 **Found {result.total_count} project(s)**"
                if result.search_time_ms < 1000:
                    response_text += f" (searched in {result.search_time_ms:.1f}ms)\n\n"
                else:
                    response_text += (
                        f" (searched in {result.search_time_ms/1000:.1f}s)\n\n"
                    )

                for i, project in enumerate(result.projects, 1):
                    response_text += f"**{i}. {project['title']}**\n"
                    response_text += f"   • ID: `{project['id']}`\n"
                    if project.get("shortDescription"):
                        response_text += (
                            f"   • Description: {project['shortDescription']}\n"
                        )
                    response_text += f"   • Visibility: {'Public' if project.get('public') else 'Private'}\n"
                    if project.get("owner"):
                        response_text += f"   • Owner: {project['owner']}\n"
                    if project.get("createdAt"):
                        created_date = project["createdAt"][:10]
                        response_text += f"   • Created: {created_date}\n"
                    if project.get("updatedAt"):
                        updated_date = project["updatedAt"][:10]
                        response_text += f"   • Updated: {updated_date}\n"
                    response_text += "\n"

                if result.has_next_page:
                    response_text += f"📄 *Showing first {len(result.projects)} of {result.total_count} results*\n"
                    response_text += "*Use pagination parameters to see more results*"

            return CallToolResult(
                content=[TextContent(type="text", text=response_text)],
                isError=False,
            )

        except Exception as e:
            logger.error(f"Advanced search failed: {str(e)}")
            error_message = _classify_and_format_error(e)
            return CallToolResult(
                content=[TextContent(type="text", text=error_message)],
                isError=True,
            )

    except Exception as e:
        logger.error(f"Unexpected error in search_projects_advanced_handler: {str(e)}")
        error_message = _classify_and_format_error(e)
        return CallToolResult(
            content=[TextContent(type="text", text=error_message)],
            isError=True,
        )


# Define the search project tools
SEARCH_PROJECT_TOOLS = [
    Tool(
        name="search_projects",
        description="""Search for GitHub Projects v2 using various filter criteria.

        Supports text search across project titles and descriptions, filtering by visibility,
        ownership, creation/update dates, and result sorting. Perfect for finding specific
        projects or browsing project collections with advanced filtering.

        Features:
        • Text search across project titles and descriptions
        • Filter by visibility (public/private)
        • Filter by owner username
        • Date range filtering (created/updated)
        • Configurable result limits and sorting
        • Fast search with performance metrics
        """,
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Text search query for project titles and descriptions",
                },
                "visibility": {
                    "type": "string",
                    "enum": ["public", "private"],
                    "description": "Filter by project visibility",
                },
                "owner": {
                    "type": "string",
                    "description": "Filter by project owner username",
                },
                "created_after": {
                    "type": "string",
                    "description": "Filter projects created after this date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)",
                },
                "created_before": {
                    "type": "string",
                    "description": "Filter projects created before this date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)",
                },
                "updated_after": {
                    "type": "string",
                    "description": "Filter projects updated after this date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)",
                },
                "updated_before": {
                    "type": "string",
                    "description": "Filter projects updated before this date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)",
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 25,
                    "description": "Maximum number of results to return (1-100)",
                },
                "sort_by": {
                    "type": "string",
                    "enum": ["created", "updated", "name"],
                    "default": "updated",
                    "description": "Sort results by creation date, update date, or name",
                },
                "sort_order": {
                    "type": "string",
                    "enum": ["asc", "desc"],
                    "default": "desc",
                    "description": "Sort order: ascending or descending",
                },
            },
            "additionalProperties": False,
        },
    ),
    Tool(
        name="search_projects_advanced",
        description="""Advanced project search with structured query builder.

        Provides a more structured approach to project searching using a configuration
        object with nested search criteria. Supports complex search scenarios with
        fluent query building and enhanced result presentation.

        Ideal for:
        • Complex multi-criteria searches
        • Programmatic search configuration
        • Search result analysis and reporting
        • Advanced filtering workflows
        """,
        inputSchema={
            "type": "object",
            "properties": {
                "search_config": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Text search query"},
                        "public": {
                            "type": "boolean",
                            "description": "Filter for public projects only",
                        },
                        "private": {
                            "type": "boolean",
                            "description": "Filter for private projects only",
                        },
                        "owner": {
                            "type": "string",
                            "description": "Project owner username",
                        },
                        "created_after": {
                            "type": "string",
                            "description": "Created after date (ISO format)",
                        },
                        "created_before": {
                            "type": "string",
                            "description": "Created before date (ISO format)",
                        },
                        "updated_after": {
                            "type": "string",
                            "description": "Updated after date (ISO format)",
                        },
                        "updated_before": {
                            "type": "string",
                            "description": "Updated before date (ISO format)",
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 25,
                            "description": "Result limit",
                        },
                        "sort": {
                            "type": "object",
                            "properties": {
                                "by": {
                                    "type": "string",
                                    "enum": ["created", "updated", "name"],
                                    "default": "updated",
                                    "description": "Sort field",
                                },
                                "ascending": {
                                    "type": "boolean",
                                    "default": False,
                                    "description": "Sort in ascending order",
                                },
                            },
                            "additionalProperties": False,
                        },
                    },
                    "additionalProperties": False,
                }
            },
            "required": ["search_config"],
            "additionalProperties": False,
        },
    ),
]

# Mapping of tool names to their handler functions
SEARCH_PROJECT_TOOL_HANDLERS = {
    "search_projects": search_projects_handler,
    "search_projects_advanced": search_projects_advanced_handler,
}

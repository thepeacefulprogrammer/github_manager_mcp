"""
MCP tool handlers for subtask management operations.

This module provides handlers for managing Subtasks within GitHub Projects v2 Tasks,
including creation, listing, updating, and deletion operations with comprehensive
error handling and parameter validation.
"""

import logging
from typing import Any, Dict, List, Optional

from mcp.types import CallToolResult, TextContent, Tool

from ..models.subtask import Subtask, SubtaskStatus
from ..utils.query_builder import ProjectQueryBuilder

logger = logging.getLogger(__name__)

# Global GitHub client instance
_github_client = None


def get_github_client():
    """Get the current GitHub client instance."""
    return _github_client


def initialize_github_client(token: str) -> None:
    """Initialize the GitHub client with authentication token."""
    global _github_client
    from ..github_client import GitHubClient

    _github_client = GitHubClient(token)


def _build_subtask_description_body(
    description: str,
    parent_task_id: str,
    order: int = 1,
) -> str:
    """
    Build a comprehensive description body for a subtask.

    Args:
        description: Base description text
        parent_task_id: ID of the parent task
        order: Order position within parent task

    Returns:
        Formatted description body with metadata
    """
    lines = []

    if description:
        lines.append(description)
        lines.append("")

    lines.extend(
        [
            "## Subtask Metadata",
            f"- **Type:** Subtask",
            f"- **Parent Task ID:** {parent_task_id}",
            f"- **Order:** {order}",
            f"- **Status:** Incomplete",
            "",
            "---",
            "*This subtask was created via GitHub Project Manager MCP*",
        ]
    )

    return "\n".join(lines)


def _build_add_subtask_mutation(
    project_id: str,
    title: str,
    body: str,
) -> str:
    """
    Build GraphQL mutation for creating a new subtask as a draft issue.

    Args:
        project_id: GitHub project ID
        title: Subtask title
        body: Subtask description body

    Returns:
        GraphQL mutation string
    """
    query_builder = ProjectQueryBuilder()

    # Escape strings for GraphQL
    escaped_title = query_builder._escape_string(title)
    escaped_body = query_builder._escape_string(body)
    escaped_project_id = query_builder._escape_string(project_id)

    mutation = f"""
mutation {{
  addProjectV2DraftIssue(input: {{
    projectId: {escaped_project_id}
    title: {escaped_title}
    body: {escaped_body}
  }}) {{
    projectItem {{
      id
      content {{
        ... on DraftIssue {{
          title
          body
          createdAt
        }}
      }}
    }}
  }}
}}
""".strip()

    return mutation


async def add_subtask_handler(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle add_subtask tool calls.

    Creates a new Subtask as a draft issue in a GitHub project with association
    to a parent Task. Supports subtask metadata including order positioning
    and comprehensive description formatting.

    Args:
        arguments: Tool call arguments containing:
            - project_id (required): GitHub project ID
            - parent_task_id (required): ID of parent Task
            - title (required): Subtask title
            - description (optional): Subtask description
            - order (optional): Order position (defaults to 1)

    Returns:
        CallToolResult with operation results
    """
    try:
        # Validate required parameters
        project_id = arguments.get("project_id", "").strip()
        parent_task_id = arguments.get("parent_task_id", "").strip()
        title = arguments.get("title", "").strip()

        if not project_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: project_id is required to create subtask",
                    )
                ],
                isError=True,
            )

        if not parent_task_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: parent_task_id is required to create subtask",
                    )
                ],
                isError=True,
            )

        if not title:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: title is required to create subtask",
                    )
                ],
                isError=True,
            )

        # Extract optional parameters
        description = arguments.get("description", "")
        order = arguments.get("order", 1)

        # Validate order if provided
        if order is not None:
            try:
                order = int(order)
                if order <= 0:
                    raise ValueError("Must be positive")
            except (ValueError, TypeError):
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text="Error: order must be a positive integer",
                        )
                    ],
                    isError=True,
                )

        # Check if GitHub client is initialized
        client = get_github_client()
        if not client:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: GitHub client not initialized. Please call initialize_github_client first.",
                    )
                ],
                isError=True,
            )

        # Build comprehensive subtask description
        body = _build_subtask_description_body(
            description=description,
            parent_task_id=parent_task_id,
            order=order,
        )

        # Build and execute GraphQL mutation
        mutation = _build_add_subtask_mutation(project_id, title, body)

        try:
            response = await client.mutate(mutation)
        except Exception as e:
            error_msg = str(e)

            # Handle specific error cases
            if "could not resolve to projectv2 node" in error_msg.lower():
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Error: Invalid project ID: {project_id}",
                        )
                    ],
                    isError=True,
                )

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: Failed to create subtask: {error_msg}",
                    )
                ],
                isError=True,
            )

        # Validate response structure
        if not response:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: Failed to create subtask: No data returned from API",
                    )
                ],
                isError=True,
            )

        project_item = response.get("addProjectV2DraftIssue", {}).get("projectItem")
        if not project_item:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: Failed to create subtask: Invalid response format",
                    )
                ],
                isError=True,
            )

        # Extract subtask information
        subtask_id = project_item.get("id")
        content = project_item.get("content", {})
        subtask_title = content.get("title", title)
        created_at = content.get("createdAt", "")

        # Format success response
        result_text = f"""Subtask created successfully!

**Subtask Details:**
- **ID:** {subtask_id}
- **Title:** {subtask_title}
- **Parent Task:** {parent_task_id}
- **Order:** {order}
- **Project:** {project_id}
- **Created:** {created_at}"""

        if description:
            result_text += f"\n- **Description:** {description}"

        return CallToolResult(
            content=[TextContent(type="text", text=result_text)],
            isError=False,
        )

    except Exception as e:
        logger.error(f"Unexpected error in add_subtask_handler: {e}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error: Unexpected error creating subtask: {str(e)}",
                )
            ],
            isError=True,
        )


def _filter_subtasks_by_parent(
    items: List[Dict[str, Any]],
    parent_task_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Filter project items to find subtasks, optionally by parent task.

    Args:
        items: List of project items from GraphQL response
        parent_task_id: Optional parent task ID to filter by

    Returns:
        Filtered list of subtask items
    """
    subtasks = []

    for item in items:
        content = item.get("content", {})
        body = content.get("body", "")

        # Check if this is a subtask by looking for metadata markers
        if "## Subtask Metadata" not in body:
            continue

        # If parent_task_id is specified, filter by it
        if parent_task_id:
            if f"- **Parent Task ID:** {parent_task_id}" not in body:
                continue

        subtasks.append(item)

    return subtasks


def _format_subtask_list_response(
    subtasks: List[Dict[str, Any]],
    project_id: str,
    parent_task_id: Optional[str] = None,
    total_count: int = 0,
    has_next_page: bool = False,
    end_cursor: Optional[str] = None,
) -> str:
    """
    Format the response for subtask listing.

    Args:
        subtasks: List of subtask items
        project_id: GitHub project ID
        parent_task_id: Optional parent task ID filter
        total_count: Total number of subtasks
        has_next_page: Whether there are more pages
        end_cursor: Cursor for next page

    Returns:
        Formatted response text
    """
    lines = []

    # Header with project info
    if parent_task_id:
        lines.append(f"📋 **Subtasks in Project** (Parent Task: {parent_task_id})")
    else:
        lines.append("📋 **Subtasks in Project**")

    lines.append(f"**Project ID:** {project_id}")
    lines.append(f"**Total:** {len(subtasks)} subtasks")
    lines.append(f"**Showing:** {len(subtasks)} subtasks")
    lines.append("")

    # Pagination info
    if has_next_page:
        lines.append(f"**Has next page:** {has_next_page}")
        if end_cursor:
            lines.append(f"**Next cursor:** {end_cursor}")
        lines.append("")

    if not subtasks:
        lines.append("No subtasks found in this project.")
        return "\n".join(lines)

    # List each subtask
    for i, item in enumerate(subtasks, 1):
        content = item.get("content", {})
        title = content.get("title", "Untitled")
        item_id = item.get("id", "")
        created_at = content.get("createdAt", "")
        updated_at = content.get("updatedAt", "")
        body = content.get("body", "")

        lines.append(f"**{i}. {title}**")
        lines.append(f"   - **Type:** Subtask")
        lines.append(f"   - **Item ID:** {item_id}")
        lines.append(f"   - **Created:** {created_at}")
        lines.append(f"   - **Updated:** {updated_at}")

        # Extract parent task from metadata
        if "- **Parent Task ID:** " in body:
            parent_start = body.find("- **Parent Task ID:** ") + len(
                "- **Parent Task ID:** "
            )
            parent_end = body.find("\n", parent_start)
            if parent_end == -1:
                parent_end = len(body)
            parent_id = body[parent_start:parent_end].strip()
            lines.append(f"   - **Parent Task:** {parent_id}")

        # Extract order from metadata
        if "- **Order:** " in body:
            order_start = body.find("- **Order:** ") + len("- **Order:** ")
            order_end = body.find("\n", order_start)
            if order_end == -1:
                order_end = len(body)
            order = body[order_start:order_end].strip()
            lines.append(f"   - **Order:** {order}")

        # Add description if available (before metadata section)
        if body and "## Subtask Metadata" in body:
            desc_part = body.split("## Subtask Metadata")[0].strip()
            if desc_part:
                lines.append(f"   - **Description:** {desc_part[:100]}...")

        lines.append("")

    return "\n".join(lines)


async def list_subtasks_handler(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle list_subtasks tool calls.

    Lists all subtasks in a GitHub project with optional filtering by parent task.
    Supports pagination for large result sets and provides comprehensive metadata
    about each subtask including parent task relationships and order positioning.

    Args:
        arguments: Tool call arguments containing:
            - project_id (required): GitHub project ID
            - parent_task_id (optional): Filter by parent task ID
            - first (optional): Number of items to fetch (max 100, default 25)
            - after (optional): Cursor for pagination

    Returns:
        CallToolResult with subtask listing results
    """
    try:
        # Validate required parameters
        project_id = arguments.get("project_id", "").strip()

        if not project_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: project_id is required to list subtasks",
                    )
                ],
                isError=True,
            )

        # Extract optional parameters
        parent_task_id = arguments.get("parent_task_id")
        if parent_task_id:
            parent_task_id = parent_task_id.strip()
            if not parent_task_id:
                parent_task_id = None

        first = arguments.get("first", 25)
        after = arguments.get("after")

        # Validate pagination parameters
        if first is not None:
            try:
                first = int(first)
                if first <= 0:
                    raise ValueError("Must be positive")
                if first > 100:
                    raise ValueError("Cannot exceed 100")
            except (ValueError, TypeError):
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text="Error: first must be a positive integer and cannot exceed 100",
                        )
                    ],
                    isError=True,
                )

        # Check if GitHub client is initialized
        client = get_github_client()
        if not client:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: GitHub client not initialized. Please call initialize_github_client first.",
                    )
                ],
                isError=True,
            )

        # Build and execute GraphQL query
        query_builder = ProjectQueryBuilder()
        query = query_builder.list_subtasks_in_project(
            project_id=project_id,
            parent_task_id=parent_task_id,
            first=first,
            after=after,
        )

        try:
            response = await client.query(query)
        except Exception as e:
            error_msg = str(e)
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error listing subtasks: {error_msg}",
                    )
                ],
                isError=True,
            )

        # Parse response
        if not response or "node" not in response:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error listing subtasks: Invalid response format",
                    )
                ],
                isError=True,
            )

        project_data = response["node"]
        if not project_data or "items" not in project_data:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error listing subtasks: Invalid project data",
                    )
                ],
                isError=True,
            )

        items_data = project_data["items"]
        all_items = items_data.get("nodes", [])
        total_count = items_data.get("totalCount", 0)
        page_info = items_data.get("pageInfo", {})
        has_next_page = page_info.get("hasNextPage", False)
        end_cursor = page_info.get("endCursor")

        # Filter items to find subtasks
        subtasks = _filter_subtasks_by_parent(all_items, parent_task_id)

        # Format response
        result_text = _format_subtask_list_response(
            subtasks=subtasks,
            project_id=project_id,
            parent_task_id=parent_task_id,
            total_count=total_count,
            has_next_page=has_next_page,
            end_cursor=end_cursor,
        )

        return CallToolResult(
            content=[TextContent(type="text", text=result_text)],
            isError=False,
        )

    except Exception as e:
        logger.error(f"Unexpected error in list_subtasks_handler: {e}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error: Unexpected error listing subtasks: {str(e)}",
                )
            ],
            isError=True,
        )


# Tool definitions
ADD_SUBTASK_TOOL = Tool(
    name="add_subtask",
    description="Create a new subtask and associate it with a parent Task in a GitHub project. Subtasks represent specific work items within a larger Task.",
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "GitHub Projects v2 project ID (e.g., 'PVT_kwDOA...')",
            },
            "parent_task_id": {
                "type": "string",
                "description": "ID of the parent Task this subtask belongs to (e.g., 'PVTI_kwDOA...')",
            },
            "title": {
                "type": "string",
                "description": "Subtask title/summary",
            },
            "description": {
                "type": "string",
                "description": "Optional detailed description of the subtask",
                "default": "",
            },
            "order": {
                "type": "integer",
                "description": "Order position within the parent task (default: 1)",
                "minimum": 1,
                "default": 1,
            },
        },
        "required": ["project_id", "parent_task_id", "title"],
    },
)

LIST_SUBTASKS_TOOL = Tool(
    name="list_subtasks",
    description="List subtasks in a GitHub project with optional filtering by parent task. Supports pagination and returns detailed information about each subtask including status, parent task, and metadata.",
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "GitHub Projects v2 project ID (e.g., 'PVT_kwDOA...')",
            },
            "parent_task_id": {
                "type": "string",
                "description": "Optional: Filter subtasks by parent task ID (e.g., 'PVTI_kwDOA...')",
            },
            "first": {
                "type": "integer",
                "description": "Number of subtasks to retrieve (default: 25, max: 100)",
                "minimum": 1,
                "maximum": 100,
                "default": 25,
            },
            "after": {
                "type": "string",
                "description": "Cursor for pagination - retrieve subtasks after this cursor",
            },
        },
        "required": ["project_id"],
    },
)

# Tool exports
SUBTASK_TOOLS = [ADD_SUBTASK_TOOL, LIST_SUBTASKS_TOOL]

SUBTASK_TOOL_HANDLERS = {
    "add_subtask": add_subtask_handler,
    "list_subtasks": list_subtasks_handler,
}

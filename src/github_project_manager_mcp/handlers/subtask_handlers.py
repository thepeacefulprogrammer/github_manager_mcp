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


def _parse_subtask_metadata(body: str) -> Dict[str, Any]:
    """
    Parse subtask metadata from issue body.

    Args:
        body: Issue body content

    Returns:
        Dictionary with parsed metadata or None if invalid format
    """
    metadata = {}

    if "## Subtask Metadata" not in body:
        return None

    # Extract metadata section
    lines = body.split("\n")
    in_metadata = False

    for line in lines:
        line = line.strip()
        if line == "## Subtask Metadata":
            in_metadata = True
            continue
        elif in_metadata and line.startswith("---"):
            break  # End of metadata section
        elif in_metadata and line.startswith("- **"):
            # Parse metadata line: - **Key:** Value
            if ":" in line:
                key_part = line.split(":**")[0].replace("- **", "")
                value_part = line.split(":**", 1)[1].strip()

                # Map keys to internal format
                if key_part == "Type":
                    metadata["type"] = value_part
                elif key_part == "Parent Task ID":
                    metadata["parent_task_id"] = value_part
                elif key_part == "Order":
                    try:
                        metadata["order"] = int(value_part)
                    except ValueError:
                        metadata["order"] = 1
                elif key_part == "Status":
                    metadata["status"] = value_part

    return metadata


def _update_subtask_metadata(
    body: str,
    new_description: Optional[str] = None,
    new_status: Optional[str] = None,
    new_order: Optional[int] = None,
) -> str:
    """
    Update subtask metadata in issue body.

    Args:
        body: Original issue body
        new_description: New description (if provided)
        new_status: New status (if provided)
        new_order: New order (if provided)

    Returns:
        Updated body with new metadata
    """
    # Parse existing metadata
    metadata = _parse_subtask_metadata(body)
    if not metadata:
        raise ValueError("Invalid subtask format - metadata section not found")

    # Update metadata values
    if new_status is not None:
        metadata["status"] = new_status
    if new_order is not None:
        metadata["order"] = new_order

    # Split body into description and metadata sections
    if "## Subtask Metadata" in body:
        description_part = body.split("## Subtask Metadata")[0].strip()
    else:
        description_part = ""

    # Use new description if provided, otherwise keep existing
    if new_description is not None:
        description_part = new_description.strip()

    # Rebuild the body with updated metadata
    lines = []

    if description_part:
        lines.append(description_part)
        lines.append("")

    lines.extend(
        [
            "## Subtask Metadata",
            f"- **Type:** {metadata.get('type', 'Subtask')}",
            f"- **Parent Task ID:** {metadata.get('parent_task_id', '')}",
            f"- **Order:** {metadata.get('order', 1)}",
            f"- **Status:** {metadata.get('status', 'Incomplete')}",
            "",
            "---",
            "*This subtask was created via GitHub Project Manager MCP*",
        ]
    )

    return "\n".join(lines)


def _build_update_subtask_mutation(
    subtask_item_id: str,
    title: Optional[str] = None,
    body: Optional[str] = None,
) -> str:
    """
    Build GraphQL mutation for updating a subtask.

    Args:
        subtask_item_id: ID of the subtask item to update
        title: New title (if provided)
        body: New body content (if provided)

    Returns:
        GraphQL mutation string
    """
    query_builder = ProjectQueryBuilder()

    # Build input fields
    input_fields = []

    if title is not None:
        escaped_title = query_builder._escape_string(title)
        input_fields.append(f"title: {escaped_title}")

    if body is not None:
        escaped_body = query_builder._escape_string(body)
        input_fields.append(f"body: {escaped_body}")

    input_str = ", ".join(input_fields)
    escaped_id = query_builder._escape_string(subtask_item_id)

    mutation = f"""
mutation {{
  updateIssue(input: {{
    id: {escaped_id}
    {input_str}
  }}) {{
    issue {{
      id
      title
      body
      updatedAt
    }}
  }}
}}
""".strip()

    return mutation


async def update_subtask_handler(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle update_subtask tool calls.

    Updates a Subtask's content and metadata within a GitHub project.
    Supports updating title, description, status, and order with comprehensive
    validation and metadata preservation.

    Args:
        arguments: Tool call arguments containing:
            - subtask_item_id (required): GitHub item ID of the subtask
            - title (optional): New subtask title
            - description (optional): New subtask description
            - status (optional): New status ("Incomplete" or "Complete")
            - order (optional): New order position (positive integer)

    Returns:
        CallToolResult with operation results
    """
    try:
        # Validate required parameters
        subtask_item_id = arguments.get("subtask_item_id", "").strip()

        if not subtask_item_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: subtask_item_id is required to update subtask",
                    )
                ],
                isError=True,
            )

        # Extract optional update parameters
        new_title = arguments.get("title")
        new_description = arguments.get("description")
        new_status = arguments.get("status")
        new_order = arguments.get("order")

        # Validate that at least one field is provided for update
        update_fields = [new_title, new_description, new_status, new_order]
        if all(field is None for field in update_fields):
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: At least one field must be provided for update (title, description, status, or order)",
                    )
                ],
                isError=True,
            )

        # Validate status if provided
        if new_status is not None:
            valid_statuses = ["Incomplete", "Complete"]
            if new_status not in valid_statuses:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Error: Invalid status value '{new_status}'. Valid values are: {', '.join(valid_statuses)}",
                        )
                    ],
                    isError=True,
                )

        # Validate order if provided
        if new_order is not None:
            try:
                new_order = int(new_order)
                if new_order <= 0:
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

        # First, retrieve the current subtask content
        query_builder = ProjectQueryBuilder()
        get_content_query = f"""
query {{
  node(id: "{subtask_item_id}") {{
    id
    ... on ProjectV2Item {{
      content {{
        ... on DraftIssue {{
          title
          body
        }}
      }}
    }}
  }}
}}
""".strip()

        try:
            content_response = await client.query(get_content_query)
        except Exception as e:
            logger.error(f"Error retrieving subtask content: {e}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: Failed to retrieve subtask content: {str(e)}",
                    )
                ],
                isError=True,
            )

        # Validate content response
        if (
            not content_response
            or "node" not in content_response
            or not content_response["node"]
        ):
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: Subtask not found or inaccessible",
                    )
                ],
                isError=True,
            )

        node_data = content_response["node"]
        if "content" not in node_data or not node_data["content"]:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: Subtask content not found",
                    )
                ],
                isError=True,
            )

        current_content = node_data["content"]
        current_title = current_content.get("title", "")
        current_body = current_content.get("body", "")

        # Validate that this is actually a subtask
        try:
            metadata = _parse_subtask_metadata(current_body)
            if not metadata or metadata.get("type") != "Subtask":
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text="Error: Invalid subtask format - this item is not a valid subtask",
                        )
                    ],
                    isError=True,
                )
        except Exception:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: Invalid subtask format - could not parse metadata",
                    )
                ],
                isError=True,
            )

        # Prepare updated values
        updated_title = new_title if new_title is not None else current_title

        # Update body with new metadata and description
        try:
            updated_body = _update_subtask_metadata(
                current_body,
                new_description=new_description,
                new_status=new_status,
                new_order=new_order,
            )
        except Exception as e:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: Failed to update metadata: {str(e)}",
                    )
                ],
                isError=True,
            )

        # Build and execute update mutation
        mutation = _build_update_subtask_mutation(
            subtask_item_id=subtask_item_id,
            title=updated_title if new_title is not None else None,
            body=updated_body,
        )

        try:
            update_response = await client.mutate(mutation)
        except Exception as e:
            logger.error(f"Error updating subtask: {e}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: Failed to update subtask: {str(e)}",
                    )
                ],
                isError=True,
            )

        # Validate update response
        if not update_response:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: No response data received from update operation",
                    )
                ],
                isError=True,
            )

        # Extract updated subtask information
        update_data = update_response.get("updateIssue", {})
        issue_data = update_data.get("issue", {})

        updated_metadata = _parse_subtask_metadata(updated_body)

        # Build success response
        result_lines = [
            "🎉 **Subtask updated successfully!**",
            "",
            f"**Subtask ID:** {subtask_item_id}",
            f"**Title:** {updated_title}",
            f"**Status:** {updated_metadata.get('status', 'Unknown')}",
            f"**Order:** {updated_metadata.get('order', 'Unknown')}",
            f"**Parent Task:** {updated_metadata.get('parent_task_id', 'Unknown')}",
        ]

        if new_description is not None:
            # Show truncated description
            desc_preview = (
                new_description[:100] + "..."
                if len(new_description) > 100
                else new_description
            )
            result_lines.extend(
                [
                    "",
                    f"**Description:** {desc_preview}",
                ]
            )

        result_lines.extend(
            [
                "",
                f"**Updated:** {issue_data.get('updatedAt', 'Unknown')}",
            ]
        )

        result_text = "\n".join(result_lines)

        return CallToolResult(
            content=[TextContent(type="text", text=result_text)],
            isError=False,
        )

    except Exception as e:
        logger.error(f"Unexpected error in update_subtask_handler: {e}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error: Unexpected error updating subtask: {str(e)}",
                )
            ],
            isError=True,
        )


def _build_delete_subtask_mutation(subtask_item_id: str) -> str:
    """
    Build GraphQL mutation for deleting a subtask.

    Args:
        subtask_item_id: ID of the subtask item to delete

    Returns:
        GraphQL mutation string
    """
    query_builder = ProjectQueryBuilder()
    escaped_id = query_builder._escape_string(subtask_item_id)

    mutation = f"""
mutation {{
  deleteProjectV2Item(input: {{
    projectId: ""
    itemId: {escaped_id}
  }}) {{
    deletedItemId
  }}
}}
""".strip()

    return mutation


async def delete_subtask_handler(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle delete_subtask tool calls.

    Deletes a Subtask from a GitHub project with safety confirmation requirements.
    This action is permanent and cannot be undone.

    Args:
        arguments: Tool call arguments containing:
            - project_id (required): GitHub project ID
            - subtask_item_id (required): ID of the subtask item to delete
            - confirm (required): Boolean confirmation (must be True)

    Returns:
        CallToolResult with operation results
    """
    try:
        # Validate required parameters
        project_id = arguments.get("project_id", "").strip()
        subtask_item_id = arguments.get("subtask_item_id", "").strip()
        confirm = arguments.get("confirm")

        if not project_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: project_id is required to delete subtask",
                    )
                ],
                isError=True,
            )

        if not subtask_item_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: subtask_item_id is required to delete subtask",
                    )
                ],
                isError=True,
            )

        # Validate confirmation requirement
        if confirm is None or not confirm:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: Confirmation is required to delete subtask. Set 'confirm' to true to proceed with deletion.",
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

        # Build and execute delete mutation
        mutation = _build_delete_subtask_mutation(subtask_item_id)

        try:
            response = await client.mutate(mutation)
        except Exception as e:
            logger.error(f"Error deleting subtask: {e}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: Failed to delete subtask: {str(e)}",
                    )
                ],
                isError=True,
            )

        # Validate response
        if not response:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: No response data received from delete operation",
                    )
                ],
                isError=True,
            )

        # Parse response
        delete_data = response.get("deleteProjectV2Item", {})
        if not delete_data:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: Invalid response format - deleteProjectV2Item not found",
                    )
                ],
                isError=True,
            )

        # Get deleted item ID if available (for confirmation)
        deleted_item_id = delete_data.get("deletedItemId")

        # Build success response
        result_lines = [
            "🗑️ **Subtask deleted successfully!**",
            "",
            f"**Project ID:** {project_id}",
            f"**Subtask Item ID:** {subtask_item_id}",
        ]

        if deleted_item_id:
            result_lines.append(f"**Deleted Item ID:** {deleted_item_id}")

        result_lines.extend(
            [
                "",
                "⚠️ **This action is permanent and cannot be undone.**",
            ]
        )

        result_text = "\n".join(result_lines)

        return CallToolResult(
            content=[TextContent(type="text", text=result_text)],
            isError=False,
        )

    except Exception as e:
        logger.error(f"Unexpected error in delete_subtask_handler: {e}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error: Unexpected error deleting subtask: {str(e)}",
                )
            ],
            isError=True,
        )


def _build_get_subtask_content_query(subtask_item_id: str) -> str:
    """
    Build GraphQL query to get subtask content by item ID.

    Args:
        subtask_item_id: GitHub Projects v2 item ID of the subtask

    Returns:
        GraphQL query string
    """
    query_builder = ProjectQueryBuilder()
    escaped_item_id = query_builder._escape_string(subtask_item_id)

    query = f"""
query {{
  node(id: {escaped_item_id}) {{
    ... on ProjectV2Item {{
      content {{
        ... on DraftIssue {{
          title
          body
        }}
        ... on Issue {{
          title
          body
        }}
      }}
    }}
  }}
}}
""".strip()

    return query


async def complete_subtask_handler(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle complete_subtask tool calls.

    Marks a subtask as complete by updating its status in the subtask metadata.
    This is a convenience method that automatically sets the status to "Complete"
    without requiring other parameters.

    Args:
        arguments: Tool call arguments containing:
            - subtask_item_id (required): ID of the subtask item to complete

    Returns:
        CallToolResult with operation results
    """
    try:
        # Validate required parameters
        subtask_item_id = arguments.get("subtask_item_id", "").strip()

        if not subtask_item_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: subtask_item_id is required to complete subtask",
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

        # Get current subtask content to check status and retrieve metadata
        query = _build_get_subtask_content_query(subtask_item_id)

        try:
            response = await client.query(query)
        except Exception as e:
            logger.error(f"Error fetching subtask content: {e}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: Failed to fetch subtask content: {str(e)}",
                    )
                ],
                isError=True,
            )

        # Validate response
        if not response or not response.get("node"):
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: Subtask content not found. The item may not exist or you may not have access to it.",
                    )
                ],
                isError=True,
            )

        # Get content from response
        node = response["node"]
        content = node.get("content")
        if not content:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: Subtask content not found in response.",
                    )
                ],
                isError=True,
            )

        current_title = content.get("title", "")
        current_body = content.get("body", "")

        # Validate this is actually a subtask by checking metadata
        metadata = _parse_subtask_metadata(current_body)
        if not metadata or metadata.get("type") != "Subtask":
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: Invalid subtask content format. This item does not appear to be a subtask.",
                    )
                ],
                isError=True,
            )

        current_status = metadata.get("status", "Incomplete")

        # Check if already complete
        if current_status == "Complete":
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"✅ **Subtask is already complete!**\n\n**Title:** {current_title}\n**Status:** {current_status}",
                    )
                ],
                isError=False,
            )

        # Update status to Complete
        updated_body = _update_subtask_metadata(
            current_body,
            new_status="Complete",
        )

        # Build and execute update mutation
        mutation = _build_update_subtask_mutation(
            subtask_item_id=subtask_item_id,
            title=None,  # Keep existing title
            body=updated_body,
        )

        try:
            update_response = await client.mutate(mutation)
        except Exception as e:
            logger.error(f"Error completing subtask: {e}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: Failed to complete subtask: {str(e)}",
                    )
                ],
                isError=True,
            )

        # Validate update response
        if not update_response:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: No response data received from completion operation",
                    )
                ],
                isError=True,
            )

        # Parse update response
        update_data = update_response.get("updateIssue", {})
        if not update_data:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: Invalid response format from completion operation",
                    )
                ],
                isError=True,
            )

        updated_issue = update_data.get("issue", {})
        updated_title = updated_issue.get("title", current_title)

        # Build success response
        result_lines = [
            "✅ **Subtask completed successfully!**",
            "",
            f"**Title:** {updated_title}",
            f"**Subtask ID:** {subtask_item_id}",
            f"**Status:** Complete",
            "",
            "🎉 **Great job! This subtask is now marked as complete.**",
        ]

        result_text = "\n".join(result_lines)

        return CallToolResult(
            content=[TextContent(type="text", text=result_text)],
            isError=False,
        )

    except Exception as e:
        logger.error(f"Unexpected error in complete_subtask_handler: {e}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error: Unexpected error completing subtask: {str(e)}",
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

UPDATE_SUBTASK_TOOL = Tool(
    name="update_subtask",
    description="Update a subtask's content and status. Supports updating title, description, status, and order with comprehensive validation and metadata preservation.",
    inputSchema={
        "type": "object",
        "properties": {
            "subtask_item_id": {
                "type": "string",
                "description": "GitHub Projects v2 item ID of the subtask to update (e.g., 'PVTI_kwDOA...')",
            },
            "title": {
                "type": "string",
                "description": "New subtask title",
            },
            "description": {
                "type": "string",
                "description": "New subtask description",
            },
            "status": {
                "type": "string",
                "description": "New subtask status",
                "enum": ["Incomplete", "Complete"],
            },
            "order": {
                "type": "integer",
                "description": "New order position within the parent task",
                "minimum": 1,
            },
        },
        "required": ["subtask_item_id"],
    },
)

DELETE_SUBTASK_TOOL = Tool(
    name="delete_subtask",
    description="Delete a subtask from a GitHub project. This action is permanent and cannot be undone.",
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "GitHub Projects v2 project ID (e.g., 'PVT_kwDOA...')",
            },
            "subtask_item_id": {
                "type": "string",
                "description": "GitHub Projects v2 item ID of the subtask to delete (e.g., 'PVTI_kwDOA...')",
            },
            "confirm": {
                "type": "boolean",
                "description": "Confirmation that you want to delete the subtask (must be true)",
            },
        },
        "required": ["project_id", "subtask_item_id", "confirm"],
    },
)

COMPLETE_SUBTASK_TOOL = Tool(
    name="complete_subtask",
    description="Mark a subtask as complete. This is a convenience method that automatically sets the subtask status to 'Complete' without requiring other parameters.",
    inputSchema={
        "type": "object",
        "properties": {
            "subtask_item_id": {
                "type": "string",
                "description": "GitHub Projects v2 item ID of the subtask to complete (e.g., 'PVTI_kwDOA...')",
            },
        },
        "required": ["subtask_item_id"],
    },
)

# Tool exports
SUBTASK_TOOLS = [
    ADD_SUBTASK_TOOL,
    LIST_SUBTASKS_TOOL,
    UPDATE_SUBTASK_TOOL,
    DELETE_SUBTASK_TOOL,
    COMPLETE_SUBTASK_TOOL,
]

SUBTASK_TOOL_HANDLERS = {
    "add_subtask": add_subtask_handler,
    "list_subtasks": list_subtasks_handler,
    "update_subtask": update_subtask_handler,
    "delete_subtask": delete_subtask_handler,
    "complete_subtask": complete_subtask_handler,
}

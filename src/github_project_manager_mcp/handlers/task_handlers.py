"""
Task handlers for GitHub Projects v2.

This module provides MCP tool handlers for managing Tasks as items within
GitHub Projects v2, including creation with parent PRD association and
comprehensive task lifecycle management.
"""

import logging
from typing import Any, Dict, List, Optional

from mcp.types import CallToolResult, TextContent, Tool

from github_project_manager_mcp.github_client import GitHubClient
from github_project_manager_mcp.models.task import Task, TaskPriority, TaskStatus
from github_project_manager_mcp.utils.query_builder import ProjectQueryBuilder

logger = logging.getLogger(__name__)

# Global GitHub client instance
_github_client: Optional[GitHubClient] = None


def get_github_client() -> Optional[GitHubClient]:
    """Get the initialized GitHub client."""
    return _github_client


def initialize_github_client(token: str) -> None:
    """Initialize the GitHub client with authentication token."""
    global _github_client
    _github_client = GitHubClient(token)
    logger.info("GitHub client initialized for Task handlers")


def _build_task_description_body(
    description: str,
    parent_prd_id: str,
    priority: TaskPriority = TaskPriority.MEDIUM,
    estimated_hours: Optional[int] = None,
) -> str:
    """
    Build a comprehensive description body for Task with structured sections.

    Args:
        description: Base description
        parent_prd_id: ID of parent PRD
        priority: Task priority
        estimated_hours: Estimated hours for completion

    Returns:
        Formatted description with task metadata
    """
    body = description

    # Add parent PRD reference
    body += f"\n\n**Parent PRD:** {parent_prd_id}"

    # Add priority
    body += f"\n\n**Priority:** {priority.value}"

    # Add estimated hours if provided
    if estimated_hours is not None:
        body += f"\n\n**Estimated Hours:** {estimated_hours}"

    return body


def _build_add_task_mutation(
    project_id: str,
    title: str,
    body: str,
) -> str:
    """
    Build GraphQL mutation to add a Task (draft issue) to a project.

    Args:
        project_id: GitHub project ID
        title: Task title
        body: Task description body

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


async def create_task_handler(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle create_task tool calls.

    Creates a new Task as a draft issue in a GitHub project with association
    to a parent PRD. Supports task metadata including priority, estimated hours,
    and comprehensive description formatting.

    Args:
        arguments: Tool call arguments containing:
            - project_id (required): GitHub project ID
            - parent_prd_id (required): ID of parent PRD
            - title (required): Task title
            - description (optional): Task description
            - priority (optional): Task priority (defaults to "Medium")
            - estimated_hours (optional): Estimated hours for completion

    Returns:
        CallToolResult with operation results
    """
    try:
        # Validate required parameters
        project_id = arguments.get("project_id", "").strip()
        parent_prd_id = arguments.get("parent_prd_id", "").strip()
        title = arguments.get("title", "").strip()

        if not project_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: project_id is required to create task",
                    )
                ],
                isError=True,
            )

        if not parent_prd_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: parent_prd_id is required to create task",
                    )
                ],
                isError=True,
            )

        if not title:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: title is required to create task",
                    )
                ],
                isError=True,
            )

        # Extract optional parameters
        description = arguments.get("description", "")
        estimated_hours = arguments.get("estimated_hours")

        # Validate estimated_hours if provided
        if estimated_hours is not None:
            try:
                estimated_hours = int(estimated_hours)
                if estimated_hours <= 0:
                    raise ValueError("Must be positive")
            except (ValueError, TypeError):
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text="Error: estimated_hours must be a positive integer",
                        )
                    ],
                    isError=True,
                )

        # Validate and parse priority
        priority_str = arguments.get("priority", "Medium")
        try:
            priority = TaskPriority(priority_str)
        except ValueError:
            valid_priorities = [p.value for p in TaskPriority]
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: Invalid priority '{priority_str}'. Valid values: {', '.join(valid_priorities)}",
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

        # Build comprehensive task description
        body = _build_task_description_body(
            description=description,
            parent_prd_id=parent_prd_id,
            priority=priority,
            estimated_hours=estimated_hours,
        )

        # Build and execute GraphQL mutation
        mutation = _build_add_task_mutation(project_id, title, body)

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
                        text=f"Error: Failed to create task: {error_msg}",
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
                        text="Error: Failed to create task: No data returned from API",
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
                        text="Error: Failed to create task: Invalid response format",
                    )
                ],
                isError=True,
            )

        # Extract task information
        task_id = project_item.get("id")
        content = project_item.get("content", {})
        task_title = content.get("title", title)
        created_at = content.get("createdAt", "")

        # Format success response
        result_text = f"""Task created successfully!

**Task Details:**
- **ID:** {task_id}
- **Title:** {task_title}
- **Parent PRD:** {parent_prd_id}
- **Priority:** {priority.value}
- **Project:** {project_id}
- **Created:** {created_at}"""

        if estimated_hours:
            result_text += f"\n- **Estimated Hours:** {estimated_hours}"

        if description:
            result_text += f"\n- **Description:** {description}"

        return CallToolResult(
            content=[TextContent(type="text", text=result_text)],
            isError=False,
        )

    except Exception as e:
        logger.error(f"Unexpected error in create_task_handler: {e}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error: Unexpected error creating task: {str(e)}",
                )
            ],
            isError=True,
        )


async def list_tasks_handler(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle list_tasks tool calls.

    Lists all Tasks within a GitHub project with optional filtering by parent PRD.
    Supports pagination and returns detailed information about each task including
    status, priority, parent PRD, and creation/update timestamps.

    Args:
        arguments: Tool call arguments containing:
            - project_id (required): GitHub project ID
            - parent_prd_id (optional): Filter tasks by parent PRD ID
            - first (optional): Number of tasks to fetch (pagination, default: 25)
            - after (optional): Cursor for pagination

    Returns:
        CallToolResult with task list and pagination info
    """
    try:
        # Validate required parameters
        project_id = arguments.get("project_id", "").strip()

        if not project_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: project_id is required to list tasks in project",
                    )
                ],
                isError=True,
            )

        # Extract optional parameters
        parent_prd_id = arguments.get("parent_prd_id", "").strip() or None
        first = arguments.get("first", 25)
        after = arguments.get("after")

        # Validate first parameter
        if first is not None:
            try:
                first = int(first)
                if first <= 0 or first > 100:
                    raise ValueError("first must be between 1 and 100")
            except (ValueError, TypeError):
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text="Error: 'first' parameter must be a positive integer between 1 and 100",
                        )
                    ],
                    isError=True,
                )

        # Check if GitHub client is initialized
        github_client = get_github_client()
        if github_client is None:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: GitHub client not initialized. Please check your authentication.",
                    )
                ],
                isError=True,
            )

        # Build and execute query
        query_builder = ProjectQueryBuilder()
        query = query_builder.list_tasks_in_project(
            project_id=project_id, parent_prd_id=parent_prd_id, first=first, after=after
        )

        logger.info(
            f"Listing tasks in project: {project_id}, parent PRD: {parent_prd_id}"
        )
        response = await github_client.query(query)

        # Debug: log the full response
        logger.debug(f"GitHub API response: {response}")

        # Check for GraphQL errors
        if "errors" in response:
            error_messages = [
                error.get("message", "Unknown error") for error in response["errors"]
            ]
            logger.error(f"GraphQL errors: {error_messages}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error listing tasks: GraphQL errors: {'; '.join(error_messages)}",
                    )
                ],
                isError=True,
            )

        # Extract project data
        if "data" in response:
            data = response["data"]
        else:
            data = response

        node = data.get("node")
        if not node:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: Project with ID '{project_id}' not found or not accessible",
                    )
                ],
                isError=True,
            )

        project_title = node.get("title", "Unknown Project")
        items_data = node.get("items", {})
        total_count = items_data.get("totalCount", 0)
        page_info = items_data.get("pageInfo", {})
        items = items_data.get("nodes", [])

        # Filter for Tasks and format response
        tasks = []
        for item in items:
            content = item.get("content")
            if not content:
                continue

            # Extract item metadata
            item_id = item.get("id", "Unknown")
            item_created_at = item.get("createdAt", "Unknown")
            item_updated_at = item.get("updatedAt", "Unknown")

            # Extract field values (Parent PRD, priority, etc.)
            field_values = {}
            for field_value in item.get("fieldValues", {}).get("nodes", []):
                field_name = None
                field_val = None

                if "field" in field_value and field_value["field"]:
                    field_name = field_value["field"].get("name")

                if "text" in field_value:
                    field_val = field_value["text"]
                elif "name" in field_value:
                    field_val = field_value["name"]

                if field_name and field_val:
                    field_values[field_name] = field_val

            # Check if this item is a task by looking for Parent PRD field
            item_parent_prd_id = field_values.get("Parent PRD")

            # Apply parent PRD filter if specified
            if parent_prd_id and item_parent_prd_id != parent_prd_id:
                continue

            # Handle both DraftIssue and Issue types
            if "title" in content:
                title = content.get("title", "Untitled Task")
                body = content.get("body", "")
                created_at = content.get("createdAt", item_created_at)
                updated_at = content.get("updatedAt", item_updated_at)

                # Extract assignees
                assignees = []
                assignees_data = content.get("assignees", {})
                if assignees_data and "nodes" in assignees_data:
                    for assignee in assignees_data["nodes"]:
                        login = assignee.get("login", "")
                        name = assignee.get("name", "")
                        if login:
                            assignees.append(
                                f"{name} (@{login})" if name else f"@{login}"
                            )

                # Determine task type and additional info
                task_type = "Draft Issue"
                additional_info = {}

                if "number" in content:  # This is a regular Issue
                    task_type = "Issue"
                    additional_info["number"] = content.get("number")
                    additional_info["state"] = content.get("state", "OPEN")
                    repo_info = content.get("repository", {})
                    if repo_info:
                        repo_name = repo_info.get("name", "")
                        repo_owner = repo_info.get("owner", {}).get("login", "")
                        if repo_name and repo_owner:
                            additional_info["repository"] = f"{repo_owner}/{repo_name}"

                # Only include items that have a Parent PRD field (identifies them as tasks)
                if item_parent_prd_id:
                    tasks.append(
                        {
                            "item_id": item_id,
                            "title": title,
                            "body": body,
                            "type": task_type,
                            "parent_prd_id": item_parent_prd_id,
                            "created_at": created_at,
                            "updated_at": updated_at,
                            "assignees": assignees,
                            "field_values": field_values,
                            "additional_info": additional_info,
                        }
                    )

        # Build response text
        filter_text = f" (Parent PRD: {parent_prd_id})" if parent_prd_id else ""
        result_lines = [
            f"📋 **Tasks in Project: {project_title}**{filter_text}",
            f"**Project ID:** {project_id}",
            f"**Total:** {len(tasks)} tasks",
        ]

        # Add pagination info
        if page_info:
            result_lines.append(f"**Showing:** {len(tasks)} tasks")
            if page_info.get("hasNextPage"):
                result_lines.append("**Next page available**")

        result_lines.append("")

        if not tasks:
            result_lines.append("No tasks found in this project.")
        else:
            for idx, task in enumerate(tasks, 1):
                result_lines.append(f"## {idx}. {task['title']}")
                result_lines.append(f"**ID:** {task['item_id']}")
                result_lines.append(f"**Type:** {task['type']}")
                result_lines.append(f"**Parent PRD:** {task['parent_prd_id']}")

                # Add priority if available
                priority = task["field_values"].get("Priority")
                if priority:
                    result_lines.append(f"**Priority:** {priority}")

                # Add assignees if any
                if task["assignees"]:
                    result_lines.append(
                        f"**Assignees:** {', '.join(task['assignees'])}"
                    )

                # Add status if available
                status = task["field_values"].get("Status")
                if status:
                    result_lines.append(f"**Status:** {status}")

                result_lines.append(f"**Created:** {task['created_at']}")
                result_lines.append(f"**Updated:** {task['updated_at']}")

                # Add body preview if available
                if task["body"]:
                    # Extract first line or first 100 chars for preview
                    body_preview = task["body"].split("\n")[0]
                    if len(body_preview) > 100:
                        body_preview = body_preview[:97] + "..."
                    result_lines.append(f"**Description:** {body_preview}")

                # Add additional info for Issues
                if task["additional_info"].get("number"):
                    result_lines.append(
                        f"**Issue #:** {task['additional_info']['number']}"
                    )
                if task["additional_info"].get("repository"):
                    result_lines.append(
                        f"**Repository:** {task['additional_info']['repository']}"
                    )

                result_lines.append("")

        return CallToolResult(
            content=[TextContent(type="text", text="\n".join(result_lines))],
            isError=False,
        )

    except Exception as e:
        logger.error(f"Unexpected error in list_tasks_handler: {e}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error: Unexpected error listing tasks: {str(e)}",
                )
            ],
            isError=True,
        )


async def update_task_handler(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle update_task tool calls.

    Updates a Task's content (title, description) and/or project field values
    (status, priority, estimated_hours, actual_hours) using the GitHub Projects v2 API.

    Args:
        arguments: Tool call arguments containing:
            - task_item_id (required): GitHub project item ID
            - title (optional): New task title
            - description (optional): New task description
            - status (optional): New task status value
            - priority (optional): New task priority value
            - estimated_hours (optional): New estimated hours value
            - actual_hours (optional): New actual hours value

    Returns:
        CallToolResult with operation results
    """
    try:
        # Validate required parameters
        task_item_id = arguments.get("task_item_id", "").strip()

        if not task_item_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: task_item_id is required to update task",
                    )
                ],
                isError=True,
            )

        # Extract update parameters
        title = arguments.get("title")
        description = arguments.get("description")
        status_str = arguments.get("status")
        priority_str = arguments.get("priority")
        estimated_hours = arguments.get("estimated_hours")
        actual_hours = arguments.get("actual_hours")

        # Validate that at least one update field is provided
        update_fields = [
            title,
            description,
            status_str,
            priority_str,
            estimated_hours,
            actual_hours,
        ]
        if not any(field is not None for field in update_fields):
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: At least one field to update must be provided",
                    )
                ],
                isError=True,
            )

        # Validate status if provided
        if status_str is not None:
            try:
                status = TaskStatus(status_str)
            except ValueError:
                valid_statuses = [s.value for s in TaskStatus]
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Error: Invalid status '{status_str}'. Valid values: {', '.join(valid_statuses)}",
                        )
                    ],
                    isError=True,
                )

        # Validate priority if provided
        if priority_str is not None:
            try:
                priority = TaskPriority(priority_str)
            except ValueError:
                valid_priorities = [p.value for p in TaskPriority]
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Error: Invalid priority '{priority_str}'. Valid values: {', '.join(valid_priorities)}",
                        )
                    ],
                    isError=True,
                )

        # Validate estimated_hours if provided
        if estimated_hours is not None:
            try:
                estimated_hours = int(estimated_hours)
                if estimated_hours <= 0:
                    raise ValueError("Must be positive")
            except (ValueError, TypeError):
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text="Error: estimated_hours must be a positive integer",
                        )
                    ],
                    isError=True,
                )

        # Validate actual_hours if provided
        if actual_hours is not None:
            try:
                actual_hours = int(actual_hours)
                if actual_hours <= 0:
                    raise ValueError("Must be positive")
            except (ValueError, TypeError):
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text="Error: actual_hours must be a positive integer",
                        )
                    ],
                    isError=True,
                )

        # Get GitHub client
        client = get_github_client()
        if client is None:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: GitHub client not initialized. Please check your authentication settings.",
                    )
                ],
                isError=True,
            )

        query_builder = ProjectQueryBuilder()
        updated_fields = []

        # Step 1: Update task content (title/description) if provided
        if title is not None or description is not None:
            # Get the draft issue content ID
            content_query = query_builder.get_task_content_id(task_item_id)
            logger.info(f"Getting task content ID for task: {task_item_id}")
            content_response = await client.query(content_query)

            # Check for GraphQL errors
            if "errors" in content_response:
                error_messages = [
                    error["message"] for error in content_response["errors"]
                ]
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Error: GraphQL errors occurred: {'; '.join(error_messages)}",
                        )
                    ],
                    isError=True,
                )

            # Validate task item exists and has content
            node_data = content_response.get("node")
            if not node_data:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Error: Could not find project item with ID {task_item_id}",
                        )
                    ],
                    isError=True,
                )

            content_data = node_data.get("content")
            if not content_data:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Error: Project item {task_item_id} does not have content (may not be a draft issue)",
                        )
                    ],
                    isError=True,
                )

            draft_issue_id = content_data.get("id")
            if not draft_issue_id:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Error: Could not extract draft issue ID from project item {task_item_id}",
                        )
                    ],
                    isError=True,
                )

            # Update task content using the draft issue content ID
            mutation = query_builder.update_task(
                task_item_id=draft_issue_id,  # Use the content ID, not the project item ID
                title=title,
                description=description,
            )

            logger.info(
                f"Updating task '{draft_issue_id}' (from project item '{task_item_id}')"
            )
            response = await client.mutate(mutation)

            # Check for GraphQL errors
            if "errors" in response:
                error_messages = [error["message"] for error in response["errors"]]
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Error updating task: GraphQL errors: {'; '.join(error_messages)}",
                        )
                    ],
                    isError=True,
                )

            # Track successful content updates
            if title is not None:
                updated_fields.append("title")
            if description is not None:
                updated_fields.append("description")

        # Step 2: Update project field values if provided
        field_updates_needed = any(
            [
                status_str is not None,
                priority_str is not None,
                estimated_hours is not None,
                actual_hours is not None,
            ]
        )

        if field_updates_needed:
            # Get project item details and field definitions
            fields_query = query_builder.get_project_item_fields(task_item_id)
            logger.info(f"Fetching project item fields for task: {task_item_id}")
            fields_response = await client.query(fields_query)

            # Check for GraphQL errors
            if "errors" in fields_response:
                error_messages = [
                    error["message"] for error in fields_response["errors"]
                ]
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Error: GraphQL errors occurred: {'; '.join(error_messages)}",
                        )
                    ],
                    isError=True,
                )

            # Validate project item exists
            if not fields_response.get("node"):
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Error: Project item not found: {task_item_id}",
                        )
                    ],
                    isError=True,
                )

            project_item_data = fields_response["node"]
            project_data = project_item_data["project"]
            project_id = project_data["id"]

            # Parse available fields
            available_fields = {}
            for field in project_data["fields"]["nodes"]:
                # Skip empty field objects
                if not field or "name" not in field:
                    continue
                field_name = field["name"]
                field_id = field["id"]
                field_data_type = field.get("dataType", "")

                if field_data_type == "SINGLE_SELECT":
                    field_options = {
                        opt["name"]: opt["id"] for opt in field.get("options", [])
                    }
                    available_fields[field_name] = {
                        "id": field_id,
                        "type": "SINGLE_SELECT",
                        "options": field_options,
                    }
                elif field_data_type == "NUMBER":
                    available_fields[field_name] = {
                        "id": field_id,
                        "type": "NUMBER",
                    }

            # Update status field if provided
            if status_str is not None:
                if "Status" not in available_fields:
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text="Error: Status field not found in project",
                            )
                        ],
                        isError=True,
                    )

                status_field = available_fields["Status"]
                if status_str not in status_field["options"]:
                    available_options = list(status_field["options"].keys())
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text=f"Error: Status option '{status_str}' not found. Available options: {', '.join(available_options)}",
                            )
                        ],
                        isError=True,
                    )

                # Update status field
                status_mutation = query_builder.update_project_item_field_value(
                    project_id=project_id,
                    item_id=task_item_id,
                    field_id=status_field["id"],
                    single_select_option_id=status_field["options"][status_str],
                )

                logger.info(
                    f"Updating status to '{status_str}' for task: {task_item_id}"
                )
                status_response = await client.mutate(status_mutation)

                if "errors" in status_response:
                    error_messages = [
                        error["message"] for error in status_response["errors"]
                    ]
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text=f"Error updating status: {'; '.join(error_messages)}",
                            )
                        ],
                        isError=True,
                    )

                updated_fields.append("status")

            # Update priority field if provided
            if priority_str is not None:
                if "Priority" not in available_fields:
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text="Error: Priority field not found in project",
                            )
                        ],
                        isError=True,
                    )

                priority_field = available_fields["Priority"]
                if priority_str not in priority_field["options"]:
                    available_options = list(priority_field["options"].keys())
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text=f"Error: Priority option '{priority_str}' not found. Available options: {', '.join(available_options)}",
                            )
                        ],
                        isError=True,
                    )

                # Update priority field
                priority_mutation = query_builder.update_project_item_field_value(
                    project_id=project_id,
                    item_id=task_item_id,
                    field_id=priority_field["id"],
                    single_select_option_id=priority_field["options"][priority_str],
                )

                logger.info(
                    f"Updating priority to '{priority_str}' for task: {task_item_id}"
                )
                priority_response = await client.mutate(priority_mutation)

                if "errors" in priority_response:
                    error_messages = [
                        error["message"] for error in priority_response["errors"]
                    ]
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text=f"Error updating priority: {'; '.join(error_messages)}",
                            )
                        ],
                        isError=True,
                    )

                updated_fields.append("priority")

            # Update estimated hours field if provided
            if estimated_hours is not None:
                if "Estimated Hours" not in available_fields:
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text="Error: Estimated Hours field not found in project",
                            )
                        ],
                        isError=True,
                    )

                est_hours_field = available_fields["Estimated Hours"]

                # Update estimated hours field
                est_hours_mutation = (
                    query_builder.update_project_item_number_field_value(
                        project_id=project_id,
                        item_id=task_item_id,
                        field_id=est_hours_field["id"],
                        number_value=estimated_hours,
                    )
                )

                logger.info(
                    f"Updating estimated hours to '{estimated_hours}' for task: {task_item_id}"
                )
                est_hours_response = await client.mutate(est_hours_mutation)

                if "errors" in est_hours_response:
                    error_messages = [
                        error["message"] for error in est_hours_response["errors"]
                    ]
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text=f"Error updating estimated hours: {'; '.join(error_messages)}",
                            )
                        ],
                        isError=True,
                    )

                updated_fields.append("estimated_hours")

            # Update actual hours field if provided
            if actual_hours is not None:
                if "Actual Hours" not in available_fields:
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text="Error: Actual Hours field not found in project",
                            )
                        ],
                        isError=True,
                    )

                act_hours_field = available_fields["Actual Hours"]

                # Update actual hours field
                act_hours_mutation = (
                    query_builder.update_project_item_number_field_value(
                        project_id=project_id,
                        item_id=task_item_id,
                        field_id=act_hours_field["id"],
                        number_value=actual_hours,
                    )
                )

                logger.info(
                    f"Updating actual hours to '{actual_hours}' for task: {task_item_id}"
                )
                act_hours_response = await client.mutate(act_hours_mutation)

                if "errors" in act_hours_response:
                    error_messages = [
                        error["message"] for error in act_hours_response["errors"]
                    ]
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text=f"Error updating actual hours: {'; '.join(error_messages)}",
                            )
                        ],
                        isError=True,
                    )

                updated_fields.append("actual_hours")

        # Build success response
        updates_text = ", ".join(updated_fields)
        response_text = f"""✅ Task successfully updated!

**Updated Task:** {task_item_id}
**Fields Updated:** {updates_text}

The task has been updated successfully."""

        if title is not None:
            response_text += f"\n**New Title:** {title}"

        if description is not None:
            preview = (
                description[:100] + "..." if len(description) > 100 else description
            )
            response_text += f"\n**Description Updated:** {preview}"

        logger.info(f"Successfully updated task: {task_item_id}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=response_text,
                )
            ],
            isError=False,
        )

    except Exception as e:
        logger.error(f"Unexpected error in update_task_handler: {e}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error: An unexpected error occurred while updating task: {str(e)}",
                )
            ],
            isError=True,
        )


def _build_delete_task_mutation(project_id: str, task_item_id: str) -> str:
    """
    Build GraphQL mutation to delete a Task (project item) from a project.

    Args:
        project_id: GitHub project ID
        task_item_id: GitHub project item ID

    Returns:
        GraphQL mutation string
    """
    query_builder = ProjectQueryBuilder()

    # Escape strings for GraphQL
    escaped_project_id = query_builder._escape_string(project_id)
    escaped_item_id = query_builder._escape_string(task_item_id)

    mutation = f"""
mutation {{
  deleteProjectV2Item(input: {{
    projectId: {escaped_project_id}
    itemId: {escaped_item_id}
  }}) {{
    deletedItemId
  }}
}}
""".strip()

    return mutation


async def delete_task_handler(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle delete_task tool calls.

    Deletes a Task (project item) from a GitHub project.
    This operation requires explicit confirmation to prevent accidental deletions.

    Args:
        arguments: Tool call arguments containing:
            - project_id (required): GitHub project ID
            - task_item_id (required): GitHub project item ID
            - confirm (required): Boolean confirmation for deletion

    Returns:
        CallToolResult with operation results
    """
    try:
        # Validate required parameters
        project_id = arguments.get("project_id", "").strip()
        task_item_id = arguments.get("task_item_id", "").strip()
        confirm = arguments.get("confirm", False)

        if not project_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: project_id is required to delete task",
                    )
                ],
                isError=True,
            )

        if not task_item_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: task_item_id is required to delete task",
                    )
                ],
                isError=True,
            )

        if not confirm:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: You must explicitly confirm task deletion by setting 'confirm' to true. This action cannot be undone.",
                    )
                ],
                isError=True,
            )

        # Check if GitHub client is initialized
        github_client = get_github_client()
        if github_client is None:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: GitHub client not initialized. Please check your authentication.",
                    )
                ],
                isError=True,
            )

        # Build and execute mutation
        mutation = _build_delete_task_mutation(project_id, task_item_id)

        logger.info(f"Deleting task with project item ID: {task_item_id}")
        response = await github_client.mutate(mutation)

        # Debug: log the full response
        logger.debug(f"GitHub API response: {response}")

        # Check for GraphQL errors
        if "errors" in response:
            error_messages = [
                error.get("message", "Unknown error") for error in response["errors"]
            ]
            logger.error(f"GraphQL errors: {error_messages}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error deleting task: GraphQL errors: {'; '.join(error_messages)}",
                    )
                ],
                isError=True,
            )

        # Extract deletion result
        # Handle response structure - check if data is nested under "data" key or direct
        if "data" in response:
            data = response["data"]
        else:
            data = response

        delete_result = data.get("deleteProjectV2Item", {})
        deleted_item_id = delete_result.get("deletedItemId")

        logger.debug(f"Response data: {data}")
        logger.debug(f"Delete result: {delete_result}")
        logger.debug(f"Deleted item ID: {deleted_item_id}")

        if not deleted_item_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: Failed to delete task - no deleted item ID returned from GitHub API. Response: {response}",
                    )
                ],
                isError=True,
            )

        # Build success response
        result_text = f"""✅ Task successfully deleted from project!

**Deletion Details:**
- **Deleted Item ID:** {deleted_item_id}
- **Original Item ID:** {task_item_id}

The task has been permanently removed from the project. This action cannot be undone."""

        logger.info(f"Task with ID '{task_item_id}' successfully deleted")

        return CallToolResult(
            content=[TextContent(type="text", text=result_text)],
            isError=False,
        )

    except Exception as e:
        logger.error(f"Error deleting task: {e}", exc_info=True)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error deleting task: {str(e)}")],
            isError=True,
        )


# Tool definitions
CREATE_TASK_TOOL = Tool(
    name="create_task",
    description="Create a new task and associate it with a parent PRD in a GitHub project. Tasks represent specific work items that need to be completed as part of a larger Product Requirements Document (PRD).",
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "GitHub Projects v2 project ID (e.g., 'PVT_kwDOA...')",
            },
            "parent_prd_id": {
                "type": "string",
                "description": "ID of the parent PRD this task belongs to (e.g., 'PVTI_kwDOA...')",
            },
            "title": {
                "type": "string",
                "description": "Task title/summary",
            },
            "description": {
                "type": "string",
                "description": "Optional detailed description of the task",
                "default": "",
            },
            "priority": {
                "type": "string",
                "description": "Task priority level",
                "enum": ["Low", "Medium", "High", "Critical"],
                "default": "Medium",
            },
            "estimated_hours": {
                "type": "integer",
                "description": "Optional estimated hours needed to complete the task",
                "minimum": 1,
            },
        },
        "required": ["project_id", "parent_prd_id", "title"],
    },
)

LIST_TASKS_TOOL = Tool(
    name="list_tasks",
    description="List tasks in a GitHub project with optional filtering by parent PRD. Supports pagination and returns detailed information about each task including status, priority, parent PRD, and metadata.",
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "GitHub Projects v2 project ID (e.g., 'PVT_kwDOA...')",
            },
            "parent_prd_id": {
                "type": "string",
                "description": "Optional parent PRD ID to filter tasks (e.g., 'PVTI_kwDOA...')",
            },
            "first": {
                "type": "integer",
                "description": "Number of tasks to fetch (pagination, default: 25, max: 100)",
                "minimum": 1,
                "maximum": 100,
                "default": 25,
            },
            "after": {
                "type": "string",
                "description": "Cursor for pagination to fetch tasks after this cursor",
            },
        },
        "required": ["project_id"],
    },
)

UPDATE_TASK_TOOL = Tool(
    name="update_task",
    description="Update a Task's content (title, description) and/or project field values (status, priority, estimated_hours, actual_hours)",
    inputSchema={
        "type": "object",
        "properties": {
            "task_item_id": {
                "type": "string",
                "description": "GitHub project item ID of the task to update",
            },
            "title": {
                "type": "string",
                "description": "New task title",
            },
            "description": {
                "type": "string",
                "description": "New task description",
            },
            "status": {
                "type": "string",
                "description": "New task status",
                "enum": [
                    "Todo",
                    "In Progress",
                    "Blocked",
                    "Review",
                    "Done",
                    "Cancelled",
                ],
            },
            "priority": {
                "type": "string",
                "description": "New task priority",
                "enum": ["Low", "Medium", "High", "Critical"],
            },
            "estimated_hours": {
                "type": "integer",
                "description": "New estimated hours for task completion",
                "minimum": 1,
            },
            "actual_hours": {
                "type": "integer",
                "description": "New actual hours spent on task",
                "minimum": 1,
            },
        },
        "required": ["task_item_id"],
    },
)

DELETE_TASK_TOOL = Tool(
    name="delete_task",
    description="Delete a task from a GitHub project. This action is permanent and cannot be undone.",
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "GitHub Projects v2 project ID (e.g., 'PVT_kwDOA...')",
            },
            "task_item_id": {
                "type": "string",
                "description": "GitHub project item ID of the task to delete",
            },
            "confirm": {
                "type": "boolean",
                "description": "Confirmation for deletion - must be true to proceed",
            },
        },
        "required": ["project_id", "task_item_id", "confirm"],
    },
)

# Export lists for registration
TASK_TOOLS: List[Tool] = [
    CREATE_TASK_TOOL,
    LIST_TASKS_TOOL,
    UPDATE_TASK_TOOL,
    DELETE_TASK_TOOL,
]

TASK_TOOL_HANDLERS: Dict[str, Any] = {
    "create_task": create_task_handler,
    "list_tasks": list_tasks_handler,
    "update_task": update_task_handler,
    "delete_task": delete_task_handler,
}

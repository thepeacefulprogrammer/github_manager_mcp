"""
PRD (Product Requirements Document) handlers for GitHub Projects v2.

This module provides MCP tool handlers for managing Product Requirements Documents
as items within GitHub Projects v2, including creation, status updates, and
comprehensive PRD lifecycle management.
"""

import logging
from typing import Any, Dict, List, Optional

from mcp.types import CallToolResult, TextContent, Tool

from github_project_manager_mcp.github_client import GitHubClient
from github_project_manager_mcp.models.prd import PRD, PRDPriority, PRDStatus
from github_project_manager_mcp.utils.query_builder import ProjectQueryBuilder
from github_project_manager_mcp.utils.validation import PRDValidator, ValidationError

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
    logger.info("GitHub client initialized for PRD handlers")


def _build_prd_description_body(
    description: str,
    acceptance_criteria: Optional[str] = None,
    technical_requirements: Optional[str] = None,
    business_value: Optional[str] = None,
) -> str:
    """
    Build a comprehensive description body for PRD with structured sections.

    Args:
        description: Base description
        acceptance_criteria: Acceptance criteria section
        technical_requirements: Technical requirements section
        business_value: Business value section

    Returns:
        Formatted description with sections
    """
    body = description

    if acceptance_criteria:
        body += f"\n\n**Acceptance Criteria:**\n{acceptance_criteria}"

    if technical_requirements:
        body += f"\n\n**Technical Requirements:**\n{technical_requirements}"

    if business_value:
        body += f"\n\n**Business Value:**\n{business_value}"

    return body


def _build_add_prd_mutation(
    project_id: str,
    title: str,
    body: str,
    status: PRDStatus = PRDStatus.BACKLOG,
    priority: PRDPriority = PRDPriority.MEDIUM,
) -> str:
    """
    Build GraphQL mutation to add a PRD (draft issue) to a project.

    Args:
        project_id: GitHub project ID
        title: PRD title
        body: PRD description body
        status: PRD status
        priority: PRD priority

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


async def add_prd_to_project_handler(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle add_prd_to_project tool calls.

    Adds a new Product Requirements Document as a draft issue to a GitHub project.
    Supports comprehensive PRD fields including acceptance criteria, technical
    requirements, business value, status, and priority.

    Args:
        arguments: Tool call arguments containing:
            - project_id (required): GitHub project ID
            - title (required): PRD title
            - description (optional): PRD description
            - acceptance_criteria (optional): Acceptance criteria
            - technical_requirements (optional): Technical requirements
            - business_value (optional): Business value description
            - status (optional): PRD status (defaults to "Backlog")
            - priority (optional): PRD priority (defaults to "Medium")

    Returns:
        CallToolResult with operation results
    """
    try:
        # Comprehensive validation using PRDValidator
        validator = PRDValidator()

        # Validate project_id separately
        project_id = arguments.get("project_id", "").strip()
        if not project_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: project_id is required to add PRD to project",
                    )
                ],
                isError=True,
            )

        # Validate PRD creation data
        prd_data = {
            "title": arguments.get("title", "").strip(),
            "description": arguments.get("description", ""),
            "acceptance_criteria": arguments.get("acceptance_criteria"),
            "business_value": arguments.get("business_value"),
            "technical_requirements": arguments.get("technical_requirements"),
            "priority": arguments.get("priority", "Medium"),
            "status": arguments.get("status", "Backlog"),
        }

        validation_result = validator.validate_prd_creation(prd_data)
        if not validation_result.is_valid:
            error_message = f"Validation failed: {', '.join(validation_result.errors)}"
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: {error_message}",
                    )
                ],
                isError=True,
            )

        # Extract validated parameters
        title = prd_data["title"]
        description = prd_data["description"]
        acceptance_criteria = prd_data["acceptance_criteria"]
        technical_requirements = prd_data["technical_requirements"]
        business_value = prd_data["business_value"]

        # Parse validated status and priority
        status_str = prd_data["status"]
        priority_str = prd_data["priority"]

        try:
            status = PRDStatus(status_str)
        except ValueError:
            valid_statuses = [s.value for s in PRDStatus]
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: Invalid status '{status_str}'. Valid values: {', '.join(valid_statuses)}",
                    )
                ],
                isError=True,
            )

        try:
            priority = PRDPriority(priority_str)
        except ValueError:
            valid_priorities = [p.value for p in PRDPriority]
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

        # Build comprehensive description body
        body = _build_prd_description_body(
            description=description,
            acceptance_criteria=acceptance_criteria,
            technical_requirements=technical_requirements,
            business_value=business_value,
        )

        # Build and execute mutation
        mutation = _build_add_prd_mutation(
            project_id=project_id,
            title=title,
            body=body,
            status=status,
            priority=priority,
        )

        logger.info(f"Adding PRD '{title}' to project {project_id}")
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
                        text=f"Error adding PRD to project: GraphQL errors: {'; '.join(error_messages)}",
                    )
                ],
                isError=True,
            )

        # Extract project item data
        # Handle response structure - check if data is nested under "data" key or direct
        if "data" in response:
            data = response["data"]
        else:
            data = response

        add_result = data.get("addProjectV2DraftIssue", {})
        project_item_data = add_result.get("projectItem")

        logger.debug(f"Response data: {data}")
        logger.debug(f"Add result: {add_result}")
        logger.debug(f"Project item data: {project_item_data}")

        # Check if project item was created successfully
        if not project_item_data or not project_item_data.get("id"):
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: Failed to create PRD - no project item returned from GitHub API. Response: {response}",
                    )
                ],
                isError=True,
            )

        # Extract draft issue content
        content = project_item_data.get("content", {})
        prd_title = content.get("title", title)
        prd_description = content.get("body", body)
        prd_id = project_item_data.get("id")
        created_at = project_item_data.get("createdAt") or content.get("createdAt")

        # TODO: Set custom field values for status and priority
        # This would require additional mutations to update project fields
        # For now, we'll note the intended values in the response

        # Build success response
        result_text = f"""✅ PRD successfully added to project!

**PRD Details:**
- **ID:** {prd_id}
- **Title:** {prd_title}
- **Status:** {status.value} (to be set via project fields)
- **Priority:** {priority.value} (to be set via project fields)
- **Created:** {created_at or "Unknown"}

**Description:**
{prd_description if prd_description else "No description provided"}"""

        if acceptance_criteria:
            result_text += f"\n\n**Acceptance Criteria:**\n{acceptance_criteria}"

        if technical_requirements:
            result_text += f"\n\n**Technical Requirements:**\n{technical_requirements}"

        if business_value:
            result_text += f"\n\n**Business Value:**\n{business_value}"

        logger.info(f"PRD '{prd_title}' successfully added with ID: {prd_id}")

        return CallToolResult(
            content=[TextContent(type="text", text=result_text)],
            isError=False,
        )

    except Exception as e:
        logger.error(f"Error adding PRD to project: {e}", exc_info=True)
        return CallToolResult(
            content=[
                TextContent(type="text", text=f"Error adding PRD to project: {str(e)}")
            ],
            isError=True,
        )


def _build_delete_prd_mutation(project_id: str, project_item_id: str) -> str:
    """
    Build GraphQL mutation to delete a PRD (project item) from a project.

    Args:
        project_id: GitHub project ID
        project_item_id: GitHub project item ID

    Returns:
        GraphQL mutation string
    """
    query_builder = ProjectQueryBuilder()

    # Escape strings for GraphQL
    escaped_project_id = query_builder._escape_string(project_id)
    escaped_item_id = query_builder._escape_string(project_item_id)

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


async def delete_prd_from_project_handler(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle delete_prd_from_project tool calls.

    Deletes a Product Requirements Document (project item) from a GitHub project.
    This operation requires explicit confirmation to prevent accidental deletions.

    Args:
        arguments: Tool call arguments containing:
            - project_id (required): GitHub project ID
            - project_item_id (required): GitHub project item ID
            - confirm (required): Boolean confirmation for deletion

    Returns:
        CallToolResult with operation results
    """
    try:
        # Validate required parameters
        project_id = arguments.get("project_id", "").strip()
        project_item_id = arguments.get("project_item_id", "").strip()
        confirm = arguments.get("confirm", False)

        if not project_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: project_id is required to delete PRD from project",
                    )
                ],
                isError=True,
            )

        if not project_item_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: project_item_id is required to delete PRD from project",
                    )
                ],
                isError=True,
            )

        if not confirm:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: You must explicitly confirm PRD deletion by setting 'confirm' to true. This action cannot be undone.",
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
        mutation = _build_delete_prd_mutation(project_id, project_item_id)

        logger.info(f"Deleting PRD with project item ID: {project_item_id}")
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
                        text=f"Error deleting PRD from project: GraphQL errors: {'; '.join(error_messages)}",
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
                        text=f"Error: Failed to delete PRD - no deleted item ID returned from GitHub API. Response: {response}",
                    )
                ],
                isError=True,
            )

        # Build success response
        result_text = f"""✅ PRD successfully deleted from project!

**Deletion Details:**
- **Deleted Item ID:** {deleted_item_id}
- **Original Item ID:** {project_item_id}

The PRD has been permanently removed from the project. This action cannot be undone."""

        logger.info(f"PRD with ID '{project_item_id}' successfully deleted")

        return CallToolResult(
            content=[TextContent(type="text", text=result_text)],
            isError=False,
        )

    except Exception as e:
        logger.error(f"Error deleting PRD from project: {e}", exc_info=True)
        return CallToolResult(
            content=[
                TextContent(
                    type="text", text=f"Error deleting PRD from project: {str(e)}"
                )
            ],
            isError=True,
        )


async def list_prds_in_project_handler(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle list_prds_in_project tool calls.

    Lists all Product Requirements Documents (PRDs) within a GitHub project.
    Supports pagination and returns detailed information about each PRD including
    status, priority, assignees, and creation/update timestamps.

    Args:
        arguments: Tool call arguments containing:
            - project_id (required): GitHub project ID
            - first (optional): Number of PRDs to fetch (pagination, default: 25)
            - after (optional): Cursor for pagination

    Returns:
        CallToolResult with PRD list and pagination info
    """
    try:
        # Validate required parameters
        project_id = arguments.get("project_id", "").strip()

        if not project_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: project_id is required to list PRDs in project",
                    )
                ],
                isError=True,
            )

        # Extract optional pagination parameters
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
        query = query_builder.list_prds_in_project(
            project_id=project_id, first=first, after=after
        )

        logger.info(f"Listing PRDs in project: {project_id}")
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
                        text=f"Error listing PRDs: GraphQL errors: {'; '.join(error_messages)}",
                    )
                ],
                isError=True,
            )

        # Extract project data
        # Handle response structure - check if data is nested under "data" key or direct
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

        # Filter for PRDs (draft issues and issues) and format response
        prds = []
        for item in items:
            content = item.get("content")
            if not content:
                continue

            # Extract item metadata
            item_id = item.get("id", "Unknown")
            item_created_at = item.get("createdAt", "Unknown")
            item_updated_at = item.get("updatedAt", "Unknown")

            # Extract field values (status, priority, etc.)
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

            # Handle both DraftIssue and Issue types
            if "title" in content:
                title = content.get("title", "Untitled PRD")
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

                # Determine PRD type and additional info
                prd_type = "Draft Issue"
                additional_info = {}

                if "number" in content:  # This is a regular Issue
                    prd_type = "Issue"
                    additional_info["number"] = content.get("number")
                    additional_info["state"] = content.get("state", "OPEN")
                    repo_info = content.get("repository", {})
                    if repo_info:
                        repo_name = repo_info.get("name", "")
                        repo_owner = repo_info.get("owner", {}).get("login", "")
                        if repo_name and repo_owner:
                            additional_info["repository"] = f"{repo_owner}/{repo_name}"

                prds.append(
                    {
                        "item_id": item_id,
                        "title": title,
                        "body": body,
                        "type": prd_type,
                        "created_at": created_at,
                        "updated_at": updated_at,
                        "assignees": assignees,
                        "field_values": field_values,
                        "additional_info": additional_info,
                    }
                )

        # Build response text
        result_lines = [
            f"📋 **PRDs in Project: {project_title}**",
            f"**Project ID:** {project_id}",
            f"**Total Items:** {total_count}",
            f"**PRDs Found:** {len(prds)}",
            "",
        ]

        if not prds:
            result_lines.append("No PRDs found in this project.")
        else:
            for i, prd in enumerate(prds, 1):
                result_lines.append(f"**{i}. {prd['title']}**")
                result_lines.append(f"   - **Type:** {prd['type']}")
                result_lines.append(f"   - **Item ID:** {prd['item_id']}")

                # Add additional info for regular issues
                if prd["additional_info"]:
                    for key, value in prd["additional_info"].items():
                        result_lines.append(f"   - **{key.title()}:** {value}")

                # Add assignees if present
                if prd["assignees"]:
                    result_lines.append(
                        f"   - **Assignees:** {', '.join(prd['assignees'])}"
                    )

                # Add field values (status, priority, etc.)
                if prd["field_values"]:
                    for field_name, field_value in prd["field_values"].items():
                        result_lines.append(f"   - **{field_name}:** {field_value}")

                result_lines.append(f"   - **Created:** {prd['created_at']}")
                result_lines.append(f"   - **Updated:** {prd['updated_at']}")

                # Add body preview if present
                if prd["body"]:
                    body_preview = prd["body"][:100]
                    if len(prd["body"]) > 100:
                        body_preview += "..."
                    result_lines.append(f"   - **Description:** {body_preview}")

                result_lines.append("")  # Empty line between PRDs

        # Add pagination info
        if page_info:
            has_next = page_info.get("hasNextPage", False)
            has_prev = page_info.get("hasPreviousPage", False)
            start_cursor = page_info.get("startCursor")
            end_cursor = page_info.get("endCursor")

            if has_next or has_prev:
                result_lines.append("**Pagination Info:**")
                if has_prev:
                    result_lines.append(f"   - Has previous page")
                if has_next:
                    result_lines.append(
                        f"   - Has next page (use after: '{end_cursor}')"
                    )
                result_lines.append("")

        result_text = "\n".join(result_lines)

        logger.info(f"Found {len(prds)} PRDs in project '{project_id}'")

        return CallToolResult(
            content=[TextContent(type="text", text=result_text)],
            isError=False,
        )

    except Exception as e:
        logger.error(f"Error listing PRDs in project: {e}", exc_info=True)
        return CallToolResult(
            content=[
                TextContent(
                    type="text", text=f"Error listing PRDs in project: {str(e)}"
                )
            ],
            isError=True,
        )


async def update_prd_handler(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle update_prd tool calls.

    Updates a Product Requirements Document (PRD) in a GitHub project. This handler
    supports updating title, body content, and assignee assignments. The update
    process involves two steps:
    1. Query the project item to get the draft issue content ID
    2. Update the draft issue using the content ID

    Args:
        arguments: Tool call arguments containing:
            - prd_item_id (required): GitHub project item ID (PVTI_...)
            - title (optional): New title for the PRD
            - body (optional): New body content for the PRD
            - assignee_ids (optional): List of user IDs to assign to the PRD

    Returns:
        CallToolResult with updated PRD details or error information
    """
    try:
        # Validate required parameters
        prd_item_id = arguments.get("prd_item_id", "").strip()
        if not prd_item_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: prd_item_id is required to update PRD",
                    )
                ],
                isError=True,
            )

        # Comprehensive validation using PRDValidator
        validator = PRDValidator()

        # Prepare update data for validation
        update_data = {}
        if arguments.get("title") is not None:
            update_data["title"] = arguments.get("title")
        if arguments.get("body") is not None:
            update_data["description"] = arguments.get(
                "body"
            )  # Map body to description for validation
        if arguments.get("assignee_ids") is not None:
            update_data["assignee_ids"] = arguments.get("assignee_ids")

        # Validate update data
        validation_result = validator.validate_prd_update(update_data)
        if not validation_result.is_valid:
            error_message = f"Validation failed: {', '.join(validation_result.errors)}"
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: {error_message}",
                    )
                ],
                isError=True,
            )

        # Extract validated parameters
        title = arguments.get("title")
        body = arguments.get("body")
        assignee_ids = arguments.get("assignee_ids")

        # Validate assignee_ids if provided
        if assignee_ids is not None:
            if not isinstance(assignee_ids, list):
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text="Error: assignee_ids must be a list of user IDs",
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

        # Step 1: Get the draft issue content ID from the project item
        query_builder = ProjectQueryBuilder()
        content_id_query = query_builder.get_prd_content_id(prd_item_id)

        logger.info(
            f"Querying for draft issue content ID for project item: {prd_item_id}"
        )
        content_response = await github_client.query(content_id_query)

        # Debug: log the content ID response
        logger.debug(f"Content ID query response: {content_response}")

        # Check for GraphQL errors
        if "errors" in content_response:
            error_messages = [
                error.get("message", "Unknown error")
                for error in content_response["errors"]
            ]
            logger.error(f"GraphQL errors in content ID query: {error_messages}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error getting PRD content ID: GraphQL errors: {'; '.join(error_messages)}",
                    )
                ],
                isError=True,
            )

        # Extract draft issue content ID
        if "data" in content_response:
            data = content_response["data"]
        else:
            data = content_response

        node_data = data.get("node")
        if not node_data:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: Could not find project item with ID {prd_item_id}",
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
                        text=f"Error: Project item {prd_item_id} does not have content (may not be a draft issue)",
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
                        text=f"Error: Could not extract draft issue ID from project item {prd_item_id}",
                    )
                ],
                isError=True,
            )

        logger.info(f"Found draft issue content ID: {draft_issue_id}")

        # Step 2: Build and execute the update mutation using the draft issue content ID
        mutation = query_builder.update_prd(
            prd_item_id=draft_issue_id,  # Use the content ID, not the project item ID
            title=title,
            body=body,
            assignee_ids=assignee_ids,
        )

        logger.info(
            f"Updating draft issue '{draft_issue_id}' (from project item '{prd_item_id}')"
        )
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
                        text=f"Error updating PRD: GraphQL errors: {'; '.join(error_messages)}",
                    )
                ],
                isError=True,
            )

        # Extract update result
        if "data" in response:
            data = response["data"]
        else:
            data = response

        update_result = data.get("updateProjectV2DraftIssue", {})
        draft_issue_data = update_result.get("draftIssue")

        if not draft_issue_data:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: No draft issue data returned from update. Response: {response}",
                    )
                ],
                isError=True,
            )

        # Extract updated PRD information
        updated_title = draft_issue_data.get("title", "")
        updated_body = draft_issue_data.get("body", "")
        updated_id = draft_issue_data.get("id", "")
        created_at = draft_issue_data.get("createdAt", "")
        updated_at = draft_issue_data.get("updatedAt", "")

        # Extract assignee information
        assignees_data = draft_issue_data.get("assignees", {})
        assignee_count = assignees_data.get("totalCount", 0)
        assignee_nodes = assignees_data.get("nodes", [])
        assignee_info = []
        for assignee in assignee_nodes:
            login = assignee.get("login", "")
            name = assignee.get("name", "") or login
            assignee_info.append(f"{name} (@{login})")

        # Extract project information
        project_items = draft_issue_data.get("projectV2Items", {})
        project_nodes = project_items.get("nodes", [])
        project_info = []
        for project_item in project_nodes:
            project = project_item.get("project", {})
            project_title = project.get("title", "Unknown Project")
            project_id = project.get("id", "")
            project_info.append(f"{project_title} ({project_id})")

        # Format response
        updated_fields = []
        if title is not None:
            updated_fields.append("title")
        if body is not None:
            updated_fields.append("body")
        if assignee_ids is not None:
            updated_fields.append("assignees")

        response_text = f"""✅ PRD successfully updated!

**Updated PRD Details:**
- **ID:** {updated_id}
- **Title:** {updated_title}
- **Created:** {created_at}
- **Updated:** {updated_at}

**Updated Fields:** {', '.join(updated_fields)}

**Assignees:** {assignee_count} assigned
{chr(10).join([f"  - {assignee}" for assignee in assignee_info]) if assignee_info else "  - None"}

**Associated Projects:**
{chr(10).join([f"  - {project}" for project in project_info]) if project_info else "  - None"}"""

        if body is not None and len(updated_body) > 100:
            response_text += f"""

**Body Preview:**
{updated_body[:100]}..."""
        elif body is not None:
            response_text += f"""

**Body:**
{updated_body}"""

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
        logger.error(f"Unexpected error in update_prd_handler: {e}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error: An unexpected error occurred while updating PRD: {str(e)}",
                )
            ],
            isError=True,
        )


async def update_prd_status_handler(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle update_prd_status tool calls.

    Updates the status and/or priority fields of a Product Requirements Document
    in a GitHub project using the Projects v2 field value update API.

    Args:
        arguments: Tool call arguments containing:
            - prd_item_id (required): GitHub project item ID
            - status (optional): New PRD status value
            - priority (optional): New PRD priority value

    Returns:
        CallToolResult with operation results
    """
    try:
        # Validate required parameters
        prd_item_id = arguments.get("prd_item_id", "").strip()

        if not prd_item_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: prd_item_id is required to update PRD status",
                    )
                ],
                isError=True,
            )

        # Extract optional update parameters
        status_str = arguments.get("status")
        priority_str = arguments.get("priority")

        # Validate that at least one update field is provided
        if status_str is None and priority_str is None:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: At least one update field (status or priority) must be provided",
                    )
                ],
                isError=True,
            )

        # Validate status if provided
        if status_str is not None:
            try:
                status = PRDStatus(status_str)
            except ValueError:
                valid_statuses = [s.value for s in PRDStatus]
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
                priority = PRDPriority(priority_str)
            except ValueError:
                valid_priorities = [p.value for p in PRDPriority]
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Error: Invalid priority '{priority_str}'. Valid values: {', '.join(valid_priorities)}",
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

        # Get project item details and field definitions
        query_builder = ProjectQueryBuilder()
        fields_query = query_builder.get_project_item_fields(prd_item_id)

        logger.info(f"Fetching project item fields for PRD: {prd_item_id}")
        fields_response = await client.query(fields_query)

        # Check for GraphQL errors
        if "errors" in fields_response:
            error_messages = [error["message"] for error in fields_response["errors"]]
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
                        text=f"Error: Project item not found: {prd_item_id}",
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
            field_options = {opt["name"]: opt["id"] for opt in field.get("options", [])}
            available_fields[field_name] = {
                "id": field_id,
                "options": field_options,
            }

        # Track successful updates
        updated_fields = []

        # Update status if provided
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
                item_id=prd_item_id,
                field_id=status_field["id"],
                single_select_option_id=status_field["options"][status_str],
            )

            logger.info(f"Updating status to '{status_str}' for PRD: {prd_item_id}")
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

            updated_fields.append(f"status to '{status_str}'")

        # Update priority if provided
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
                item_id=prd_item_id,
                field_id=priority_field["id"],
                single_select_option_id=priority_field["options"][priority_str],
            )

            logger.info(f"Updating priority to '{priority_str}' for PRD: {prd_item_id}")
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

            updated_fields.append(f"priority to '{priority_str}'")

        # Build success response
        updates_text = " and ".join(updated_fields)
        response_text = f"""✅ PRD field values successfully updated!

**Updated PRD:** {prd_item_id}
**Updates Applied:** {updates_text}
**Project:** {project_id}

The field values have been updated in the GitHub project."""

        logger.info(f"Successfully updated PRD field values: {prd_item_id}")
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
        logger.error(f"Unexpected error in update_prd_status_handler: {e}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error: An unexpected error occurred while updating PRD status: {str(e)}",
                )
            ],
            isError=True,
        )


async def complete_prd_handler(arguments: Dict[str, Any]) -> CallToolResult:
    """
    Handle complete_prd tool calls.

    Marks a PRD as complete by setting its status to "Done". This is a
    convenience method that provides a simple one-click completion for PRDs.
    The operation is idempotent - calling it on an already complete PRD
    will return a success message without making changes.

    Args:
        arguments: Tool call arguments containing:
            - prd_item_id (required): GitHub project item ID of the PRD

    Returns:
        CallToolResult with operation results
    """
    try:
        # Validate required parameters
        prd_item_id = arguments.get("prd_item_id", "").strip()

        if not prd_item_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: prd_item_id is required to complete PRD",
                    )
                ],
                isError=True,
            )

        client = get_github_client()
        if not client:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: GitHub client not initialized",
                    )
                ],
                isError=True,
            )

        # Use existing logic from update_prd_status_handler to get project item fields
        query_builder = ProjectQueryBuilder()
        escaped_item_id = query_builder._escape_string(prd_item_id)

        # Query to get project item fields and current status
        fields_query = f"""
query {{
  node(id: {escaped_item_id}) {{
    ... on ProjectV2Item {{
      id
      project {{
        id
        fields(first: 20) {{
          nodes {{
            ... on ProjectV2SingleSelectField {{
              id
              name
              dataType
              options {{
                id
                name
              }}
            }}
          }}
        }}
      }}
      fieldValues(first: 20) {{
        nodes {{
          ... on ProjectV2ItemFieldSingleSelectValue {{
            field {{
              ... on ProjectV2SingleSelectField {{
                name
              }}
            }}
            optionId
            name
          }}
        }}
      }}
    }}
  }}
}}
""".strip()

        logger.info(f"Fetching PRD status for completion: {prd_item_id}")
        fields_response = await client.query(fields_query)

        if "errors" in fields_response:
            error_messages = [error["message"] for error in fields_response["errors"]]
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Failed to fetch PRD status: {'; '.join(error_messages)}",
                    )
                ],
                isError=True,
            )

        if not fields_response.get("node"):
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: PRD not found",
                    )
                ],
                isError=True,
            )

        project_item = fields_response["node"]
        project = project_item.get("project", {})
        project_fields = project.get("fields", {}).get("nodes", [])
        current_field_values = project_item.get("fieldValues", {}).get("nodes", [])

        # Find Status field
        status_field = None
        for field in project_fields:
            if (
                field.get("name") == "Status"
                and field.get("dataType") == "SINGLE_SELECT"
            ):
                status_field = field
                break

        if not status_field:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: Status field not found in project",
                    )
                ],
                isError=True,
            )

        # Get current status
        current_status = None
        for field_value in current_field_values:
            if field_value.get("field", {}).get("name") == "Status":
                current_status = field_value.get("name")
                break

        # Check if already complete
        if current_status == "Done":
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"✅ PRD is already complete!\n\n**Status:** Done",
                    )
                ],
                isError=False,
            )

        # Find the "Done" option ID
        done_option_id = None
        for option in status_field.get("options", []):
            if option.get("name") == "Done":
                done_option_id = option.get("id")
                break

        if not done_option_id:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: 'Done' status option not found in project",
                    )
                ],
                isError=True,
            )

        # Build update mutation to set status to "Done"
        status_mutation = f"""
mutation {{
  updateProjectV2ItemFieldValue(input: {{
    projectId: {query_builder._escape_string(project["id"])}
    itemId: {escaped_item_id}
    fieldId: {query_builder._escape_string(status_field["id"])}
    value: {{
      singleSelectOptionId: {query_builder._escape_string(done_option_id)}
    }}
  }}) {{
    projectV2Item {{
      id
      fieldValues(first: 20) {{
        nodes {{
          ... on ProjectV2ItemFieldSingleSelectValue {{
            field {{
              ... on ProjectV2SingleSelectField {{
                name
              }}
            }}
            optionId
            name
          }}
        }}
      }}
    }}
  }}
}}
""".strip()

        logger.info(f"Completing PRD (setting status to 'Done'): {prd_item_id}")

        try:
            status_response = await client.mutate(status_mutation)
        except Exception as e:
            logger.error(f"GraphQL mutation error in complete_prd_handler: {e}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Failed to complete PRD: {str(e)}",
                    )
                ],
                isError=True,
            )

        if not status_response:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="No response data received from completion operation",
                    )
                ],
                isError=True,
            )

        if "errors" in status_response:
            error_messages = [error["message"] for error in status_response["errors"]]
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Failed to complete PRD: {'; '.join(error_messages)}",
                    )
                ],
                isError=True,
            )

        # Verify successful completion
        update_data = status_response.get("updateProjectV2ItemFieldValue")
        if not update_data:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Invalid response format from completion operation",
                    )
                ],
                isError=True,
            )

        # Success response
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text="✅ PRD completed successfully!\n\n**Status:** Done",
                )
            ],
            isError=False,
        )

    except Exception as e:
        logger.error(f"Unexpected error in complete_prd_handler: {e}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Failed to fetch PRD status: {str(e)}",
                )
            ],
            isError=True,
        )


# Define MCP tools for PRD management
PRD_TOOLS = [
    Tool(
        name="add_prd_to_project",
        description="Add a new Product Requirements Document (PRD) to a GitHub project as a draft issue with comprehensive metadata including acceptance criteria, technical requirements, and business value",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "GitHub project ID (e.g., 'PVT_kwDOBQfyVc0FoQ')",
                },
                "title": {
                    "type": "string",
                    "description": "PRD title - should be clear and descriptive",
                },
                "description": {
                    "type": "string",
                    "description": "PRD description - detailed explanation of the feature or requirement",
                },
                "acceptance_criteria": {
                    "type": "string",
                    "description": "Acceptance criteria - specific conditions that must be met for completion",
                },
                "technical_requirements": {
                    "type": "string",
                    "description": "Technical requirements - technologies, architecture, and implementation details",
                },
                "business_value": {
                    "type": "string",
                    "description": "Business value - expected impact, metrics, and value proposition",
                },
                "status": {
                    "type": "string",
                    "description": "PRD status",
                    "enum": [
                        "Backlog",
                        "This Sprint",
                        "Up Next",
                        "In Progress",
                        "Done",
                        "Cancelled",
                    ],
                    "default": "Backlog",
                },
                "priority": {
                    "type": "string",
                    "description": "PRD priority level",
                    "enum": ["Low", "Medium", "High", "Critical"],
                    "default": "Medium",
                },
            },
            "required": ["project_id", "title"],
            "additionalProperties": False,
        },
    ),
    Tool(
        name="delete_prd_from_project",
        description="Delete a Product Requirements Document (PRD) from a GitHub project. This action is permanent and cannot be undone.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "GitHub project ID (e.g., 'PVT_kwDOBQfyVc0FoQ') - the project containing the PRD",
                },
                "project_item_id": {
                    "type": "string",
                    "description": "GitHub project item ID (e.g., 'PVTI_kwDOBQfyVc0FoQ') - this is the ID of the PRD item to delete",
                },
                "confirm": {
                    "type": "boolean",
                    "description": "Confirmation that you want to delete the PRD (must be true to proceed)",
                },
            },
            "required": ["project_id", "project_item_id", "confirm"],
            "additionalProperties": False,
        },
    ),
    Tool(
        name="list_prds_in_project",
        description="List all Product Requirements Documents (PRDs) within a GitHub project with filtering and pagination support",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "GitHub project ID (e.g., 'PVT_kwDOBQfyVc0FoQ')",
                },
                "first": {
                    "type": "integer",
                    "description": "Number of PRDs to fetch (pagination, max 100)",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 25,
                },
                "after": {
                    "type": "string",
                    "description": "Cursor for pagination to fetch PRDs after this point",
                },
            },
            "required": ["project_id"],
            "additionalProperties": False,
        },
    ),
    Tool(
        name="update_prd",
        description="Update a Product Requirements Document (PRD) in a GitHub project",
        inputSchema={
            "type": "object",
            "properties": {
                "prd_item_id": {
                    "type": "string",
                    "description": "GitHub project item ID to update",
                },
                "title": {
                    "type": "string",
                    "description": "New title for the PRD",
                },
                "body": {
                    "type": "string",
                    "description": "New body content for the PRD",
                },
                "assignee_ids": {
                    "type": "array",
                    "description": "List of user IDs to assign to the PRD",
                    "items": {
                        "type": "string",
                    },
                },
            },
            "required": ["prd_item_id"],
            "additionalProperties": False,
        },
    ),
    Tool(
        name="update_prd_status",
        description="Update the status and/or priority fields of a Product Requirements Document (PRD) in a GitHub project using the Projects v2 field value update API",
        inputSchema={
            "type": "object",
            "properties": {
                "prd_item_id": {
                    "type": "string",
                    "description": "GitHub project item ID to update (e.g., 'PVTI_kwDOBQfyVc0FoQ')",
                },
                "status": {
                    "type": "string",
                    "description": "New PRD status value",
                    "enum": [
                        "Backlog",
                        "This Sprint",
                        "Up Next",
                        "In Progress",
                        "Done",
                        "Cancelled",
                    ],
                },
                "priority": {
                    "type": "string",
                    "description": "New PRD priority level",
                    "enum": ["Low", "Medium", "High", "Critical"],
                },
            },
            "required": ["prd_item_id"],
            "additionalProperties": False,
        },
    ),
    Tool(
        name="complete_prd",
        description="Mark a PRD as complete. This is a convenience method that automatically sets the PRD status to 'Done' without requiring other parameters.",
        inputSchema={
            "type": "object",
            "properties": {
                "prd_item_id": {
                    "type": "string",
                    "description": "GitHub project item ID of the PRD to complete",
                },
            },
            "required": ["prd_item_id"],
        },
    ),
]

# Map tool names to handler functions
PRD_TOOL_HANDLERS = {
    "add_prd_to_project": add_prd_to_project_handler,
    "list_prds_in_project": list_prds_in_project_handler,
    "delete_prd_from_project": delete_prd_from_project_handler,
    "update_prd": update_prd_handler,
    "update_prd_status": update_prd_status_handler,
    "complete_prd": complete_prd_handler,
}

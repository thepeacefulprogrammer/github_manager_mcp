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
        # Validate required parameters
        project_id = arguments.get("project_id", "").strip()
        title = arguments.get("title", "").strip()

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

        if not title:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Error: title is required to add PRD to project",
                    )
                ],
                isError=True,
            )

        # Extract optional parameters
        description = arguments.get("description", "")
        acceptance_criteria = arguments.get("acceptance_criteria")
        technical_requirements = arguments.get("technical_requirements")
        business_value = arguments.get("business_value")

        # Validate and parse status
        status_str = arguments.get("status", "Backlog")
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

        # Validate and parse priority
        priority_str = arguments.get("priority", "Medium")
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
]

# Map tool names to handler functions
PRD_TOOL_HANDLERS = {
    "add_prd_to_project": add_prd_to_project_handler,
    "delete_prd_from_project": delete_prd_from_project_handler,
}

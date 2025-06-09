"""
Status Column (Single Select Field) handlers for GitHub Projects v2.

This module provides MCP tool handlers for managing status columns in GitHub Projects v2.
Status columns are implemented as single select fields with predefined options.
"""

import logging
from typing import Any, Dict, List, Optional

from ..github_client import GitHubClient
from ..models.status_column import StatusColumn, StatusColumnOption

logger = logging.getLogger(__name__)


async def create_status_column_handler(
    client: GitHubClient,
    project_id: str,
    name: str,
    options: List[str],
) -> Dict[str, Any]:
    """
    Create a new status column (single select field) in a GitHub Projects v2 project.

    Args:
        client: GitHub GraphQL client
        project_id: ID of the project to add the status column to
        name: Name of the status column
        options: List of option names for the status column

    Returns:
        Dict containing success status and status column details

    Raises:
        ValueError: If validation fails or API request fails
    """
    try:
        # Validate inputs
        if not name or not name.strip():
            raise ValueError("Status column name cannot be empty")

        if not options or len(options) == 0:
            raise ValueError("At least one option is required for a status column")

        if len(options) > 50:
            raise ValueError("Maximum 50 options allowed for a status column")

        # Build GraphQL mutation
        mutation = """
        mutation CreateStatusColumn($projectId: ID!, $name: String!, $options: [ProjectV2SingleSelectFieldOptionInput!]!) {
            createProjectV2Field(input: {
                projectId: $projectId
                dataType: SINGLE_SELECT
                name: $name
                singleSelectOptions: $options
            }) {
                projectV2Field {
                    ... on ProjectV2SingleSelectField {
                        id
                        name
                        dataType
                        options {
                            id
                            name
                        }
                    }
                }
            }
        }
        """

        # Prepare options input
        options_input = [{"name": option} for option in options]

        variables = {
            "projectId": project_id,
            "name": name,
            "options": options_input,
        }

        logger.info(f"Creating status column '{name}' in project {project_id}")
        response = await client.execute_query(mutation, variables)

        field_data = response["createProjectV2Field"]["projectV2Field"]
        status_column = StatusColumn.from_github_field(field_data)

        logger.info(f"Successfully created status column: {status_column.id}")
        return {
            "success": True,
            "status_column": status_column.to_dict(),
            "message": f"Successfully created status column '{name}' with {len(options)} options",
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to create status column: {error_msg}")

        # Map common errors to user-friendly messages
        if "field with this name already exists" in error_msg.lower():
            raise ValueError(
                f"A field with the name '{name}' already exists in this project"
            )
        elif "could not resolve to projectv2 node" in error_msg.lower():
            raise ValueError(f"Invalid project ID: {project_id}")
        elif "permission" in error_msg.lower():
            raise ValueError(
                "Insufficient permissions to create status columns in this project"
            )
        else:
            raise ValueError(f"Failed to create status column: {error_msg}")


async def list_status_columns_handler(
    client: GitHubClient,
    project_id: str,
    first: int = 50,
) -> Dict[str, Any]:
    """
    List all status columns (single select fields) in a GitHub Projects v2 project.

    Args:
        client: GitHub GraphQL client
        project_id: ID of the project to list status columns from
        first: Maximum number of fields to retrieve (default: 50)

    Returns:
        Dict containing success status and list of status columns

    Raises:
        ValueError: If API request fails
    """
    try:
        # Build GraphQL query
        query = """
        query ListStatusColumns($projectId: ID!, $first: Int!) {
            node(id: $projectId) {
                ... on ProjectV2 {
                    fields(first: $first) {
                        nodes {
                            __typename
                            ... on ProjectV2SingleSelectField {
                                id
                                name
                                dataType
                                options {
                                    id
                                    name
                                }
                            }
                        }
                    }
                }
            }
        }
        """

        variables = {
            "projectId": project_id,
            "first": first,
        }

        logger.info(f"Listing status columns for project {project_id}")
        response = await client.execute_query(query, variables)

        # Filter for single select fields only
        fields_data = response["node"]["fields"]["nodes"]
        status_columns = []

        for field_data in fields_data:
            if field_data.get("__typename") == "ProjectV2SingleSelectField":
                status_column = StatusColumn.from_github_field(field_data)
                status_columns.append(status_column.to_dict())

        logger.info(f"Found {len(status_columns)} status columns")
        return {
            "success": True,
            "status_columns": status_columns,
            "count": len(status_columns),
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to list status columns: {error_msg}")

        if "could not resolve to projectv2 node" in error_msg.lower():
            raise ValueError(f"Invalid project ID: {project_id}")
        else:
            raise ValueError(f"Failed to list status columns: {error_msg}")


async def update_status_column_handler(
    client: GitHubClient,
    project_id: str,
    field_id: str,
    name: Optional[str] = None,
    options: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Update a status column (single select field) in a GitHub Projects v2 project.

    Args:
        client: GitHub GraphQL client
        project_id: ID of the project containing the status column
        field_id: ID of the status column field to update
        name: New name for the status column (optional)
        options: New list of option names (optional, but if provided, replaces all existing options)

    Returns:
        Dict containing success status and updated status column details

    Raises:
        ValueError: If validation fails or API request fails
    """
    try:
        # Validate inputs
        if options is not None and len(options) == 0:
            raise ValueError("At least one option is required for a status column")

        if options is not None and len(options) > 50:
            raise ValueError("Maximum 50 options allowed for a status column")

        # Build GraphQL mutation
        mutation = """
        mutation UpdateStatusColumn($projectId: ID!, $fieldId: ID!, $name: String, $options: [ProjectV2SingleSelectFieldOptionInput!]) {
            updateProjectV2Field(input: {
                projectId: $projectId
                fieldId: $fieldId
                name: $name
                singleSelectOptions: $options
            }) {
                projectV2Field {
                    ... on ProjectV2SingleSelectField {
                        id
                        name
                        dataType
                        options {
                            id
                            name
                        }
                    }
                }
            }
        }
        """

        variables = {
            "projectId": project_id,
            "fieldId": field_id,
        }

        if name is not None:
            variables["name"] = name

        if options is not None:
            variables["options"] = [{"name": option} for option in options]

        logger.info(f"Updating status column {field_id} in project {project_id}")
        response = await client.execute_query(mutation, variables)

        field_data = response["updateProjectV2Field"]["projectV2Field"]
        status_column = StatusColumn.from_github_field(field_data)

        logger.info(f"Successfully updated status column: {status_column.id}")
        return {
            "success": True,
            "status_column": status_column.to_dict(),
            "message": f"Successfully updated status column '{status_column.name}'",
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to update status column: {error_msg}")

        if "could not resolve to projectv2field node" in error_msg.lower():
            raise ValueError(f"Invalid field ID: {field_id}")
        elif "could not resolve to projectv2 node" in error_msg.lower():
            raise ValueError(f"Invalid project ID: {project_id}")
        elif "permission" in error_msg.lower():
            raise ValueError(
                "Insufficient permissions to update status columns in this project"
            )
        else:
            raise ValueError(f"Failed to update status column: {error_msg}")


async def delete_status_column_handler(
    client: GitHubClient,
    project_id: str,
    field_id: str,
    confirm: bool = False,
) -> Dict[str, Any]:
    """
    Delete a status column (single select field) from a GitHub Projects v2 project.

    Args:
        client: GitHub GraphQL client
        project_id: ID of the project containing the status column
        field_id: ID of the status column field to delete
        confirm: Confirmation flag to prevent accidental deletion

    Returns:
        Dict containing success status and deletion confirmation

    Raises:
        ValueError: If confirmation is missing or API request fails
    """
    try:
        # Require explicit confirmation
        if not confirm:
            raise ValueError("Deletion must be confirmed by setting confirm=True")

        # Build GraphQL mutation
        mutation = """
        mutation DeleteStatusColumn($projectId: ID!, $fieldId: ID!) {
            deleteProjectV2Field(input: {
                projectId: $projectId
                fieldId: $fieldId
            }) {
                deletedFieldId
            }
        }
        """

        variables = {
            "projectId": project_id,
            "fieldId": field_id,
        }

        logger.info(f"Deleting status column {field_id} from project {project_id}")
        response = await client.execute_query(mutation, variables)

        deleted_field_id = response["deleteProjectV2Field"]["deletedFieldId"]

        logger.info(f"Successfully deleted status column: {deleted_field_id}")
        return {
            "success": True,
            "deleted_field_id": deleted_field_id,
            "message": f"Successfully deleted status column {deleted_field_id}",
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to delete status column: {error_msg}")

        if "cannot delete the default status field" in error_msg.lower():
            raise ValueError("Cannot delete the default Status field")
        elif "could not resolve to projectv2field node" in error_msg.lower():
            raise ValueError(f"Invalid field ID: {field_id}")
        elif "could not resolve to projectv2 node" in error_msg.lower():
            raise ValueError(f"Invalid project ID: {project_id}")
        elif "permission" in error_msg.lower():
            raise ValueError(
                "Insufficient permissions to delete status columns in this project"
            )
        else:
            raise ValueError(f"Failed to delete status column: {error_msg}")


async def get_status_column_handler(
    client: GitHubClient,
    project_id: str,
    field_id: str,
) -> Dict[str, Any]:
    """
    Get details of a specific status column (single select field) in a GitHub Projects v2 project.

    Args:
        client: GitHub GraphQL client
        project_id: ID of the project containing the status column
        field_id: ID of the status column field to retrieve

    Returns:
        Dict containing success status and status column details

    Raises:
        ValueError: If API request fails or field is not a single select field
    """
    try:
        # Build GraphQL query
        query = """
        query GetStatusColumn($fieldId: ID!) {
            node(id: $fieldId) {
                __typename
                ... on ProjectV2SingleSelectField {
                    id
                    name
                    dataType
                    options {
                        id
                        name
                    }
                }
            }
        }
        """

        variables = {
            "fieldId": field_id,
        }

        logger.info(f"Getting status column {field_id}")
        response = await client.execute_query(query, variables)

        field_data = response["node"]

        # Check if it's a single select field
        if field_data.get("__typename") != "ProjectV2SingleSelectField":
            raise ValueError("Field is not a single select field (status column)")

        status_column = StatusColumn.from_github_field(field_data)

        logger.info(f"Successfully retrieved status column: {status_column.id}")
        return {
            "success": True,
            "status_column": status_column.to_dict(),
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to get status column: {error_msg}")

        if "could not resolve to projectv2field node" in error_msg.lower():
            raise ValueError(f"Invalid field ID: {field_id}")
        elif "field is not a single select field" in error_msg.lower():
            raise ValueError("Field is not a single select field (status column)")
        else:
            raise ValueError(f"Failed to get status column: {error_msg}")

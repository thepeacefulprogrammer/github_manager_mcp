"""
Relationship management utilities for GitHub Project Manager MCP.

This module provides utilities for managing hierarchical relationships
between PRDs, Tasks, and Subtasks in GitHub Projects v2.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RelationshipValidationResult:
    """Result of relationship validation operations."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]


class RelationshipManager:
    """Manages hierarchical relationships between PRDs, tasks, and subtasks."""

    def __init__(self, github_client=None):
        """Initialize the relationship manager.

        Args:
            github_client: GitHub client for API operations
        """
        self.github_client = github_client
        logger.info("RelationshipManager initialized")

    async def validate_prd_task_relationship(
        self, project_id: str, prd_item_id: str, task_item_id: str
    ) -> RelationshipValidationResult:
        """Validate that a task belongs to the specified PRD.

        Args:
            project_id: GitHub project ID
            prd_item_id: PRD project item ID
            task_item_id: Task project item ID

        Returns:
            RelationshipValidationResult with validation status
        """
        errors = []
        warnings = []
        metadata = {}

        try:
            # Validate input parameters
            if not all([project_id, prd_item_id, task_item_id]):
                errors.append("Missing required parameters for relationship validation")
                return RelationshipValidationResult(
                    is_valid=False, errors=errors, warnings=warnings, metadata=metadata
                )

            if not self.github_client:
                errors.append("GitHub client not initialized")
                return RelationshipValidationResult(
                    is_valid=False, errors=errors, warnings=warnings, metadata=metadata
                )

            logger.info(
                f"Validating PRD-Task relationship: PRD={prd_item_id}, Task={task_item_id}"
            )

            # Query the task to get its content and check parent PRD reference
            task_query = """
            query($taskId: ID!) {
                node(id: $taskId) {
                    ... on ProjectV2Item {
                        id
                        content {
                            ... on DraftIssue {
                                id
                                title
                                body
                            }
                        }
                    }
                }
            }
            """

            task_response = await self.github_client.query(
                task_query, {"taskId": task_item_id}
            )

            if not task_response or "node" not in task_response:
                errors.append(f"Task not found: {task_item_id}")
                return RelationshipValidationResult(
                    is_valid=False, errors=errors, warnings=warnings, metadata=metadata
                )

            task_node = task_response["node"]
            if not task_node or "content" not in task_node:
                errors.append(f"Invalid task structure: {task_item_id}")
                return RelationshipValidationResult(
                    is_valid=False, errors=errors, warnings=warnings, metadata=metadata
                )

            task_content = task_node["content"]
            if not task_content or "body" not in task_content:
                errors.append(f"Task has no content body: {task_item_id}")
                return RelationshipValidationResult(
                    is_valid=False, errors=errors, warnings=warnings, metadata=metadata
                )

            # Parse the task body to find parent PRD reference
            task_body = task_content["body"] or ""

            # Look for parent PRD reference in task body
            import re

            prd_pattern = r"\*\*Parent PRD:\*\*\s*(\w+)"
            prd_match = re.search(prd_pattern, task_body)

            if not prd_match:
                errors.append(f"Task {task_item_id} has no parent PRD reference")
                return RelationshipValidationResult(
                    is_valid=False, errors=errors, warnings=warnings, metadata=metadata
                )

            referenced_prd_id = prd_match.group(1)

            # Validate that the referenced PRD matches the expected PRD
            if referenced_prd_id != prd_item_id:
                errors.append(
                    f"Task {task_item_id} belongs to PRD {referenced_prd_id}, not {prd_item_id}"
                )
                return RelationshipValidationResult(
                    is_valid=False, errors=errors, warnings=warnings, metadata=metadata
                )

            # Success - valid relationship
            metadata = {
                "task_id": task_item_id,
                "prd_id": prd_item_id,
                "referenced_prd_id": referenced_prd_id,
                "task_title": task_content.get("title", ""),
            }

            return RelationshipValidationResult(
                is_valid=True, errors=errors, warnings=warnings, metadata=metadata
            )

        except Exception as e:
            logger.error(f"Error validating PRD-Task relationship: {e}")
            errors.append(f"Validation failed: {str(e)}")
            return RelationshipValidationResult(
                is_valid=False, errors=errors, warnings=warnings, metadata=metadata
            )

    async def validate_task_subtask_relationship(
        self, project_id: str, task_item_id: str, subtask_item_id: str
    ) -> RelationshipValidationResult:
        """Validate that a subtask belongs to the specified task.

        Args:
            project_id: GitHub project ID
            task_item_id: Task project item ID
            subtask_item_id: Subtask project item ID

        Returns:
            RelationshipValidationResult with validation status
        """
        errors = []
        warnings = []
        metadata = {}

        try:
            # Validate input parameters
            if not all([project_id, task_item_id, subtask_item_id]):
                errors.append("Missing required parameters for relationship validation")
                return RelationshipValidationResult(
                    is_valid=False, errors=errors, warnings=warnings, metadata=metadata
                )

            if not self.github_client:
                errors.append("GitHub client not initialized")
                return RelationshipValidationResult(
                    is_valid=False, errors=errors, warnings=warnings, metadata=metadata
                )

            logger.info(
                f"Validating Task-Subtask relationship: Task={task_item_id}, Subtask={subtask_item_id}"
            )

            # Query the subtask to get its content and check parent task reference
            subtask_query = """
            query($subtaskId: ID!) {
                node(id: $subtaskId) {
                    ... on ProjectV2Item {
                        id
                        content {
                            ... on DraftIssue {
                                id
                                title
                                body
                            }
                        }
                    }
                }
            }
            """

            subtask_response = await self.github_client.query(
                subtask_query, {"subtaskId": subtask_item_id}
            )

            if not subtask_response or "node" not in subtask_response:
                errors.append(f"Subtask not found: {subtask_item_id}")
                return RelationshipValidationResult(
                    is_valid=False, errors=errors, warnings=warnings, metadata=metadata
                )

            subtask_node = subtask_response["node"]
            if not subtask_node or "content" not in subtask_node:
                errors.append(f"Invalid subtask structure: {subtask_item_id}")
                return RelationshipValidationResult(
                    is_valid=False, errors=errors, warnings=warnings, metadata=metadata
                )

            subtask_content = subtask_node["content"]
            if not subtask_content or "body" not in subtask_content:
                errors.append(f"Subtask has no content body: {subtask_item_id}")
                return RelationshipValidationResult(
                    is_valid=False, errors=errors, warnings=warnings, metadata=metadata
                )

            # Parse the subtask body to find parent task reference
            subtask_body = subtask_content["body"] or ""

            # Look for parent task reference in subtask body
            import re

            task_pattern = r"\*\*Parent Task:\*\*\s*(\w+)"
            task_match = re.search(task_pattern, subtask_body)

            if not task_match:
                errors.append(f"Subtask {subtask_item_id} has no parent task reference")
                return RelationshipValidationResult(
                    is_valid=False, errors=errors, warnings=warnings, metadata=metadata
                )

            referenced_task_id = task_match.group(1)

            # Validate that the referenced task matches the expected task
            if referenced_task_id != task_item_id:
                errors.append(
                    f"Subtask {subtask_item_id} belongs to Task {referenced_task_id}, not {task_item_id}"
                )
                return RelationshipValidationResult(
                    is_valid=False, errors=errors, warnings=warnings, metadata=metadata
                )

            # Success - valid relationship
            metadata = {
                "subtask_id": subtask_item_id,
                "task_id": task_item_id,
                "referenced_task_id": referenced_task_id,
                "subtask_title": subtask_content.get("title", ""),
            }

            return RelationshipValidationResult(
                is_valid=True, errors=errors, warnings=warnings, metadata=metadata
            )

        except Exception as e:
            logger.error(f"Error validating Task-Subtask relationship: {e}")
            errors.append(f"Validation failed: {str(e)}")
            return RelationshipValidationResult(
                is_valid=False, errors=errors, warnings=warnings, metadata=metadata
            )

    async def get_prd_children(
        self, project_id: str, prd_item_id: str
    ) -> List[Dict[str, Any]]:
        """Get all tasks that belong to a specific PRD.

        Args:
            project_id: GitHub project ID
            prd_item_id: PRD project item ID

        Returns:
            List of task items belonging to the PRD
        """
        try:
            if not self.github_client:
                logger.error("GitHub client not initialized")
                return []

            logger.info(f"Getting children for PRD: {prd_item_id}")

            # Query all items in the project and filter for tasks belonging to this PRD
            project_query = """
            query($projectId: ID!, $first: Int!) {
                node(id: $projectId) {
                    ... on ProjectV2 {
                        items(first: $first) {
                            nodes {
                                id
                                content {
                                    ... on DraftIssue {
                                        id
                                        title
                                        body
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """

            response = await self.github_client.query(
                project_query, {"projectId": project_id, "first": 100}
            )

            if not response or "node" not in response:
                logger.warning(f"No response or node for project: {project_id}")
                return []

            project_node = response["node"]
            if not project_node or "items" not in project_node:
                logger.warning(f"No items found in project: {project_id}")
                return []

            items = project_node["items"]["nodes"]
            children = []

            # Filter items to find tasks that belong to this PRD
            import re

            prd_pattern = r"\*\*Parent PRD:\*\*\s*(\w+)"

            for item in items:
                if not item or "content" not in item:
                    continue

                content = item["content"]
                if not content or "body" not in content:
                    continue

                body = content["body"] or ""
                prd_match = re.search(prd_pattern, body)

                if prd_match and prd_match.group(1) == prd_item_id:
                    children.append(
                        {
                            "id": item["id"],
                            "content_id": content["id"],
                            "title": content.get("title", ""),
                            "body": body,
                            "parent_prd_id": prd_item_id,
                        }
                    )

            logger.info(f"Found {len(children)} children for PRD {prd_item_id}")
            return children

        except Exception as e:
            logger.error(f"Error getting PRD children: {e}")
            return []

    async def get_task_children(
        self, project_id: str, task_item_id: str
    ) -> List[Dict[str, Any]]:
        """Get all subtasks that belong to a specific task.

        Args:
            project_id: GitHub project ID
            task_item_id: Task project item ID

        Returns:
            List of subtask items belonging to the task
        """
        try:
            if not self.github_client:
                logger.error("GitHub client not initialized")
                return []

            logger.info(f"Getting children for Task: {task_item_id}")

            # Query all items in the project and filter for subtasks belonging to this task
            project_query = """
            query($projectId: ID!, $first: Int!) {
                node(id: $projectId) {
                    ... on ProjectV2 {
                        items(first: $first) {
                            nodes {
                                id
                                content {
                                    ... on DraftIssue {
                                        id
                                        title
                                        body
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """

            response = await self.github_client.query(
                project_query, {"projectId": project_id, "first": 100}
            )

            if not response or "node" not in response:
                logger.warning(f"No response or node for project: {project_id}")
                return []

            project_node = response["node"]
            if not project_node or "items" not in project_node:
                logger.warning(f"No items found in project: {project_id}")
                return []

            items = project_node["items"]["nodes"]
            children = []

            # Filter items to find subtasks that belong to this task
            import re

            task_pattern = r"\*\*Parent Task:\*\*\s*(\w+)"

            for item in items:
                if not item or "content" not in item:
                    continue

                content = item["content"]
                if not content or "body" not in content:
                    continue

                body = content["body"] or ""
                task_match = re.search(task_pattern, body)

                if task_match and task_match.group(1) == task_item_id:
                    # Extract order from subtask body if present
                    order_pattern = r"\*\*Order:\*\*\s*(\d+)"
                    order_match = re.search(order_pattern, body)
                    order = int(order_match.group(1)) if order_match else 0

                    children.append(
                        {
                            "id": item["id"],
                            "content_id": content["id"],
                            "title": content.get("title", ""),
                            "body": body,
                            "parent_task_id": task_item_id,
                            "order": order,
                        }
                    )

            # Sort by order
            children.sort(key=lambda x: x["order"])

            logger.info(f"Found {len(children)} children for Task {task_item_id}")
            return children

        except Exception as e:
            logger.error(f"Error getting Task children: {e}")
            return []

    async def validate_hierarchy_consistency(
        self, project_id: str
    ) -> RelationshipValidationResult:
        """Validate the consistency of the entire project hierarchy.

        Args:
            project_id: GitHub project ID

        Returns:
            RelationshipValidationResult with overall hierarchy validation status
        """
        errors = []
        warnings = []
        metadata = {}

        try:
            if not self.github_client:
                errors.append("GitHub client not initialized")
                return RelationshipValidationResult(
                    is_valid=False, errors=errors, warnings=warnings, metadata=metadata
                )

            logger.info(f"Validating hierarchy consistency for project: {project_id}")

            # Query all items in the project
            project_query = """
            query($projectId: ID!, $first: Int!) {
                node(id: $projectId) {
                    ... on ProjectV2 {
                        items(first: $first) {
                            nodes {
                                id
                                content {
                                    ... on DraftIssue {
                                        id
                                        title
                                        body
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """

            response = await self.github_client.query(
                project_query, {"projectId": project_id, "first": 100}
            )

            if not response or "node" not in response:
                errors.append(f"Project not found: {project_id}")
                return RelationshipValidationResult(
                    is_valid=False, errors=errors, warnings=warnings, metadata=metadata
                )

            project_node = response["node"]
            if not project_node or "items" not in project_node:
                warnings.append("No items found in project")
                return RelationshipValidationResult(
                    is_valid=True,
                    errors=errors,
                    warnings=warnings,
                    metadata={"total_items": 0},
                )

            items = project_node["items"]["nodes"]

            # Categorize items
            prds = []
            tasks = []
            subtasks = []
            orphaned_items = []

            import re

            prd_pattern = r"\*\*Parent PRD:\*\*\s*(\w+)"
            task_pattern = r"\*\*Parent Task:\*\*\s*(\w+)"
            type_pattern = r"\*\*Type:\*\*\s*(\w+)"

            for item in items:
                if not item or "content" not in item:
                    continue

                content = item["content"]
                if not content or "body" not in content:
                    orphaned_items.append(item["id"])
                    continue

                body = content["body"] or ""

                # Check if it's a subtask
                type_match = re.search(type_pattern, body)
                if type_match and type_match.group(1).lower() == "subtask":
                    task_match = re.search(task_pattern, body)
                    if task_match:
                        subtasks.append(
                            {
                                "id": item["id"],
                                "parent_task_id": task_match.group(1),
                                "title": content.get("title", ""),
                            }
                        )
                    else:
                        orphaned_items.append(item["id"])
                        errors.append(
                            f"Subtask {item['id']} has no parent task reference"
                        )
                # Check if it's a task (contains "Task" in title but also has Parent PRD reference)
                elif re.search(prd_pattern, body):
                    prd_match = re.search(prd_pattern, body)
                    tasks.append(
                        {
                            "id": item["id"],
                            "parent_prd_id": prd_match.group(1),
                            "title": content.get("title", ""),
                        }
                    )
                # Check if it appears to be a task (contains "Task" in title) but lacks parent PRD reference
                elif (
                    "task" in content.get("title", "").lower() or "task" in body.lower()
                ):
                    orphaned_items.append(item["id"])
                    errors.append(f"Task {item['id']} has no parent PRD reference")
                # Assume it's a PRD if it doesn't match other patterns
                else:
                    prds.append({"id": item["id"], "title": content.get("title", "")})

            # Validate relationships
            prd_ids = {prd["id"] for prd in prds}
            task_ids = {task["id"] for task in tasks}

            # Check for orphaned tasks (referencing non-existent PRDs)
            for task in tasks:
                if task["parent_prd_id"] not in prd_ids:
                    errors.append(
                        f"Task {task['id']} references non-existent PRD {task['parent_prd_id']}"
                    )

            # Check for orphaned subtasks (referencing non-existent tasks)
            for subtask in subtasks:
                if subtask["parent_task_id"] not in task_ids:
                    errors.append(
                        f"Subtask {subtask['id']} references non-existent Task {subtask['parent_task_id']}"
                    )

            # Log orphaned items
            if orphaned_items:
                warnings.append(
                    f"Found {len(orphaned_items)} orphaned items without proper structure"
                )

            # Compile metadata
            metadata = {
                "total_items": len(items),
                "prds_count": len(prds),
                "tasks_count": len(tasks),
                "subtasks_count": len(subtasks),
                "orphaned_count": len(orphaned_items),
                "prd_ids": [prd["id"] for prd in prds],
                "task_ids": [task["id"] for task in tasks],
                "subtask_ids": [subtask["id"] for subtask in subtasks],
                "orphaned_ids": orphaned_items,
            }

            is_valid = len(errors) == 0
            logger.info(
                f"Hierarchy validation complete: {is_valid}, {len(errors)} errors, {len(warnings)} warnings"
            )

            return RelationshipValidationResult(
                is_valid=is_valid, errors=errors, warnings=warnings, metadata=metadata
            )

        except Exception as e:
            logger.error(f"Error validating hierarchy consistency: {e}")
            errors.append(f"Hierarchy validation failed: {str(e)}")
            return RelationshipValidationResult(
                is_valid=False, errors=errors, warnings=warnings, metadata=metadata
            )

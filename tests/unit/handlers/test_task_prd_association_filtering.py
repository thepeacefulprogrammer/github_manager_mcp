"""
Comprehensive unit tests for task-PRD association filtering functionality.

This test file focuses on verifying that the task-PRD association filtering
works correctly across all scenarios, including edge cases and real-world usage patterns.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from github_project_manager_mcp.handlers.task_handlers import list_tasks_handler


class TestTaskPRDAssociationFiltering:
    """Comprehensive tests for task-PRD association filtering."""

    @pytest.fixture
    def mock_github_client(self):
        """Mock GitHub client for testing."""
        client = AsyncMock()
        client.query = AsyncMock()
        return client

    @pytest.fixture
    def sample_mixed_project_response(self):
        """Sample response with mixed PRDs, tasks, and subtasks for comprehensive testing."""
        return {
            "data": {
                "node": {
                    "title": "Mixed Project",
                    "items": {
                        "totalCount": 8,
                        "pageInfo": {
                            "hasNextPage": False,
                            "hasPreviousPage": False,
                            "startCursor": "cursor1",
                            "endCursor": "cursor8",
                        },
                        "nodes": [
                            # PRD 1 - Should NOT be included in task results
                            {
                                "id": "PVTI_prd1",
                                "createdAt": "2023-01-01T00:00:00Z",
                                "updatedAt": "2023-01-02T00:00:00Z",
                                "content": {
                                    "title": "PRD 1: User Authentication System",
                                    "body": "This is a PRD for user authentication.",
                                    "createdAt": "2023-01-01T00:00:00Z",
                                    "updatedAt": "2023-01-02T00:00:00Z",
                                    "assignees": {"nodes": []},
                                },
                                "fieldValues": {
                                    "nodes": [
                                        {"text": "High", "field": {"name": "Priority"}}
                                    ]
                                },
                            },
                            # Task 1 for PRD 1 - Field-based Parent PRD
                            {
                                "id": "PVTI_task1",
                                "createdAt": "2023-01-01T00:00:00Z",
                                "updatedAt": "2023-01-02T00:00:00Z",
                                "content": {
                                    "title": "Implement login endpoint",
                                    "body": "Create REST API endpoint for user login",
                                    "createdAt": "2023-01-01T00:00:00Z",
                                    "updatedAt": "2023-01-02T00:00:00Z",
                                    "assignees": {"nodes": []},
                                },
                                "fieldValues": {
                                    "nodes": [
                                        {
                                            "text": "PVTI_prd1",
                                            "field": {"name": "Parent PRD"},
                                        },
                                        {
                                            "text": "Medium",
                                            "field": {"name": "Priority"},
                                        },
                                    ]
                                },
                            },
                            # Task 2 for PRD 1 - Description-based Parent PRD
                            {
                                "id": "PVTI_task2",
                                "createdAt": "2023-01-01T00:00:00Z",
                                "updatedAt": "2023-01-02T00:00:00Z",
                                "content": {
                                    "title": "Create password validation",
                                    "body": "**Parent PRD:** PVTI_prd1\n\nImplement password strength validation logic",
                                    "createdAt": "2023-01-01T00:00:00Z",
                                    "updatedAt": "2023-01-02T00:00:00Z",
                                    "assignees": {"nodes": []},
                                },
                                "fieldValues": {
                                    "nodes": [
                                        {"text": "High", "field": {"name": "Priority"}}
                                    ]
                                },
                            },
                            # PRD 2 - Should NOT be included in task results
                            {
                                "id": "PVTI_prd2",
                                "createdAt": "2023-01-01T00:00:00Z",
                                "updatedAt": "2023-01-02T00:00:00Z",
                                "content": {
                                    "title": "PRD 2: Data Export Feature",
                                    "body": "This is a PRD for data export functionality.",
                                    "createdAt": "2023-01-01T00:00:00Z",
                                    "updatedAt": "2023-01-02T00:00:00Z",
                                    "assignees": {"nodes": []},
                                },
                                "fieldValues": {
                                    "nodes": [
                                        {
                                            "text": "Medium",
                                            "field": {"name": "Priority"},
                                        }
                                    ]
                                },
                            },
                            # Task 3 for PRD 2 - Field-based Parent PRD
                            {
                                "id": "PVTI_task3",
                                "createdAt": "2023-01-01T00:00:00Z",
                                "updatedAt": "2023-01-02T00:00:00Z",
                                "content": {
                                    "title": "CSV export functionality",
                                    "body": "Implement CSV export for user data",
                                    "createdAt": "2023-01-01T00:00:00Z",
                                    "updatedAt": "2023-01-02T00:00:00Z",
                                    "assignees": {"nodes": []},
                                },
                                "fieldValues": {
                                    "nodes": [
                                        {
                                            "text": "PVTI_prd2",
                                            "field": {"name": "Parent PRD"},
                                        },
                                        {"text": "Low", "field": {"name": "Priority"}},
                                    ]
                                },
                            },
                            # Task 4 for PRD 2 - Description-based Parent PRD with extra formatting
                            {
                                "id": "PVTI_task4",
                                "createdAt": "2023-01-01T00:00:00Z",
                                "updatedAt": "2023-01-02T00:00:00Z",
                                "content": {
                                    "title": "PDF export functionality",
                                    "body": "## Task Details\n\n**Parent PRD:** PVTI_prd2\n\n**Description:**\nImplement PDF export for user reports with proper formatting.",
                                    "createdAt": "2023-01-01T00:00:00Z",
                                    "updatedAt": "2023-01-02T00:00:00Z",
                                    "assignees": {"nodes": []},
                                },
                                "fieldValues": {
                                    "nodes": [
                                        {
                                            "text": "Medium",
                                            "field": {"name": "Priority"},
                                        }
                                    ]
                                },
                            },
                            # Subtask 1 for Task 1 - Should NOT be included (not a task)
                            {
                                "id": "DI_subtask1",
                                "createdAt": "2023-01-01T00:00:00Z",
                                "updatedAt": "2023-01-02T00:00:00Z",
                                "content": {
                                    "title": "Write login endpoint tests",
                                    "body": "**Parent Task:** PVTI_task1\n\nWrite comprehensive unit tests for the login endpoint",
                                    "createdAt": "2023-01-01T00:00:00Z",
                                    "updatedAt": "2023-01-02T00:00:00Z",
                                    "assignees": {"nodes": []},
                                },
                                "fieldValues": {
                                    "nodes": [
                                        {
                                            "text": "PVTI_task1",
                                            "field": {"name": "Parent Task"},
                                        }
                                    ]
                                },
                            },
                            # Orphaned task with no Parent PRD - Should NOT be included
                            {
                                "id": "PVTI_orphan",
                                "createdAt": "2023-01-01T00:00:00Z",
                                "updatedAt": "2023-01-02T00:00:00Z",
                                "content": {
                                    "title": "Orphaned task",
                                    "body": "This task has no parent PRD association",
                                    "createdAt": "2023-01-01T00:00:00Z",
                                    "updatedAt": "2023-01-02T00:00:00Z",
                                    "assignees": {"nodes": []},
                                },
                                "fieldValues": {
                                    "nodes": [
                                        {"text": "Low", "field": {"name": "Priority"}}
                                    ]
                                },
                            },
                            # Task with malformed Parent PRD in description - Should NOT be included
                            {
                                "id": "PVTI_malformed",
                                "createdAt": "2023-01-01T00:00:00Z",
                                "updatedAt": "2023-01-02T00:00:00Z",
                                "content": {
                                    "title": "Malformed task",
                                    "body": "**Parent PRD:** invalid_format\n\nThis task has malformed PRD reference",
                                    "createdAt": "2023-01-01T00:00:00Z",
                                    "updatedAt": "2023-01-02T00:00:00Z",
                                    "assignees": {"nodes": []},
                                },
                                "fieldValues": {
                                    "nodes": [
                                        {"text": "Low", "field": {"name": "Priority"}}
                                    ]
                                },
                            },
                        ],
                    },
                }
            }
        }

    @pytest.mark.asyncio
    async def test_filter_tasks_by_specific_prd_field_based(
        self, mock_github_client, sample_mixed_project_response
    ):
        """Test filtering tasks by specific PRD using field-based Parent PRD."""
        mock_github_client.query.return_value = sample_mixed_project_response

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            result = await list_tasks_handler(
                {"project_id": "PVT_test123", "parent_prd_id": "PVTI_prd1", "first": 10}
            )

            assert (
                not result.isError
            ), f"Expected success but got error: {result.content[0].text if result.isError else ''}"
            content = result.content[0].text

            # Should include both tasks for PRD 1
            assert "Implement login endpoint" in content
            assert "Create password validation" in content

            # Should NOT include tasks for PRD 2
            assert "CSV export functionality" not in content
            assert "PDF export functionality" not in content

            # Should NOT include PRDs themselves
            assert "PRD 1: User Authentication System" not in content
            assert "PRD 2: Data Export Feature" not in content

            # Should NOT include subtasks
            assert "Write login endpoint tests" not in content

            # Should NOT include orphaned tasks
            assert "Orphaned task" not in content

    @pytest.mark.asyncio
    async def test_filter_tasks_by_specific_prd_description_based(
        self, mock_github_client, sample_mixed_project_response
    ):
        """Test filtering tasks by specific PRD using description-based Parent PRD."""
        mock_github_client.query.return_value = sample_mixed_project_response

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            result = await list_tasks_handler(
                {"project_id": "PVT_test123", "parent_prd_id": "PVTI_prd2", "first": 10}
            )

            assert not result.isError
            content = result.content[0].text

            # Should include both tasks for PRD 2
            assert "CSV export functionality" in content
            assert "PDF export functionality" in content

            # Should NOT include tasks for PRD 1
            assert "Implement login endpoint" not in content
            assert "Create password validation" not in content

    @pytest.mark.asyncio
    async def test_list_all_tasks_without_prd_filter(
        self, mock_github_client, sample_mixed_project_response
    ):
        """Test listing all tasks when no PRD filter is specified."""
        mock_github_client.query.return_value = sample_mixed_project_response

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            result = await list_tasks_handler(
                {"project_id": "PVT_test123", "first": 10}
            )

            assert not result.isError
            content = result.content[0].text

            # Should include all valid tasks (field-based and description-based)
            assert "Implement login endpoint" in content
            assert "Create password validation" in content
            assert "CSV export functionality" in content
            assert "PDF export functionality" in content

            # Should NOT include PRDs
            assert "PRD 1: User Authentication System" not in content
            assert "PRD 2: Data Export Feature" not in content

            # Should NOT include subtasks
            assert "Write login endpoint tests" not in content

            # Should NOT include orphaned tasks (no Parent PRD)
            assert "Orphaned task" not in content

            # Should NOT include malformed tasks
            assert "Malformed task" not in content

    @pytest.mark.asyncio
    async def test_filter_tasks_by_nonexistent_prd(
        self, mock_github_client, sample_mixed_project_response
    ):
        """Test filtering by a PRD that doesn't exist returns no tasks."""
        mock_github_client.query.return_value = sample_mixed_project_response

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            result = await list_tasks_handler(
                {
                    "project_id": "PVT_test123",
                    "parent_prd_id": "PVTI_nonexistent",
                    "first": 10,
                }
            )

            assert not result.isError
            content = result.content[0].text

            # Should return message indicating no tasks found
            assert "No tasks found" in content or "0 tasks found" in content

    @pytest.mark.asyncio
    async def test_task_prd_association_priority_field_over_description(
        self, mock_github_client
    ):
        """Test that field-based Parent PRD takes priority over description-based when both exist."""
        conflict_response = {
            "data": {
                "node": {
                    "title": "Conflict Test Project",
                    "items": {
                        "totalCount": 1,
                        "pageInfo": {"hasNextPage": False},
                        "nodes": [
                            {
                                "id": "PVTI_conflict_task",
                                "createdAt": "2023-01-01T00:00:00Z",
                                "updatedAt": "2023-01-02T00:00:00Z",
                                "content": {
                                    "title": "Conflicted task",
                                    "body": "**Parent PRD:** PVTI_description_prd\n\nThis task has conflicting Parent PRD references",
                                    "createdAt": "2023-01-01T00:00:00Z",
                                    "updatedAt": "2023-01-02T00:00:00Z",
                                    "assignees": {"nodes": []},
                                },
                                "fieldValues": {
                                    "nodes": [
                                        {
                                            "text": "PVTI_field_prd",
                                            "field": {"name": "Parent PRD"},
                                        }
                                    ]
                                },
                            }
                        ],
                    },
                }
            }
        }

        mock_github_client.query.return_value = conflict_response

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            # Filter by field-based PRD (should find the task)
            result = await list_tasks_handler(
                {
                    "project_id": "PVT_test123",
                    "parent_prd_id": "PVTI_field_prd",
                    "first": 10,
                }
            )

            assert not result.isError
            content = result.content[0].text
            assert "Conflicted task" in content

            # Filter by description-based PRD (should NOT find the task because field takes priority)
            result = await list_tasks_handler(
                {
                    "project_id": "PVT_test123",
                    "parent_prd_id": "PVTI_description_prd",
                    "first": 10,
                }
            )

            assert not result.isError
            content = result.content[0].text
            assert "No tasks found" in content or "0 tasks found" in content

    @pytest.mark.asyncio
    async def test_task_count_accuracy_with_filtering(
        self, mock_github_client, sample_mixed_project_response
    ):
        """Test that task count is accurate when PRD filtering is applied."""
        mock_github_client.query.return_value = sample_mixed_project_response

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            # Test PRD 1 (should have 2 tasks)
            result = await list_tasks_handler(
                {"project_id": "PVT_test123", "parent_prd_id": "PVTI_prd1", "first": 10}
            )

            assert not result.isError
            content = result.content[0].text

            # Count task entries using more specific pattern (## N. where N is a number)
            import re

            task_matches = re.findall(r"## \d+\.", content)
            task_count = len(task_matches)
            assert (
                task_count == 2
            ), f"Expected 2 tasks for PRD 1, but found {task_count}. Content: {content}"

            # Test PRD 2 (should have 2 tasks)
            result = await list_tasks_handler(
                {"project_id": "PVT_test123", "parent_prd_id": "PVTI_prd2", "first": 10}
            )

            assert not result.isError
            content = result.content[0].text

            task_matches = re.findall(r"## \d+\.", content)
            task_count = len(task_matches)
            assert (
                task_count == 2
            ), f"Expected 2 tasks for PRD 2, but found {task_count}. Content: {content}"

    @pytest.mark.asyncio
    async def test_task_metadata_preservation_with_filtering(
        self, mock_github_client, sample_mixed_project_response
    ):
        """Test that task metadata is preserved correctly when filtering is applied."""
        mock_github_client.query.return_value = sample_mixed_project_response

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            result = await list_tasks_handler(
                {"project_id": "PVT_test123", "parent_prd_id": "PVTI_prd1", "first": 10}
            )

            assert not result.isError
            content = result.content[0].text

            # Verify metadata preservation
            assert "PVTI_task1" in content  # Item ID
            assert "PVTI_task2" in content  # Item ID
            assert "Medium" in content or "High" in content  # Priority
            assert "2023-01-01T00:00:00Z" in content  # Created date
            assert "Draft Issue" in content  # Type

    @pytest.mark.asyncio
    async def test_regex_pattern_robustness_for_prd_extraction(
        self, mock_github_client
    ):
        """Test that the regex pattern for PRD extraction is robust across different formats."""
        varied_format_response = {
            "data": {
                "node": {
                    "title": "Format Test Project",
                    "items": {
                        "totalCount": 5,
                        "pageInfo": {"hasNextPage": False},
                        "nodes": [
                            {
                                "id": "PVTI_format1",
                                "createdAt": "2023-01-01T00:00:00Z",
                                "updatedAt": "2023-01-02T00:00:00Z",
                                "content": {
                                    "title": "Standard format",
                                    "body": "**Parent PRD:** PVTI_test_prd\n\nStandard format task",
                                    "createdAt": "2023-01-01T00:00:00Z",
                                    "updatedAt": "2023-01-02T00:00:00Z",
                                    "assignees": {"nodes": []},
                                },
                                "fieldValues": {"nodes": []},
                            },
                            {
                                "id": "PVTI_format2",
                                "createdAt": "2023-01-01T00:00:00Z",
                                "updatedAt": "2023-01-02T00:00:00Z",
                                "content": {
                                    "title": "Extra spaces format",
                                    "body": "**Parent PRD:**     PVTI_test_prd\n\nExtra spaces around PRD ID",
                                    "createdAt": "2023-01-01T00:00:00Z",
                                    "updatedAt": "2023-01-02T00:00:00Z",
                                    "assignees": {"nodes": []},
                                },
                                "fieldValues": {"nodes": []},
                            },
                            {
                                "id": "PVTI_format3",
                                "createdAt": "2023-01-01T00:00:00Z",
                                "updatedAt": "2023-01-02T00:00:00Z",
                                "content": {
                                    "title": "Mixed case format",
                                    "body": "**parent prd:** PVTI_test_prd\n\nMixed case should NOT match",
                                    "createdAt": "2023-01-01T00:00:00Z",
                                    "updatedAt": "2023-01-02T00:00:00Z",
                                    "assignees": {"nodes": []},
                                },
                                "fieldValues": {"nodes": []},
                            },
                            {
                                "id": "PVTI_format4",
                                "createdAt": "2023-01-01T00:00:00Z",
                                "updatedAt": "2023-01-02T00:00:00Z",
                                "content": {
                                    "title": "Invalid PRD format",
                                    "body": "**Parent PRD:** invalid_prd_id\n\nInvalid PRD format should NOT match",
                                    "createdAt": "2023-01-01T00:00:00Z",
                                    "updatedAt": "2023-01-02T00:00:00Z",
                                    "assignees": {"nodes": []},
                                },
                                "fieldValues": {"nodes": []},
                            },
                            {
                                "id": "PVTI_format5",
                                "createdAt": "2023-01-01T00:00:00Z",
                                "updatedAt": "2023-01-02T00:00:00Z",
                                "content": {
                                    "title": "Multiple line format",
                                    "body": "## Task Description\n\n**Parent PRD:** PVTI_test_prd\n\n**Details:**\nThis is a multiline description.",
                                    "createdAt": "2023-01-01T00:00:00Z",
                                    "updatedAt": "2023-01-02T00:00:00Z",
                                    "assignees": {"nodes": []},
                                },
                                "fieldValues": {"nodes": []},
                            },
                        ],
                    },
                }
            }
        }

        mock_github_client.query.return_value = varied_format_response

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            result = await list_tasks_handler(
                {
                    "project_id": "PVT_test123",
                    "parent_prd_id": "PVTI_test_prd",
                    "first": 10,
                }
            )

            assert not result.isError
            content = result.content[0].text

            # Should match valid formats
            assert "Standard format" in content
            assert "Extra spaces format" in content
            assert "Multiple line format" in content

            # Should NOT match invalid formats
            assert "Mixed case format" not in content  # Case sensitive
            assert "Invalid PRD format" not in content  # Invalid PVTI_ format

    @pytest.mark.asyncio
    async def test_pagination_with_prd_filtering_smart_fetch_size(
        self, mock_github_client, sample_mixed_project_response
    ):
        """Test that pagination works correctly with PRD filtering and smart fetch size optimization."""
        mock_github_client.query.return_value = sample_mixed_project_response

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            # Request small page size with PRD filtering (should trigger smart fetch optimization)
            result = await list_tasks_handler(
                {
                    "project_id": "PVT_test123",
                    "parent_prd_id": "PVTI_prd1",
                    "first": 1,  # Small size to trigger optimization
                }
            )

            assert not result.isError
            content = result.content[0].text

            # Should still limit results to requested size despite smart fetching
            import re

            task_matches = re.findall(r"## \d+\.", content)
            task_count = len(task_matches)
            assert (
                task_count == 1
            ), f"Expected 1 task due to first=1 limit, but found {task_count}"

            # Should include one of the PRD 1 tasks
            assert ("Implement login endpoint" in content) or (
                "Create password validation" in content
            )

    @pytest.mark.asyncio
    async def test_empty_project_with_prd_filtering(self, mock_github_client):
        """Test behavior when filtering by PRD in an empty project."""
        empty_response = {
            "data": {
                "node": {
                    "title": "Empty Project",
                    "items": {
                        "totalCount": 0,
                        "pageInfo": {"hasNextPage": False},
                        "nodes": [],
                    },
                }
            }
        }

        mock_github_client.query.return_value = empty_response

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            result = await list_tasks_handler(
                {
                    "project_id": "PVT_test123",
                    "parent_prd_id": "PVTI_any_prd",
                    "first": 10,
                }
            )

            assert not result.isError
            content = result.content[0].text

            # Should handle empty project gracefully
            assert "No tasks found" in content or "0 tasks found" in content

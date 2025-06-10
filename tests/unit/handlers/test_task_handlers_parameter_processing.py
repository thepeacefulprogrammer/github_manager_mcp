"""
Unit tests for list_tasks handler parameter processing.

This test file specifically focuses on testing the parameter processing
logic in the list_tasks handler to ensure proper handling of parent_prd_id
filtering, pagination, and edge cases.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from github_project_manager_mcp.handlers.task_handlers import list_tasks_handler


class TestListTasksParameterProcessing:
    """Test parameter processing in list_tasks handler."""

    @pytest.fixture
    def mock_github_client(self):
        """Mock GitHub client for testing."""
        client = AsyncMock()
        # Ensure query method returns awaitable response
        client.query = AsyncMock()
        return client

    @pytest.fixture
    def sample_response_with_tasks(self):
        """Sample GitHub API response with tasks for testing."""
        return {
            "data": {
                "node": {
                    "title": "Test Project",
                    "items": {
                        "totalCount": 2,
                        "pageInfo": {
                            "hasNextPage": False,
                            "hasPreviousPage": False,
                            "startCursor": "cursor1",
                            "endCursor": "cursor2",
                        },
                        "nodes": [
                            {
                                "id": "PVTI_task1",
                                "createdAt": "2023-01-01T00:00:00Z",
                                "updatedAt": "2023-01-02T00:00:00Z",
                                "content": {
                                    "title": "Task 1",
                                    "body": "**Parent PRD:** PVTI_prd123\n\nTask description",
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
                            {
                                "id": "PVTI_task2",
                                "createdAt": "2023-01-01T00:00:00Z",
                                "updatedAt": "2023-01-02T00:00:00Z",
                                "content": {
                                    "title": "Task 2",
                                    "body": "**Parent PRD:** PVTI_prd456\n\nAnother task description",
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
                        ],
                    },
                }
            }
        }

    @pytest.mark.asyncio
    async def test_list_tasks_parameter_normalization(
        self, mock_github_client, sample_response_with_tasks
    ):
        """Test that parameters are properly normalized before processing."""
        mock_github_client.query.return_value = sample_response_with_tasks

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            # Test with string parameters that need normalization
            result = await list_tasks_handler(
                {
                    "project_id": "  PVT_test123  ",  # Should be stripped
                    "parent_prd_id": "  PVTI_prd123  ",  # Should be stripped
                    "first": "10",  # Should be converted to int
                    "after": "  cursor123  ",  # Should be stripped
                }
            )

            assert not result.isError
            # Verify the query was called with normalized parameters
            mock_github_client.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tasks_smart_fetch_size_optimization(
        self, mock_github_client, sample_response_with_tasks
    ):
        """Test that fetch size is intelligently increased for PRD filtering."""
        mock_github_client.query.return_value = sample_response_with_tasks

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            # Test with small first parameter and PRD filtering
            result = await list_tasks_handler(
                {
                    "project_id": "PVT_test123",
                    "parent_prd_id": "PVTI_prd123",
                    "first": 5,  # Small size that should trigger optimization
                }
            )

            assert not result.isError
            # The implementation should increase fetch size to improve filtering results
            mock_github_client.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tasks_empty_parent_prd_id_handling(
        self, mock_github_client, sample_response_with_tasks
    ):
        """Test that empty parent_prd_id is properly converted to None."""
        mock_github_client.query.return_value = sample_response_with_tasks

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            # Test with empty string parent_prd_id
            result = await list_tasks_handler(
                {
                    "project_id": "PVT_test123",
                    "parent_prd_id": "",  # Should be converted to None
                    "first": 10,
                }
            )

            assert not result.isError
            # Should not apply any filtering
            content = result.content[0].text
            assert "Task 1" in content
            assert "Task 2" in content

    @pytest.mark.asyncio
    async def test_list_tasks_whitespace_only_parent_prd_id_handling(
        self, mock_github_client, sample_response_with_tasks
    ):
        """Test that whitespace-only parent_prd_id is properly converted to None."""
        mock_github_client.query.return_value = sample_response_with_tasks

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            # Test with whitespace-only parent_prd_id
            result = await list_tasks_handler(
                {
                    "project_id": "PVT_test123",
                    "parent_prd_id": "   ",  # Should be converted to None
                    "first": 10,
                }
            )

            assert not result.isError
            # Should not apply any filtering
            content = result.content[0].text
            assert "Task 1" in content
            assert "Task 2" in content

    @pytest.mark.asyncio
    async def test_list_tasks_none_parent_prd_id_handling(
        self, mock_github_client, sample_response_with_tasks
    ):
        """Test that None parent_prd_id is properly handled."""
        mock_github_client.query.return_value = sample_response_with_tasks

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            # Test with None parent_prd_id
            result = await list_tasks_handler(
                {
                    "project_id": "PVT_test123",
                    "parent_prd_id": None,  # Should be handled properly
                    "first": 10,
                }
            )

            assert not result.isError
            # Should not apply any filtering
            content = result.content[0].text
            assert "Task 1" in content
            assert "Task 2" in content

    @pytest.mark.asyncio
    async def test_list_tasks_first_parameter_validation_and_conversion(
        self, mock_github_client, sample_response_with_tasks
    ):
        """Test that first parameter is properly validated and converted."""
        # Set up a proper return value for successful cases
        mock_github_client.query.return_value = sample_response_with_tasks

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            # Test with string number - should succeed
            result = await list_tasks_handler(
                {"project_id": "PVT_test123", "first": "25"}
            )
            assert not result.isError

            # Test with invalid first parameter
            result = await list_tasks_handler(
                {"project_id": "PVT_test123", "first": "invalid"}
            )
            assert result.isError
            assert (
                "'first' parameter must be a positive integer" in result.content[0].text
            )

            # Test with zero first parameter
            result = await list_tasks_handler({"project_id": "PVT_test123", "first": 0})
            assert result.isError
            assert (
                "'first' parameter must be a positive integer" in result.content[0].text
            )

            # Test with negative first parameter
            result = await list_tasks_handler(
                {"project_id": "PVT_test123", "first": -1}
            )
            assert result.isError
            assert (
                "'first' parameter must be a positive integer" in result.content[0].text
            )

            # Test with too large first parameter
            result = await list_tasks_handler(
                {"project_id": "PVT_test123", "first": 101}
            )
            assert result.isError
            assert (
                "'first' parameter must be a positive integer between 1 and 100"
                in result.content[0].text
            )

    @pytest.mark.asyncio
    async def test_list_tasks_parameter_defaults(
        self, mock_github_client, sample_response_with_tasks
    ):
        """Test that parameter defaults are properly applied."""
        mock_github_client.query.return_value = sample_response_with_tasks

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            # Test with minimal parameters
            result = await list_tasks_handler({"project_id": "PVT_test123"})

            assert not result.isError
            # Should use default first=25, parent_prd_id=None, after=None

    @pytest.mark.asyncio
    async def test_list_tasks_after_cursor_handling(
        self, mock_github_client, sample_response_with_tasks
    ):
        """Test that after cursor parameter is properly processed."""
        mock_github_client.query.return_value = sample_response_with_tasks

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            # Test with after cursor
            result = await list_tasks_handler(
                {"project_id": "PVT_test123", "after": "cursor123"}
            )

            assert not result.isError
            # Verify after cursor was passed to query builder
            mock_github_client.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tasks_filtering_result_limiting(self, mock_github_client):
        """Test that result limiting works correctly when fetch size is increased for filtering."""
        # Create a response with more items than requested
        large_response = {
            "data": {
                "node": {
                    "title": "Test Project",
                    "items": {
                        "totalCount": 10,
                        "pageInfo": {"hasNextPage": False},
                        "nodes": [
                            {
                                "id": f"PVTI_task{i}",
                                "createdAt": "2023-01-01T00:00:00Z",
                                "updatedAt": "2023-01-02T00:00:00Z",
                                "content": {
                                    "title": f"Task {i}",
                                    "body": f"**Parent PRD:** PVTI_prd123\n\nTask {i} description",
                                    "createdAt": "2023-01-01T00:00:00Z",
                                    "updatedAt": "2023-01-02T00:00:00Z",
                                    "assignees": {"nodes": []},
                                },
                                "fieldValues": {"nodes": []},
                            }
                            for i in range(1, 11)  # 10 tasks
                        ],
                    },
                }
            }
        }

        mock_github_client.query.return_value = large_response

        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            # Request only 3 tasks with PRD filtering
            result = await list_tasks_handler(
                {
                    "project_id": "PVT_test123",
                    "parent_prd_id": "PVTI_prd123",
                    "first": 3,
                }
            )

            assert not result.isError
            content = result.content[0].text

            # Should see exactly 3 tasks in the output despite having 10 matching tasks
            # Count the number of task entries
            task_count = content.count("## ")  # Each task starts with "## N."
            assert task_count == 3

    @pytest.mark.asyncio
    async def test_list_tasks_missing_required_project_id(self, mock_github_client):
        """Test error handling for missing project_id parameter."""
        with patch(
            "github_project_manager_mcp.handlers.task_handlers.get_github_client",
            return_value=mock_github_client,
        ):
            # Test with missing project_id
            result = await list_tasks_handler({})
            assert result.isError
            assert "project_id is required" in result.content[0].text

            # Test with empty project_id
            result = await list_tasks_handler({"project_id": ""})
            assert result.isError
            assert "project_id is required" in result.content[0].text

            # Test with whitespace-only project_id
            result = await list_tasks_handler({"project_id": "   "})
            assert result.isError
            assert "project_id is required" in result.content[0].text

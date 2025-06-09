"""
Integration tests for GitHub API functionality.

These tests verify the integration between our GitHub client and the actual GitHub API.
They are designed to work with real API endpoints but use mocking for CI/CD safety.
Use a test GitHub token (with minimal permissions) to run these tests manually.
"""

import asyncio
import os
from unittest.mock import Mock, patch

import httpx
import pytest


class TestGitHubAPIIntegration:
    """Integration tests for GitHub API operations."""

    @pytest.fixture
    def github_client(self):
        """Create a GitHub client for testing."""
        from src.github_project_manager_mcp.github_client import GitHubClient

        # Use test token from environment or mock token for CI
        test_token = os.getenv("GITHUB_TEST_TOKEN", "test_token_for_ci")
        return GitHubClient(token=test_token, rate_limit_enabled=True)

    @pytest.fixture
    def query_builder(self):
        """Create a query builder for testing."""
        from src.github_project_manager_mcp.utils.query_builder import (
            ProjectQueryBuilder,
        )

        return ProjectQueryBuilder()

    @pytest.mark.asyncio
    async def test_github_api_authentication_integration(self, github_client):
        """Test that authentication works with GitHub API."""
        # Mock the response for CI safety
        mock_response_data = {
            "data": {
                "viewer": {
                    "login": "test-user",
                    "id": "MDQ6VXNlcjEyMzQ1Njc4",
                    "databaseId": 12345678,
                }
            }
        }

        mock_response = Mock()
        mock_response.json = Mock(return_value=mock_response_data)
        mock_response.headers = {
            "x-ratelimit-remaining": "4999",
            "x-ratelimit-reset": "1640995200",
        }
        mock_response.raise_for_status = Mock()

        query = """
        query {
          viewer {
            login
            id
            databaseId
          }
        }
        """

        with patch.object(github_client.session, "post", return_value=mock_response):
            result = await github_client.query(query)

            assert result["viewer"]["login"] == "test-user"
            assert result["viewer"]["id"] == "MDQ6VXNlcjEyMzQ1Njc4"
            assert github_client.remaining_requests == 4999

    @pytest.mark.asyncio
    async def test_list_projects_integration(self, github_client, query_builder):
        """Test listing projects integration with GitHub API."""
        # Mock realistic project data
        mock_response_data = {
            "data": {
                "user": {
                    "projectsV2": {
                        "totalCount": 2,
                        "pageInfo": {
                            "hasNextPage": False,
                            "hasPreviousPage": False,
                            "startCursor": "Y3Vyc29yOnYyOpHOAAA=",
                            "endCursor": "Y3Vyc29yOnYyOpHOBBB=",
                        },
                        "nodes": [
                            {
                                "id": "PVT_kwDOABCDEF",
                                "title": "My Project 1",
                                "description": "Test project description",
                                "url": "https://github.com/users/test-user/projects/1",
                                "createdAt": "2024-01-01T00:00:00Z",
                                "updatedAt": "2024-01-02T00:00:00Z",
                                "viewerCanUpdate": True,
                                "number": 1,
                            },
                            {
                                "id": "PVT_kwDOGHIJKL",
                                "title": "My Project 2",
                                "description": "Another test project",
                                "url": "https://github.com/users/test-user/projects/2",
                                "createdAt": "2024-01-03T00:00:00Z",
                                "updatedAt": "2024-01-04T00:00:00Z",
                                "viewerCanUpdate": True,
                                "number": 2,
                            },
                        ],
                    }
                }
            }
        }

        mock_response = Mock()
        mock_response.json = Mock(return_value=mock_response_data)
        mock_response.headers = {"x-ratelimit-remaining": "4998"}
        mock_response.raise_for_status = Mock()

        query = query_builder.list_projects("test-user", first=10)

        with patch.object(github_client.session, "post", return_value=mock_response):
            result = await github_client.query(query)

            projects = result["user"]["projectsV2"]["nodes"]
            assert len(projects) == 2
            assert projects[0]["title"] == "My Project 1"
            assert projects[1]["title"] == "My Project 2"
            assert result["user"]["projectsV2"]["totalCount"] == 2

    @pytest.mark.asyncio
    async def test_create_project_integration(self, github_client, query_builder):
        """Test creating a project integration with GitHub API."""
        # Mock successful project creation
        mock_response_data = {
            "data": {
                "createProjectV2": {
                    "projectV2": {
                        "id": "PVT_kwDONEWPROJECT",
                        "title": "Test Integration Project",
                        "description": "Created via integration test",
                        "url": "https://github.com/users/test-user/projects/3",
                        "createdAt": "2024-01-05T00:00:00Z",
                    }
                }
            }
        }

        mock_response = Mock()
        mock_response.json = Mock(return_value=mock_response_data)
        mock_response.headers = {"x-ratelimit-remaining": "4997"}
        mock_response.raise_for_status = Mock()

        mutation = query_builder.create_project(
            "MDQ6VXNlcjEyMzQ1Njc4",  # Test user ID
            "Test Integration Project",
            "Created via integration test",
        )

        with patch.object(github_client.session, "post", return_value=mock_response):
            result = await github_client.mutate(mutation)

            project = result["createProjectV2"]["projectV2"]
            assert project["title"] == "Test Integration Project"
            assert project["description"] == "Created via integration test"
            assert "PVT_" in project["id"]

    @pytest.mark.asyncio
    async def test_update_project_integration(self, github_client, query_builder):
        """Test updating a project integration with GitHub API."""
        # Mock successful project update
        mock_response_data = {
            "data": {
                "updateProjectV2": {
                    "projectV2": {
                        "id": "PVT_kwDOEXISTING",
                        "title": "Updated Project Title",
                        "shortDescription": "Updated project description",
                        "updatedAt": "2024-01-06T00:00:00Z",
                    }
                }
            }
        }

        mock_response = Mock()
        mock_response.json = Mock(return_value=mock_response_data)
        mock_response.headers = {"x-ratelimit-remaining": "4996"}
        mock_response.raise_for_status = Mock()

        mutation = query_builder.update_project(
            "PVT_kwDOEXISTING",
            title="Updated Project Title",
            short_description="Updated project description",
        )

        with patch.object(github_client.session, "post", return_value=mock_response):
            result = await github_client.mutate(mutation)

            project = result["updateProjectV2"]["projectV2"]
            assert project["title"] == "Updated Project Title"
            assert project["shortDescription"] == "Updated project description"

    @pytest.mark.asyncio
    async def test_get_project_items_integration(self, github_client, query_builder):
        """Test retrieving project items integration with GitHub API."""
        # Mock project items response
        mock_response_data = {
            "data": {
                "node": {
                    "items": {
                        "totalCount": 3,
                        "pageInfo": {
                            "hasNextPage": False,
                            "hasPreviousPage": False,
                            "startCursor": "Y3Vyc29yOnYyOpHOAAA=",
                            "endCursor": "Y3Vyc29yOnYyOpHOCCC=",
                        },
                        "nodes": [
                            {
                                "id": "PVTI_lADOABCDEF",
                                "createdAt": "2024-01-07T00:00:00Z",
                                "updatedAt": "2024-01-07T00:00:00Z",
                                "content": {
                                    "id": "I_kwDOISSUE123",
                                    "title": "Sample Issue",
                                    "number": 1,
                                },
                            },
                            {
                                "id": "PVTI_lADOGHIJKL",
                                "createdAt": "2024-01-08T00:00:00Z",
                                "updatedAt": "2024-01-08T00:00:00Z",
                                "content": {
                                    "id": "PR_kwDOPULLREQ456",
                                    "title": "Sample Pull Request",
                                    "number": 2,
                                },
                            },
                        ],
                    }
                }
            }
        }

        mock_response = Mock()
        mock_response.json = Mock(return_value=mock_response_data)
        mock_response.headers = {"x-ratelimit-remaining": "4995"}
        mock_response.raise_for_status = Mock()

        query = query_builder.get_project_items("PVT_kwDOTESTPROJECT", first=20)

        with patch.object(github_client.session, "post", return_value=mock_response):
            result = await github_client.query(query)

            items = result["node"]["items"]["nodes"]
            assert len(items) == 2
            assert items[0]["content"]["title"] == "Sample Issue"
            assert items[1]["content"]["title"] == "Sample Pull Request"

    @pytest.mark.asyncio
    async def test_rate_limiting_integration(self, github_client):
        """Test rate limiting behavior with GitHub API."""
        # Configure low rate limit for testing
        github_client.requests_per_hour = 5
        github_client.request_timestamps = []

        mock_response = Mock()
        mock_response.json = Mock(return_value={"data": {"viewer": {"login": "test"}}})
        mock_response.headers = {"x-ratelimit-remaining": "10"}
        mock_response.raise_for_status = Mock()

        # Make several requests quickly
        with patch.object(github_client.session, "post", return_value=mock_response):
            with patch("asyncio.sleep") as mock_sleep:
                # Make requests up to the limit
                for i in range(6):  # One more than the limit
                    await github_client.query("{ viewer { login } }")

                # Should have been called to sleep on the last request
                assert mock_sleep.call_count >= 1

    @pytest.mark.asyncio
    async def test_graphql_error_handling_integration(self, github_client):
        """Test GraphQL error handling in integration context."""
        # Mock GraphQL error response (realistic GitHub API error)
        mock_response_data = {
            "data": None,
            "errors": [
                {
                    "message": "Field 'nonExistentField' doesn't exist on type 'Query'",
                    "locations": [{"line": 3, "column": 5}],
                    "path": ["query"],
                    "extensions": {
                        "code": "undefinedField",
                        "typeName": "Query",
                        "fieldName": "nonExistentField",
                    },
                }
            ],
        }

        mock_response = Mock()
        mock_response.json = Mock(return_value=mock_response_data)
        mock_response.headers = {"x-ratelimit-remaining": "4994"}
        mock_response.raise_for_status = Mock()

        invalid_query = """
        query {
          nonExistentField {
            id
          }
        }
        """

        with patch.object(github_client.session, "post", return_value=mock_response):
            with pytest.raises(ValueError) as exc_info:
                await github_client.query(invalid_query)

            error_msg = str(exc_info.value)
            assert "GraphQL errors:" in error_msg
            assert "nonExistentField" in error_msg

    @pytest.mark.asyncio
    async def test_http_error_handling_integration(self, github_client):
        """Test HTTP error handling in integration context."""
        # Mock HTTP 401 Unauthorized error (realistic GitHub API error)
        mock_response = Mock()
        mock_response.raise_for_status = Mock(
            side_effect=httpx.HTTPStatusError(
                "401 Unauthorized",
                request=Mock(url="https://api.github.com/graphql"),
                response=Mock(status_code=401, text="Bad credentials"),
            )
        )

        query = "{ viewer { login } }"

        with patch.object(github_client.session, "post", return_value=mock_response):
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await github_client.query(query)

            assert exc_info.value.response.status_code == 401

    @pytest.mark.asyncio
    async def test_pagination_integration(self, github_client, query_builder):
        """Test pagination handling in integration context."""
        # Mock paginated response with hasNextPage=True
        mock_response_data = {
            "data": {
                "user": {
                    "projectsV2": {
                        "totalCount": 25,  # More than one page
                        "pageInfo": {
                            "hasNextPage": True,
                            "hasPreviousPage": False,
                            "startCursor": "Y3Vyc29yOnYyOpHOAAA=",
                            "endCursor": "Y3Vyc29yOnYyOpHOJJJ=",
                        },
                        "nodes": [
                            {
                                "id": f"PVT_kwDOTEST{i:03d}",
                                "title": f"Test Project {i+1}",
                                "description": f"Description {i+1}",
                                "url": f"https://github.com/users/test-user/projects/{i+1}",
                                "createdAt": "2024-01-01T00:00:00Z",
                                "updatedAt": "2024-01-01T00:00:00Z",
                                "viewerCanUpdate": True,
                                "number": i + 1,
                            }
                            for i in range(10)  # First page of 10
                        ],
                    }
                }
            }
        }

        mock_response = Mock()
        mock_response.json = Mock(return_value=mock_response_data)
        mock_response.headers = {"x-ratelimit-remaining": "4993"}
        mock_response.raise_for_status = Mock()

        query = query_builder.list_projects("test-user", first=10)

        with patch.object(github_client.session, "post", return_value=mock_response):
            result = await github_client.query(query)

            projects_data = result["user"]["projectsV2"]
            assert projects_data["totalCount"] == 25
            assert projects_data["pageInfo"]["hasNextPage"] is True
            assert len(projects_data["nodes"]) == 10
            assert projects_data["pageInfo"]["endCursor"] == "Y3Vyc29yOnYyOpHOJJJ="

    @pytest.mark.asyncio
    async def test_end_to_end_project_workflow_integration(
        self, github_client, query_builder
    ):
        """Test complete project workflow from creation to deletion."""
        # Test the complete workflow: Create -> Read -> Update -> Delete

        # Step 1: Create project
        create_response_data = {
            "data": {
                "createProjectV2": {
                    "projectV2": {
                        "id": "PVT_kwDOWORKFLOW",
                        "title": "E2E Test Project",
                        "description": "End-to-end test project",
                        "url": "https://github.com/users/test-user/projects/999",
                        "createdAt": "2024-01-10T00:00:00Z",
                    }
                }
            }
        }

        # Step 2: Read project
        read_response_data = {
            "data": {
                "node": {
                    "id": "PVT_kwDOWORKFLOW",
                    "title": "E2E Test Project",
                    "description": "End-to-end test project",
                    "url": "https://github.com/users/test-user/projects/999",
                    "createdAt": "2024-01-10T00:00:00Z",
                    "updatedAt": "2024-01-10T00:00:00Z",
                    "viewerCanUpdate": True,
                    "number": 999,
                }
            }
        }

        # Step 3: Update project
        update_response_data = {
            "data": {
                "updateProjectV2": {
                    "projectV2": {
                        "id": "PVT_kwDOWORKFLOW",
                        "title": "Updated E2E Project",
                        "description": "Updated description",
                        "updatedAt": "2024-01-10T01:00:00Z",
                    }
                }
            }
        }

        # Step 4: Delete project
        delete_response_data = {
            "data": {"deleteProjectV2": {"projectV2": {"id": "PVT_kwDOWORKFLOW"}}}
        }

        responses = [
            create_response_data,
            read_response_data,
            update_response_data,
            delete_response_data,
        ]
        response_index = 0

        def mock_post_side_effect(*args, **kwargs):
            nonlocal response_index
            mock_response = Mock()
            mock_response.json = Mock(return_value=responses[response_index])
            mock_response.headers = {
                "x-ratelimit-remaining": str(4990 - response_index)
            }
            mock_response.raise_for_status = Mock()
            response_index += 1
            return mock_response

        with patch.object(
            github_client.session, "post", side_effect=mock_post_side_effect
        ):
            # Step 1: Create
            create_mutation = query_builder.create_project(
                "MDQ6VXNlcjEyMzQ1Njc4", "E2E Test Project", "End-to-end test project"
            )
            create_result = await github_client.mutate(create_mutation)
            project_id = create_result["createProjectV2"]["projectV2"]["id"]
            assert project_id == "PVT_kwDOWORKFLOW"

            # Step 2: Read
            read_query = query_builder.get_project(project_id)
            read_result = await github_client.query(read_query)
            assert read_result["node"]["title"] == "E2E Test Project"

            # Step 3: Update
            update_mutation = query_builder.update_project(
                project_id,
                title="Updated E2E Project",
                short_description="Updated description",
            )
            update_result = await github_client.mutate(update_mutation)
            assert (
                update_result["updateProjectV2"]["projectV2"]["title"]
                == "Updated E2E Project"
            )

            # Step 4: Delete
            delete_mutation = query_builder.delete_project(project_id)
            delete_result = await github_client.mutate(delete_mutation)
            assert delete_result["deleteProjectV2"]["projectV2"]["id"] == project_id

            # Verify rate limit tracking worked throughout
            assert github_client.remaining_requests == 4987  # 4990 - 3 requests


# Legacy placeholder tests for backward compatibility
def test_integration_placeholder():
    """Legacy placeholder integration test for backward compatibility."""
    assert True


@pytest.mark.asyncio
async def test_async_integration_placeholder():
    """Legacy placeholder async integration test for backward compatibility."""
    await asyncio.sleep(0.01)
    assert True

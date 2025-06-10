"""
Unit tests for PRD completion GraphQL query structure fixes.

This module tests the complete_prd handler's GraphQL query structure to ensure
it uses the correct field names for GitHub Projects v2 API.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from github_project_manager_mcp.handlers.prd_handlers import complete_prd_handler


class TestPRDCompleteGraphQLFix:
    """Tests for PRD completion GraphQL query structure fixes."""

    @pytest.mark.asyncio
    async def test_complete_prd_graphql_field_structure(self):
        """
        Test that complete_prd handler uses correct GraphQL field structure.

        This test exposes the issue where the GraphQL query uses 'singleSelectOption'
        which doesn't exist on type 'ProjectV2ItemFieldSingleSelectValue'. The correct
        field should be 'name'.
        """
        # Mock GitHub client
        mock_client = Mock()
        mock_query_call = AsyncMock()
        mock_mutate_call = AsyncMock()
        mock_client.query = mock_query_call
        mock_client.mutate = mock_mutate_call

        # Mock successful query response with correct field structure
        mock_query_response = {
            "node": {
                "id": "PVTI_test123",
                "project": {
                    "id": "PVT_project123",
                    "fields": {
                        "nodes": [
                            {
                                "id": "FIELD_STATUS_ID",
                                "name": "Status",
                                "dataType": "SINGLE_SELECT",
                                "options": [
                                    {"id": "OPT_BACKLOG", "name": "Backlog"},
                                    {"id": "OPT_IN_PROGRESS", "name": "In Progress"},
                                    {"id": "OPT_DONE", "name": "Done"},
                                ],
                            },
                        ]
                    },
                },
                "fieldValues": {
                    "nodes": [
                        {
                            "field": {"name": "Status"},
                            "optionId": "OPT_IN_PROGRESS",
                            "name": "In Progress",  # Correct API structure
                        }
                    ]
                },
            }
        }

        # Mock successful mutation response
        mock_mutation_response = {
            "updateProjectV2ItemFieldValue": {
                "projectV2Item": {
                    "id": "PVTI_test123",
                    "fieldValues": {
                        "nodes": [
                            {
                                "field": {"name": "Status"},
                                "optionId": "OPT_DONE",
                                "name": "Done",  # Correct API structure
                            }
                        ]
                    },
                }
            }
        }

        mock_query_call.return_value = mock_query_response
        mock_mutate_call.return_value = mock_mutation_response

        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            # Execute the handler
            result = await complete_prd_handler({"prd_item_id": "PVTI_test123"})

            # Verify the result
            assert not result.isError
            assert "PRD completed successfully" in result.content[0].text

            # Verify the GraphQL query structure
            assert mock_query_call.called
            query_call_args = mock_query_call.call_args[0][0]

            # The query should NOT contain 'singleSelectOption' field
            assert "singleSelectOption" not in query_call_args, (
                "GraphQL query contains 'singleSelectOption' field which doesn't exist "
                "on type 'ProjectV2ItemFieldSingleSelectValue'. Use 'name' instead."
            )

            # The query should contain the correct 'name' field
            assert "name" in query_call_args

            # Verify mutation was called
            assert mock_mutate_call.called
            mutation_call_args = mock_mutate_call.call_args[0][0]

            # The mutation should not contain the incorrect nested 'singleSelectOption' structure in response fields
            assert "singleSelectOption {" not in mutation_call_args

    @pytest.mark.asyncio
    async def test_complete_prd_field_value_access_logic(self):
        """
        Test that the PRD completion logic correctly accesses field values using 'name'.

        This test ensures that the field value processing logic uses the correct
        API structure to access the status value.
        """
        mock_client = Mock()
        mock_query_call = AsyncMock()
        mock_mutate_call = AsyncMock()
        mock_client.query = mock_query_call
        mock_client.mutate = mock_mutate_call

        # Mock response with PRD already complete - this tests the field access logic
        mock_query_response = {
            "node": {
                "id": "PVTI_test123",
                "project": {
                    "id": "PVT_project123",
                    "fields": {
                        "nodes": [
                            {
                                "id": "FIELD_STATUS_ID",
                                "name": "Status",
                                "dataType": "SINGLE_SELECT",
                                "options": [
                                    {"id": "OPT_DONE", "name": "Done"},
                                ],
                            },
                        ]
                    },
                },
                "fieldValues": {
                    "nodes": [
                        {
                            "field": {"name": "Status"},
                            "optionId": "OPT_DONE",
                            "name": "Done",  # Direct 'name' field, not nested in 'singleSelectOption'
                        }
                    ]
                },
            }
        }

        mock_query_call.return_value = mock_query_response

        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            # Execute the handler
            result = await complete_prd_handler({"prd_item_id": "PVTI_test123"})

            # Verify the result - should detect that PRD is already complete
            assert not result.isError
            assert "PRD is already complete" in result.content[0].text
            assert "Status:** Done" in result.content[0].text

            # Mutation should NOT have been called since PRD was already complete
            assert not mock_mutate_call.called

    @pytest.mark.asyncio
    async def test_complete_prd_backward_compatibility(self):
        """
        Test that the handler gracefully handles legacy API responses.

        While the GraphQL queries use the correct structure, this tests that
        if somehow a legacy response is received, it's handled appropriately.
        """
        mock_client = Mock()
        mock_query_call = AsyncMock()
        mock_mutate_call = AsyncMock()
        mock_client.query = mock_query_call
        mock_client.mutate = mock_mutate_call

        # Mock response with missing status field (edge case)
        mock_query_response = {
            "node": {
                "id": "PVTI_test123",
                "project": {
                    "id": "PVT_project123",
                    "fields": {
                        "nodes": [
                            {
                                "id": "FIELD_STATUS_ID",
                                "name": "Status",
                                "dataType": "SINGLE_SELECT",
                                "options": [
                                    {"id": "OPT_DONE", "name": "Done"},
                                ],
                            },
                        ]
                    },
                },
                "fieldValues": {"nodes": []},  # No field values present
            }
        }

        mock_mutation_response = {
            "updateProjectV2ItemFieldValue": {
                "projectV2Item": {
                    "id": "PVTI_test123",
                    "fieldValues": {
                        "nodes": [
                            {
                                "field": {"name": "Status"},
                                "optionId": "OPT_DONE",
                                "name": "Done",
                            }
                        ]
                    },
                }
            }
        }

        mock_query_call.return_value = mock_query_response
        mock_mutate_call.return_value = mock_mutation_response

        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            # Execute the handler
            result = await complete_prd_handler({"prd_item_id": "PVTI_test123"})

            # Should successfully complete the PRD even with missing current status
            assert not result.isError
            assert "PRD completed successfully" in result.content[0].text

    @pytest.mark.asyncio
    async def test_complete_prd_missing_status_field_error(self):
        """
        Test error handling when Status field is not found in project.
        """
        mock_client = Mock()
        mock_query_call = AsyncMock()
        mock_client.query = mock_query_call

        # Mock response with no Status field in project
        mock_query_response = {
            "node": {
                "id": "PVTI_test123",
                "project": {
                    "id": "PVT_project123",
                    "fields": {
                        "nodes": [
                            {
                                "id": "FIELD_PRIORITY_ID",
                                "name": "Priority",  # Different field, not Status
                                "dataType": "SINGLE_SELECT",
                                "options": [
                                    {"id": "OPT_HIGH", "name": "High"},
                                ],
                            },
                        ]
                    },
                },
                "fieldValues": {"nodes": []},
            }
        }

        mock_query_call.return_value = mock_query_response

        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            # Execute the handler
            result = await complete_prd_handler({"prd_item_id": "PVTI_test123"})

            # Should return error about missing Status field
            assert result.isError
            assert "Status field not found" in result.content[0].text

    @pytest.mark.asyncio
    async def test_complete_prd_query_structure_validation(self):
        """
        Test that the GraphQL queries contain all required fields with correct structure.
        """
        mock_client = Mock()
        mock_query_call = AsyncMock()
        mock_mutate_call = AsyncMock()
        mock_client.query = mock_query_call
        mock_client.mutate = mock_mutate_call

        # Mock minimal successful response
        mock_query_response = {
            "node": {
                "id": "PVTI_test123",
                "project": {
                    "id": "PVT_project123",
                    "fields": {
                        "nodes": [
                            {
                                "id": "FIELD_STATUS_ID",
                                "name": "Status",
                                "dataType": "SINGLE_SELECT",
                                "options": [
                                    {"id": "OPT_IN_PROGRESS", "name": "In Progress"},
                                    {"id": "OPT_DONE", "name": "Done"},
                                ],
                            },
                        ]
                    },
                },
                "fieldValues": {
                    "nodes": [
                        {
                            "field": {"name": "Status"},
                            "optionId": "OPT_IN_PROGRESS",
                            "name": "In Progress",
                        }
                    ]
                },
            }
        }

        mock_mutation_response = {
            "updateProjectV2ItemFieldValue": {
                "projectV2Item": {
                    "id": "PVTI_test123",
                    "fieldValues": {
                        "nodes": [
                            {
                                "field": {"name": "Status"},
                                "optionId": "OPT_DONE",
                                "name": "Done",
                            }
                        ]
                    },
                }
            }
        }

        mock_query_call.return_value = mock_query_response
        mock_mutate_call.return_value = mock_mutation_response

        with patch(
            "github_project_manager_mcp.handlers.prd_handlers.get_github_client",
            return_value=mock_client,
        ):
            # Execute the handler
            result = await complete_prd_handler({"prd_item_id": "PVTI_test123"})

            # Verify success
            assert not result.isError

            # Validate query structure
            query_str = mock_query_call.call_args[0][0]

            # Must contain correct field structure for single select values
            assert "... on ProjectV2ItemFieldSingleSelectValue" in query_str
            assert "optionId" in query_str
            assert "name" in query_str

            # Must NOT contain the incorrect field structure
            assert "singleSelectOption {" not in query_str

            # Validate mutation structure
            mutation_str = mock_mutate_call.call_args[0][0]

            # Mutation should correctly use singleSelectOptionId for the value
            assert "singleSelectOptionId:" in mutation_str

            # But the response fields should use 'name' not 'singleSelectOption'
            assert "singleSelectOption {" not in mutation_str

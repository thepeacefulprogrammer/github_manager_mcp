"""
Unit tests for status column handlers.

This module contains comprehensive tests for managing status columns (single select fields)
in GitHub Projects v2 through MCP tool handlers.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.github_project_manager_mcp.handlers.status_column_handlers import (
    create_status_column_handler,
    delete_status_column_handler,
    get_status_column_handler,
    list_status_columns_handler,
    update_status_column_handler,
)
from src.github_project_manager_mcp.models.status_column import (
    StatusColumn,
    StatusColumnOption,
)


class TestCreateStatusColumnHandler:
    """Tests for create_status_column_handler."""

    @pytest.mark.asyncio
    async def test_create_status_column_success(self):
        """Test successful status column creation."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.execute_query.return_value = {
            "createProjectV2Field": {
                "projectV2Field": {
                    "__typename": "ProjectV2SingleSelectField",
                    "id": "PVTSSF_test123",
                    "name": "Priority",
                    "dataType": "SINGLE_SELECT",
                    "options": [
                        {"id": "opt1", "name": "High"},
                        {"id": "opt2", "name": "Medium"},
                        {"id": "opt3", "name": "Low"},
                    ],
                }
            }
        }

        # Act
        result = await create_status_column_handler(
            client=mock_client,
            project_id="PVT_test123",
            name="Priority",
            options=["High", "Medium", "Low"],
        )

        # Assert
        assert result["success"] is True
        assert "status_column" in result
        status_column = result["status_column"]
        assert status_column["id"] == "PVTSSF_test123"
        assert status_column["name"] == "Priority"
        assert len(status_column["options"]) == 3
        assert status_column["options"][0]["name"] == "High"

    @pytest.mark.asyncio
    async def test_create_status_column_duplicate_name(self):
        """Test creating status column with duplicate name fails."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.execute_query.side_effect = Exception(
            "A field with this name already exists"
        )

        # Act & Assert
        with pytest.raises(
            ValueError,
            match="A field with the name 'Status' already exists in this project",
        ):
            await create_status_column_handler(
                client=mock_client,
                project_id="PVT_test123",
                name="Status",
                options=["Todo", "In Progress", "Done"],
            )

    @pytest.mark.asyncio
    async def test_create_status_column_invalid_project(self):
        """Test creating status column with invalid project ID fails."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.execute_query.side_effect = Exception(
            "Could not resolve to ProjectV2 node"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid project ID: invalid_project_id"):
            await create_status_column_handler(
                client=mock_client,
                project_id="invalid_project_id",
                name="Priority",
                options=["High", "Low"],
            )

    @pytest.mark.asyncio
    async def test_create_status_column_empty_options(self):
        """Test creating status column with empty options fails."""
        # Arrange
        mock_client = AsyncMock()

        # Act & Assert
        with pytest.raises(ValueError, match="At least one option is required"):
            await create_status_column_handler(
                client=mock_client,
                project_id="PVT_test123",
                name="Priority",
                options=[],
            )

    @pytest.mark.asyncio
    async def test_create_status_column_too_many_options(self):
        """Test creating status column with too many options fails."""
        # Arrange
        mock_client = AsyncMock()
        options = [f"Option{i}" for i in range(51)]  # 51 options, limit is 50

        # Act & Assert
        with pytest.raises(ValueError, match="Maximum 50 options allowed"):
            await create_status_column_handler(
                client=mock_client,
                project_id="PVT_test123",
                name="Priority",
                options=options,
            )


class TestListStatusColumnsHandler:
    """Tests for list_status_columns_handler."""

    @pytest.mark.asyncio
    async def test_list_status_columns_success(self):
        """Test successful listing of status columns."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.execute_query.return_value = {
            "node": {
                "fields": {
                    "nodes": [
                        {
                            "__typename": "ProjectV2SingleSelectField",
                            "id": "PVTSSF_status123",
                            "name": "Status",
                            "dataType": "SINGLE_SELECT",
                            "options": [
                                {"id": "opt1", "name": "Todo"},
                                {"id": "opt2", "name": "In Progress"},
                                {"id": "opt3", "name": "Done"},
                            ],
                        },
                        {
                            "__typename": "ProjectV2SingleSelectField",
                            "id": "PVTSSF_priority123",
                            "name": "Priority",
                            "dataType": "SINGLE_SELECT",
                            "options": [
                                {"id": "opt4", "name": "High"},
                                {"id": "opt5", "name": "Low"},
                            ],
                        },
                        {
                            "__typename": "ProjectV2Field",
                            "id": "PVTF_text123",
                            "name": "Description",
                        },
                    ]
                }
            }
        }

        # Act
        result = await list_status_columns_handler(
            client=mock_client, project_id="PVT_test123"
        )

        # Assert
        assert result["success"] is True
        assert "status_columns" in result
        status_columns = result["status_columns"]
        assert len(status_columns) == 2  # Only single select fields
        assert status_columns[0]["name"] == "Status"
        assert len(status_columns[0]["options"]) == 3
        assert status_columns[1]["name"] == "Priority"
        assert len(status_columns[1]["options"]) == 2

    @pytest.mark.asyncio
    async def test_list_status_columns_empty_project(self):
        """Test listing status columns for project with no single select fields."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.execute_query.return_value = {"node": {"fields": {"nodes": []}}}

        # Act
        result = await list_status_columns_handler(
            client=mock_client, project_id="PVT_test123"
        )

        # Assert
        assert result["success"] is True
        assert result["status_columns"] == []

    @pytest.mark.asyncio
    async def test_list_status_columns_invalid_project(self):
        """Test listing status columns with invalid project ID."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.execute_query.side_effect = Exception(
            "Could not resolve to ProjectV2 node"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid project ID: invalid_project_id"):
            await list_status_columns_handler(
                client=mock_client, project_id="invalid_project_id"
            )


class TestUpdateStatusColumnHandler:
    """Tests for update_status_column_handler."""

    @pytest.mark.asyncio
    async def test_update_status_column_add_option(self):
        """Test successfully adding an option to a status column."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.execute_query.return_value = {
            "updateProjectV2Field": {
                "projectV2Field": {
                    "__typename": "ProjectV2SingleSelectField",
                    "id": "PVTSSF_status123",
                    "name": "Status",
                    "dataType": "SINGLE_SELECT",
                    "options": [
                        {"id": "opt1", "name": "Todo"},
                        {"id": "opt2", "name": "In Progress"},
                        {"id": "opt3", "name": "Done"},
                        {"id": "opt4", "name": "Cancelled"},
                    ],
                }
            }
        }

        # Act
        result = await update_status_column_handler(
            client=mock_client,
            project_id="PVT_test123",
            field_id="PVTSSF_status123",
            options=["Todo", "In Progress", "Done", "Cancelled"],
        )

        # Assert
        assert result["success"] is True
        assert len(result["status_column"]["options"]) == 4
        assert result["status_column"]["options"][3]["name"] == "Cancelled"

    @pytest.mark.asyncio
    async def test_update_status_column_rename_option(self):
        """Test successfully renaming an option in a status column."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.execute_query.return_value = {
            "updateProjectV2Field": {
                "projectV2Field": {
                    "__typename": "ProjectV2SingleSelectField",
                    "id": "PVTSSF_status123",
                    "name": "Status",
                    "dataType": "SINGLE_SELECT",
                    "options": [
                        {"id": "opt1", "name": "Backlog"},
                        {"id": "opt2", "name": "In Progress"},
                        {"id": "opt3", "name": "Done"},
                    ],
                }
            }
        }

        # Act
        result = await update_status_column_handler(
            client=mock_client,
            project_id="PVT_test123",
            field_id="PVTSSF_status123",
            options=["Backlog", "In Progress", "Done"],
        )

        # Assert
        assert result["success"] is True
        assert result["status_column"]["options"][0]["name"] == "Backlog"

    @pytest.mark.asyncio
    async def test_update_status_column_invalid_field(self):
        """Test updating with invalid field ID fails."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.execute_query.side_effect = Exception(
            "Could not resolve to ProjectV2Field node"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid field ID"):
            await update_status_column_handler(
                client=mock_client,
                project_id="PVT_test123",
                field_id="invalid_field_id",
                options=["Option1", "Option2"],
            )

    @pytest.mark.asyncio
    async def test_update_status_column_empty_options(self):
        """Test updating with empty options fails."""
        # Arrange
        mock_client = AsyncMock()

        # Act & Assert
        with pytest.raises(ValueError, match="At least one option is required"):
            await update_status_column_handler(
                client=mock_client,
                project_id="PVT_test123",
                field_id="PVTSSF_status123",
                options=[],
            )


class TestDeleteStatusColumnHandler:
    """Tests for delete_status_column_handler."""

    @pytest.mark.asyncio
    async def test_delete_status_column_success(self):
        """Test successful status column deletion."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.execute_query.return_value = {
            "deleteProjectV2Field": {"deletedFieldId": "PVTSSF_priority123"}
        }

        # Act
        result = await delete_status_column_handler(
            client=mock_client,
            project_id="PVT_test123",
            field_id="PVTSSF_priority123",
            confirm=True,
        )

        # Assert
        assert result["success"] is True
        assert result["deleted_field_id"] == "PVTSSF_priority123"

    @pytest.mark.asyncio
    async def test_delete_status_column_without_confirmation(self):
        """Test deleting status column without confirmation fails."""
        # Arrange
        mock_client = AsyncMock()

        # Act & Assert
        with pytest.raises(ValueError, match="Deletion must be confirmed"):
            await delete_status_column_handler(
                client=mock_client,
                project_id="PVT_test123",
                field_id="PVTSSF_priority123",
                confirm=False,
            )

    @pytest.mark.asyncio
    async def test_delete_default_status_field_fails(self):
        """Test deleting the default Status field fails."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.execute_query.side_effect = Exception(
            "Cannot delete the default Status field"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot delete the default Status field"):
            await delete_status_column_handler(
                client=mock_client,
                project_id="PVT_test123",
                field_id="PVTSSF_default_status",
                confirm=True,
            )

    @pytest.mark.asyncio
    async def test_delete_status_column_invalid_field(self):
        """Test deleting with invalid field ID fails."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.execute_query.side_effect = Exception(
            "Could not resolve to ProjectV2Field node"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid field ID"):
            await delete_status_column_handler(
                client=mock_client,
                project_id="PVT_test123",
                field_id="invalid_field_id",
                confirm=True,
            )


class TestGetStatusColumnHandler:
    """Tests for get_status_column_handler."""

    @pytest.mark.asyncio
    async def test_get_status_column_success(self):
        """Test successful retrieval of a status column."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.execute_query.return_value = {
            "node": {
                "__typename": "ProjectV2SingleSelectField",
                "id": "PVTSSF_status123",
                "name": "Status",
                "dataType": "SINGLE_SELECT",
                "options": [
                    {"id": "opt1", "name": "Todo"},
                    {"id": "opt2", "name": "In Progress"},
                    {"id": "opt3", "name": "Done"},
                ],
            }
        }

        # Act
        result = await get_status_column_handler(
            client=mock_client,
            project_id="PVT_test123",
            field_id="PVTSSF_status123",
        )

        # Assert
        assert result["success"] is True
        assert "status_column" in result
        status_column = result["status_column"]
        assert status_column["id"] == "PVTSSF_status123"
        assert status_column["name"] == "Status"
        assert len(status_column["options"]) == 3

    @pytest.mark.asyncio
    async def test_get_status_column_invalid_field(self):
        """Test retrieving with invalid field ID fails."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.execute_query.side_effect = Exception(
            "Could not resolve to ProjectV2Field node"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid field ID"):
            await get_status_column_handler(
                client=mock_client,
                project_id="PVT_test123",
                field_id="invalid_field_id",
            )

    @pytest.mark.asyncio
    async def test_get_status_column_not_single_select(self):
        """Test retrieving a field that is not a single select field fails."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.execute_query.return_value = {
            "node": {
                "__typename": "ProjectV2Field",
                "id": "PVTF_text123",
                "name": "Description",
            }
        }

        # Act & Assert
        with pytest.raises(ValueError, match="Field is not a single select field"):
            await get_status_column_handler(
                client=mock_client,
                project_id="PVT_test123",
                field_id="PVTF_text123",
            )

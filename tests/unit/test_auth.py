"""
Unit tests for GitHub authentication utilities.
"""

import os
from unittest.mock import mock_open, patch

import pytest


class TestGitHubAuth:
    """Test suite for GitHub authentication handling."""

    def test_load_token_from_env_variable(self):
        """Test loading GitHub token from environment variable."""
        from src.github_project_manager_mcp.utils.auth import load_github_token

        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token_123"}):
            token = load_github_token()
            assert token == "test_token_123"

    def test_load_token_from_env_file(self):
        """Test loading GitHub token from .env file."""
        from src.github_project_manager_mcp.utils.auth import load_github_token

        env_content = "GITHUB_TOKEN=env_file_token_456\nOTHER_VAR=value"

        with patch("builtins.open", mock_open(read_data=env_content)):
            with patch("os.path.exists", return_value=True):
                with patch.dict(os.environ, {}, clear=True):
                    token = load_github_token()
                    assert token == "env_file_token_456"

    def test_load_token_env_variable_takes_precedence(self):
        """Test that environment variable takes precedence over .env file."""
        from src.github_project_manager_mcp.utils.auth import load_github_token

        env_content = "GITHUB_TOKEN=env_file_token"

        with patch("builtins.open", mock_open(read_data=env_content)):
            with patch("os.path.exists", return_value=True):
                with patch.dict(os.environ, {"GITHUB_TOKEN": "env_var_token"}):
                    token = load_github_token()
                    assert token == "env_var_token"

    def test_load_token_returns_none_when_not_found(self):
        """Test that load_github_token returns None when no token found."""
        from src.github_project_manager_mcp.utils.auth import load_github_token

        with patch("os.path.exists", return_value=False):
            with patch.dict(os.environ, {}, clear=True):
                token = load_github_token()
                assert token is None

    def test_validate_token_format_valid_classic_token(self):
        """Test validation of valid classic GitHub token format."""
        from src.github_project_manager_mcp.utils.auth import validate_token_format

        # Classic GitHub token format (ghp_...)
        valid_token = "ghp_" + "a" * 36
        assert validate_token_format(valid_token) is True

    def test_validate_token_format_valid_fine_grained_token(self):
        """Test validation of valid fine-grained GitHub token format."""
        from src.github_project_manager_mcp.utils.auth import validate_token_format

        # Fine-grained GitHub token format (github_pat_11chars_82chars)
        valid_token = "github_pat_" + "a" * 11 + "_" + "b" * 82
        assert validate_token_format(valid_token) is True

    def test_validate_token_format_invalid_token(self):
        """Test validation of invalid GitHub token formats."""
        from src.github_project_manager_mcp.utils.auth import validate_token_format

        invalid_tokens = [
            "",
            "invalid_token",
            "ghp_tooshort",
            "ghp_" + "a" * 50,  # Too long
            "github_pat_tooshort",
            "wrong_prefix_" + "a" * 36,
            None,
        ]

        for token in invalid_tokens:
            assert validate_token_format(token) is False

    @pytest.mark.asyncio
    async def test_verify_token_with_github_api_success(self):
        """Test successful token verification with GitHub API."""
        from src.github_project_manager_mcp.utils.auth import verify_token_with_github

        # Mock successful API response
        mock_response_data = {
            "data": {"viewer": {"login": "testuser", "id": "MDQ6VXNlcjEyMzQ1Njc4"}}
        }

        with patch(
            "src.github_project_manager_mcp.utils.auth.GitHubClient"
        ) as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.query.return_value = mock_response_data["data"]

            result = await verify_token_with_github("valid_token")

            assert result is True

    @pytest.mark.asyncio
    async def test_verify_token_with_github_api_failure(self):
        """Test failed token verification with GitHub API."""
        from src.github_project_manager_mcp.utils.auth import verify_token_with_github

        with patch(
            "src.github_project_manager_mcp.utils.auth.GitHubClient"
        ) as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.query.side_effect = ValueError(
                "GraphQL errors: Bad credentials"
            )

            result = await verify_token_with_github("invalid_token")

            assert result is False

    def test_get_authenticated_client_with_valid_token(self):
        """Test getting authenticated client with valid token."""
        from src.github_project_manager_mcp.utils.auth import get_authenticated_client

        # Use a valid token format
        valid_token = "ghp_" + "a" * 36
        client = get_authenticated_client(valid_token)

        assert client is not None
        assert hasattr(client, "token")
        assert client.token == valid_token

    def test_get_authenticated_client_raises_error_with_invalid_token(self):
        """Test that get_authenticated_client raises error with invalid token."""
        from src.github_project_manager_mcp.utils.auth import get_authenticated_client

        with pytest.raises(ValueError, match="Invalid GitHub token format"):
            get_authenticated_client("invalid_token")

    def test_get_authenticated_client_raises_error_with_none_token(self):
        """Test that get_authenticated_client raises error with None token."""
        from src.github_project_manager_mcp.utils.auth import get_authenticated_client

        with pytest.raises(ValueError, match="GitHub token is required"):
            get_authenticated_client(None)

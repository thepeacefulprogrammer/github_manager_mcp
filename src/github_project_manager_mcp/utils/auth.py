"""
GitHub authentication utilities for token management and validation.

This module provides utilities for loading, validating, and managing GitHub
Personal Access Tokens for API authentication.
"""

import logging
import os
import re
from typing import Optional

from ..github_client import GitHubClient

logger = logging.getLogger(__name__)


def load_github_token() -> Optional[str]:
    """
    Load GitHub token from environment or .env file.

    Priority order:
    1. GITHUB_TOKEN environment variable
    2. GITHUB_TOKEN from .env file

    Returns:
        GitHub token string if found, None otherwise
    """
    # Check environment variable first
    token = os.getenv("GITHUB_TOKEN")
    if token:
        logger.debug("GitHub token loaded from environment variable")
        return token

    # Check .env file if no environment variable
    env_file_path = ".env"
    if os.path.exists(env_file_path):
        try:
            with open(env_file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GITHUB_TOKEN="):
                        token = line.split("=", 1)[1]
                        logger.debug("GitHub token loaded from .env file")
                        return token
        except IOError as e:
            logger.warning(f"Failed to read .env file: {e}")

    logger.warning("No GitHub token found in environment or .env file")
    return None


def validate_token_format(token: Optional[str]) -> bool:
    """
    Validate GitHub token format.

    Supports:
    - Classic tokens: ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX (40 chars total)
    - Fine-grained tokens: github_pat_XXXXXXXXXX_XXXXXXXXXXXX... (93 chars total)

    Args:
        token: Token string to validate

    Returns:
        True if token format is valid, False otherwise
    """
    if not token or not isinstance(token, str):
        return False

    # Classic GitHub token pattern (ghp_ + 36 alphanumeric characters)
    classic_pattern = r"^ghp_[A-Za-z0-9]{36}$"

    # Fine-grained GitHub token pattern (github_pat_ + 11 chars + _ + 82 chars)
    fine_grained_pattern = r"^github_pat_[A-Za-z0-9]{11}_[A-Za-z0-9]{82}$"

    return bool(
        re.match(classic_pattern, token) or re.match(fine_grained_pattern, token)
    )


async def verify_token_with_github(token: str) -> bool:
    """
    Verify token with GitHub API by making a test query.

    Args:
        token: GitHub token to verify

    Returns:
        True if token is valid and has necessary permissions, False otherwise
    """
    try:
        async with GitHubClient(token=token) as client:
            # Simple query to verify token and permissions
            query = """
            query {
                viewer {
                    login
                    id
                }
            }
            """

            result = await client.query(query)

            # If we get a valid response with viewer data, token is valid
            return bool(result.get("viewer", {}).get("login"))

    except Exception as e:
        logger.debug(f"Token verification failed: {e}")
        return False


def get_authenticated_client(token: Optional[str]) -> GitHubClient:
    """
    Get an authenticated GitHub client with token validation.

    Args:
        token: GitHub token for authentication

    Returns:
        Authenticated GitHubClient instance

    Raises:
        ValueError: If token is None, empty, or has invalid format
    """
    if not token:
        raise ValueError("GitHub token is required")

    if not validate_token_format(token):
        raise ValueError("Invalid GitHub token format")

    logger.debug("Creating authenticated GitHub client")
    return GitHubClient(token=token)

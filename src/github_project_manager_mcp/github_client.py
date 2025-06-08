"""
GitHub GraphQL API client for project management operations.

This module provides a client for interacting with GitHub's GraphQL API v4,
specifically designed for managing GitHub Projects v2.
"""

import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class GitHubClient:
    """
    Async GitHub GraphQL API client for Projects v2 operations.

    This client handles authentication, request/response processing,
    and provides methods for executing GraphQL queries and mutations.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: str = "https://api.github.com/graphql",
    ):
        """
        Initialize the GitHub client.

        Args:
            token: GitHub Personal Access Token for authentication
            base_url: GraphQL API endpoint URL (for GitHub Enterprise support)

        Raises:
            ValueError: If no token is provided
        """
        if not token:
            raise ValueError("GitHub token is required")

        self.token = token
        self.base_url = base_url

        # Set up HTTP client with proper headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github.v4+json",
        }

        self.session = httpx.AsyncClient(headers=headers, timeout=30.0)

        logger.info(f"Initialized GitHub client for {base_url}")

    async def query(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL query.

        Args:
            query: GraphQL query string
            variables: Optional variables for the query

        Returns:
            Query response data

        Raises:
            httpx.HTTPError: For HTTP-related errors
            ValueError: For GraphQL errors in response
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        logger.debug(f"Executing GraphQL query: {query[:100]}...")

        response = await self.session.post(self.base_url, json=payload)
        response.raise_for_status()

        data = response.json()

        if "errors" in data:
            error_msg = "; ".join(
                [error.get("message", "Unknown error") for error in data["errors"]]
            )
            raise ValueError(f"GraphQL errors: {error_msg}")

        return data.get("data", {})

    async def mutate(
        self, mutation: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL mutation.

        Args:
            mutation: GraphQL mutation string
            variables: Optional variables for the mutation

        Returns:
            Mutation response data

        Raises:
            httpx.HTTPError: For HTTP-related errors
            ValueError: For GraphQL errors in response
        """
        payload = {"query": mutation}
        if variables:
            payload["variables"] = variables

        logger.debug(f"Executing GraphQL mutation: {mutation[:100]}...")

        response = await self.session.post(self.base_url, json=payload)
        response.raise_for_status()

        data = response.json()

        if "errors" in data:
            error_msg = "; ".join(
                [error.get("message", "Unknown error") for error in data["errors"]]
            )
            raise ValueError(f"GraphQL errors: {error_msg}")

        return data.get("data", {})

    async def close(self) -> None:
        """Close the HTTP client session."""
        await self.session.aclose()
        logger.debug("GitHub client session closed")

    async def __aenter__(self) -> "GitHubClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

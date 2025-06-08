"""
GitHub GraphQL API client for project management operations.

This module provides a client for interacting with GitHub's GraphQL API v4,
specifically designed for managing GitHub Projects v2.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class GitHubClient:
    """
    Async GitHub GraphQL API client for Projects v2 operations.

    This client handles authentication, request/response processing,
    rate limiting compliance, and provides methods for executing GraphQL
    queries and mutations.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: str = "https://api.github.com/graphql",
        rate_limit_enabled: bool = False,
        requests_per_hour: int = 5000,
    ):
        """
        Initialize the GitHub client.

        Args:
            token: GitHub Personal Access Token for authentication
            base_url: GraphQL API endpoint URL (for GitHub Enterprise support)
            rate_limit_enabled: Whether to enforce rate limiting
            requests_per_hour: Maximum requests per hour (GitHub default: 5000)

        Raises:
            ValueError: If no token is provided
        """
        if not token:
            raise ValueError("GitHub token is required")

        self.token = token
        self.base_url = base_url
        self.rate_limit_enabled = rate_limit_enabled
        self.requests_per_hour = requests_per_hour

        # Rate limiting state
        self.remaining_requests: Optional[int] = None
        self.reset_time: Optional[int] = None
        self.request_timestamps: List[float] = []

        # Set up HTTP client with proper headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github.v4+json",
        }

        self.session = httpx.AsyncClient(headers=headers, timeout=30.0)

        logger.info(f"Initialized GitHub client for {base_url}")
        if rate_limit_enabled:
            logger.info(f"Rate limiting enabled: {requests_per_hour} requests/hour")

    async def _enforce_rate_limit(self) -> None:
        """
        Enforce rate limiting by checking request history and sleeping if necessary.

        This method implements client-side throttling based on request timestamps
        to ensure we don't exceed the configured requests per hour limit.
        """
        if not self.rate_limit_enabled:
            return

        current_time = time.time()
        one_hour_ago = current_time - 3600

        # Clean up old timestamps (older than 1 hour)
        self.request_timestamps = [
            ts for ts in self.request_timestamps if ts > one_hour_ago
        ]

        # Check if we need to throttle
        if len(self.request_timestamps) >= self.requests_per_hour:
            # Calculate when we can make the next request
            oldest_request = min(self.request_timestamps)
            next_available_time = oldest_request + 3600  # 1 hour later
            sleep_time = next_available_time - current_time

            if sleep_time > 0:
                logger.warning(
                    f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds"
                )
                await asyncio.sleep(sleep_time)

        # Record this request
        self.request_timestamps.append(current_time)

    async def _update_rate_limit_state(self, response: httpx.Response) -> None:
        """
        Update rate limit state from GitHub API response headers.

        Args:
            response: HTTP response containing rate limit headers
        """
        if not self.rate_limit_enabled:
            return

        # Extract rate limit information from headers
        remaining = response.headers.get("x-ratelimit-remaining")
        reset_time = response.headers.get("x-ratelimit-reset")
        limit = response.headers.get("x-ratelimit-limit")

        if remaining is not None:
            self.remaining_requests = int(remaining)
        if reset_time is not None:
            self.reset_time = int(reset_time)

        logger.debug(
            f"Rate limit status: {self.remaining_requests}/{limit} remaining, "
            f"resets at {self.reset_time}"
        )

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status information.

        Returns:
            Dictionary containing rate limit status
        """
        current_time = time.time()
        one_hour_ago = current_time - 3600

        # Count requests in the last hour
        recent_requests = [ts for ts in self.request_timestamps if ts > one_hour_ago]

        return {
            "enabled": self.rate_limit_enabled,
            "limit": self.requests_per_hour,
            "remaining": self.remaining_requests,
            "reset_time": self.reset_time,
            "requests_in_last_hour": len(recent_requests),
        }

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
        # Enforce rate limiting before making the request
        await self._enforce_rate_limit()

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        logger.debug(f"Executing GraphQL query: {query[:100]}...")

        response = await self.session.post(self.base_url, json=payload)
        response.raise_for_status()

        # Update rate limit state from response headers
        await self._update_rate_limit_state(response)

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
        # Enforce rate limiting before making the request
        await self._enforce_rate_limit()

        payload = {"query": mutation}
        if variables:
            payload["variables"] = variables

        logger.debug(f"Executing GraphQL mutation: {mutation[:100]}...")

        response = await self.session.post(self.base_url, json=payload)
        response.raise_for_status()

        # Update rate limit state from response headers
        await self._update_rate_limit_state(response)

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

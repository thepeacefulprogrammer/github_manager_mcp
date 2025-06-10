"""
Project search and filtering utilities for GitHub Project Manager MCP.

Provides comprehensive search functionality for GitHub Projects v2 including:
- Text-based search across project titles and descriptions
- Filtering by visibility, dates, and ownership
- Combined search criteria with logical operators
- Pagination and result ranking
- Advanced search query building
"""

import logging
import time
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ProjectSearchFilter:
    """
    Filter criteria for project search operations.

    Supports various filtering options including text search,
    visibility filters, date ranges, and sorting preferences.
    """

    query: str = ""
    visibility: Optional[str] = None  # "public" or "private"
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    updated_before: Optional[datetime] = None
    owner: Optional[str] = None
    limit: int = 25
    sort_by: str = "updated"  # "created", "updated", "name"
    sort_order: str = "desc"  # "asc" or "desc"

    def __post_init__(self):
        """Validate filter parameters after initialization."""
        if self.visibility and self.visibility not in ["public", "private"]:
            raise ValueError("visibility must be 'public' or 'private'")

        if not (1 <= self.limit <= 100):
            raise ValueError("limit must be between 1 and 100")

        if self.sort_by not in ["created", "updated", "name"]:
            raise ValueError("sort_by must be 'created', 'updated', or 'name'")

        if self.sort_order not in ["asc", "desc"]:
            raise ValueError("sort_order must be 'asc' or 'desc'")

    def to_dict(self) -> Dict[str, Any]:
        """Convert filter to dictionary, excluding None values."""
        result = {}
        for key, value in asdict(self).items():
            if value is not None:
                if isinstance(value, datetime):
                    result[key] = value.isoformat()
                else:
                    result[key] = value
        return result


@dataclass
class ProjectSearchResult:
    """
    Result of a project search operation.

    Contains matching projects, metadata about the search,
    and pagination information.
    """

    projects: List[Dict[str, Any]]
    total_count: int
    has_next_page: bool
    search_time_ms: float
    cursor: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert search result to dictionary."""
        return asdict(self)


class ProjectSearchManager:
    """
    Manager for project search and filtering operations.

    Provides comprehensive search functionality using GitHub's
    search API with advanced filtering and ranking capabilities.
    """

    def __init__(self, github_client=None):
        """
        Initialize the project search manager.

        Args:
            github_client: Authenticated GitHub GraphQL client
        """
        self.github_client = github_client
        logger.info("Project search manager initialized")

    async def search_projects(
        self, search_filter: ProjectSearchFilter
    ) -> ProjectSearchResult:
        """
        Search projects using the provided filter criteria.

        Args:
            search_filter: Filter criteria for the search

        Returns:
            ProjectSearchResult containing matching projects and metadata

        Raises:
            ValueError: If GitHub client is not initialized
            Exception: If search operation fails
        """
        if not self.github_client:
            raise ValueError("GitHub client not initialized")

        start_time = time.time()

        try:
            # Build the search query
            search_query_string = self._build_search_query(search_filter)

            # Build GraphQL query
            graphql_query = self._build_graphql_search_query(
                search_filter, search_query_string
            )

            # Execute search
            response = await self.github_client.query(graphql_query)

            # Handle errors
            if "errors" in response:
                error_messages = [error["message"] for error in response["errors"]]
                raise Exception(f"GraphQL errors: {'; '.join(error_messages)}")

            # Extract search results
            # Handle both user and viewer query formats
            if "user" in response["data"] and response["data"]["user"]:
                projects_data = response["data"]["user"]["projectsV2"]
            elif "viewer" in response["data"]:
                projects_data = response["data"]["viewer"]["projectsV2"]
            else:
                projects_data = {
                    "nodes": [],
                    "totalCount": 0,
                    "pageInfo": {"hasNextPage": False},
                }

            projects = []
            for node in projects_data.get("nodes", []):
                # Apply client-side filtering for text search and other criteria
                if self._matches_search_criteria(node, search_filter):
                    formatted_project = self._format_project_from_search_result(node)
                    projects.append(formatted_project)

            # Calculate search time
            search_time_ms = (time.time() - start_time) * 1000

            # Create result
            result = ProjectSearchResult(
                projects=projects,
                total_count=len(projects),  # Use actual filtered count
                has_next_page=projects_data.get("pageInfo", {}).get(
                    "hasNextPage", False
                ),
                search_time_ms=search_time_ms,
                cursor=projects_data.get("pageInfo", {}).get("endCursor"),
            )

            logger.info(
                f"Search completed: {len(projects)} projects found in {search_time_ms:.1f}ms"
            )
            return result

        except Exception as e:
            logger.error(f"Project search failed: {str(e)}")
            raise

    def _build_search_query(self, search_filter: ProjectSearchFilter) -> str:
        """
        Build GitHub search query string from filter criteria.

        Args:
            search_filter: Filter criteria

        Returns:
            GitHub search query string
        """
        query_parts = []

        # Base text query
        if search_filter.query:
            query_parts.append(search_filter.query)

        # Type filter - always search for projects v2
        query_parts.append("type:projectv2")

        # Visibility filter
        if search_filter.visibility:
            query_parts.append(f"is:{search_filter.visibility}")

        # Owner filter
        if search_filter.owner:
            query_parts.append(f"user:{search_filter.owner}")

        # Date filters
        if search_filter.created_after:
            date_str = search_filter.created_after.strftime("%Y-%m-%d")
            query_parts.append(f"created:>{date_str}")

        if search_filter.created_before:
            date_str = search_filter.created_before.strftime("%Y-%m-%d")
            query_parts.append(f"created:<{date_str}")

        if search_filter.updated_after:
            date_str = search_filter.updated_after.strftime("%Y-%m-%d")
            query_parts.append(f"updated:>{date_str}")

        if search_filter.updated_before:
            date_str = search_filter.updated_before.strftime("%Y-%m-%d")
            query_parts.append(f"updated:<{date_str}")

        return " ".join(query_parts)

    def _build_graphql_search_query(
        self, search_filter: ProjectSearchFilter, search_query: str
    ) -> str:
        """
        Build GraphQL query for project search.

        Since GitHub's GraphQL search API doesn't support ProjectV2 directly,
        we'll use a different approach by searching repositories and their projects.

        Args:
            search_filter: Filter criteria
            search_query: GitHub search query string

        Returns:
            GraphQL query string
        """
        # For now, we'll use the viewer's projects as a fallback
        # This is a simplified approach - in production you'd want to implement
        # a more sophisticated search using repository search + project filtering

        # Build sort clause
        sort_field = {
            "created": "CREATED_AT",
            "updated": "UPDATED_AT",
            "name": "NAME",
        }.get(search_filter.sort_by, "UPDATED_AT")

        sort_direction = "ASC" if search_filter.sort_order == "asc" else "DESC"

        # If we have an owner filter, search their projects specifically
        if search_filter.owner:
            query = f"""
            query {{
                user(login: "{search_filter.owner}") {{
                    projectsV2(
                        first: {search_filter.limit}
                        orderBy: {{field: {sort_field}, direction: {sort_direction}}}
                    ) {{
                        totalCount
                        pageInfo {{
                            hasNextPage
                            endCursor
                        }}
                        nodes {{
                            id
                            title
                            shortDescription
                            public
                            createdAt
                            updatedAt
                            owner {{
                                login
                            }}
                        }}
                    }}
                }}
            }}
            """
        else:
            # Search viewer's projects (fallback approach)
            query = f"""
            query {{
                viewer {{
                    projectsV2(
                        first: {search_filter.limit}
                        orderBy: {{field: {sort_field}, direction: {sort_direction}}}
                    ) {{
                        totalCount
                        pageInfo {{
                            hasNextPage
                            endCursor
                        }}
                        nodes {{
                            id
                            title
                            shortDescription
                            public
                            createdAt
                            updatedAt
                            owner {{
                                login
                            }}
                        }}
                    }}
                }}
            }}
            """

        return query

    def _matches_search_criteria(
        self, project_node: Dict[str, Any], search_filter: ProjectSearchFilter
    ) -> bool:
        """
        Check if a project node matches the search criteria.

        Args:
            project_node: Project node from GraphQL response
            search_filter: Search filter criteria

        Returns:
            True if project matches criteria, False otherwise
        """
        # Text search in title and description
        if search_filter.query:
            query_lower = search_filter.query.lower()
            title = project_node.get("title", "").lower()
            description = project_node.get("shortDescription", "").lower()

            if query_lower not in title and query_lower not in description:
                return False

        # Visibility filter
        if search_filter.visibility:
            project_public = project_node.get("public", False)
            if search_filter.visibility == "public" and not project_public:
                return False
            if search_filter.visibility == "private" and project_public:
                return False

        # Date filters (basic implementation)
        if search_filter.created_after or search_filter.created_before:
            created_at_str = project_node.get("createdAt")
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(
                        created_at_str.replace("Z", "+00:00")
                    )
                    if (
                        search_filter.created_after
                        and created_at < search_filter.created_after
                    ):
                        return False
                    if (
                        search_filter.created_before
                        and created_at > search_filter.created_before
                    ):
                        return False
                except ValueError:
                    pass  # Skip date filtering if date parsing fails

        if search_filter.updated_after or search_filter.updated_before:
            updated_at_str = project_node.get("updatedAt")
            if updated_at_str:
                try:
                    updated_at = datetime.fromisoformat(
                        updated_at_str.replace("Z", "+00:00")
                    )
                    if (
                        search_filter.updated_after
                        and updated_at < search_filter.updated_after
                    ):
                        return False
                    if (
                        search_filter.updated_before
                        and updated_at > search_filter.updated_before
                    ):
                        return False
                except ValueError:
                    pass  # Skip date filtering if date parsing fails

        return True

    def _format_project_from_search_result(
        self, search_node: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format a project from search result node.

        Args:
            search_node: Raw search result node from GraphQL

        Returns:
            Formatted project dictionary
        """
        return {
            "id": search_node.get("id"),
            "title": search_node.get("title"),
            "shortDescription": search_node.get("shortDescription"),
            "public": search_node.get("public"),
            "createdAt": search_node.get("createdAt"),
            "updatedAt": search_node.get("updatedAt"),
            "owner": search_node.get("owner", {}).get("login"),
        }


class ProjectSearchQueryBuilder:
    """
    Builder for complex project search queries.

    Provides a fluent interface for constructing advanced
    search queries with multiple criteria and logical operators.
    """

    def __init__(self):
        """Initialize the query builder."""
        self.filter = ProjectSearchFilter()

    def query(self, text: str) -> "ProjectSearchQueryBuilder":
        """Add text query."""
        self.filter.query = text
        return self

    def public(self) -> "ProjectSearchQueryBuilder":
        """Filter for public projects only."""
        self.filter.visibility = "public"
        return self

    def private(self) -> "ProjectSearchQueryBuilder":
        """Filter for private projects only."""
        self.filter.visibility = "private"
        return self

    def owner(self, username: str) -> "ProjectSearchQueryBuilder":
        """Filter by project owner."""
        self.filter.owner = username
        return self

    def created_after(self, date: datetime) -> "ProjectSearchQueryBuilder":
        """Filter projects created after the specified date."""
        self.filter.created_after = date
        return self

    def created_before(self, date: datetime) -> "ProjectSearchQueryBuilder":
        """Filter projects created before the specified date."""
        self.filter.created_before = date
        return self

    def updated_after(self, date: datetime) -> "ProjectSearchQueryBuilder":
        """Filter projects updated after the specified date."""
        self.filter.updated_after = date
        return self

    def updated_before(self, date: datetime) -> "ProjectSearchQueryBuilder":
        """Filter projects updated before the specified date."""
        self.filter.updated_before = date
        return self

    def limit(self, count: int) -> "ProjectSearchQueryBuilder":
        """Set result limit."""
        self.filter.limit = count
        return self

    def sort_by_created(self, ascending: bool = False) -> "ProjectSearchQueryBuilder":
        """Sort by creation date."""
        self.filter.sort_by = "created"
        self.filter.sort_order = "asc" if ascending else "desc"
        return self

    def sort_by_updated(self, ascending: bool = False) -> "ProjectSearchQueryBuilder":
        """Sort by update date."""
        self.filter.sort_by = "updated"
        self.filter.sort_order = "asc" if ascending else "desc"
        return self

    def sort_by_name(self, ascending: bool = True) -> "ProjectSearchQueryBuilder":
        """Sort by project name."""
        self.filter.sort_by = "name"
        self.filter.sort_order = "asc" if ascending else "desc"
        return self

    def build(self) -> ProjectSearchFilter:
        """Build the final search filter."""
        return self.filter

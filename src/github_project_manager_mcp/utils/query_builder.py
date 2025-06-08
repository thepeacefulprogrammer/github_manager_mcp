"""
GraphQL query builder utilities for GitHub Projects v2 API.

This module provides utilities for building type-safe GraphQL queries and mutations
specifically for GitHub's Projects v2 API, including support for pagination,
field selection, and proper parameter validation.
"""

import json
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class ProjectQueryBuilder:
    """
    Builder for GitHub Projects v2 GraphQL queries and mutations.

    This class provides methods to construct GraphQL queries and mutations
    for common project management operations, with built-in support for
    pagination, field selection, and parameter validation.
    """

    # Default fields for project queries
    DEFAULT_PROJECT_FIELDS = [
        "id",
        "title",
        "description",
        "url",
        "createdAt",
        "updatedAt",
        "viewerCanUpdate",
        "number",
    ]

    # Default fields for project items
    DEFAULT_ITEM_FIELDS = [
        "id",
        "createdAt",
        "updatedAt",
        "content",
    ]

    def _escape_string(self, value: str) -> str:
        """Escape a string for use in GraphQL queries."""
        if value is None:
            return '""'
        # Use JSON encoding to properly escape quotes and special characters
        return json.dumps(value)

    def _build_fields_fragment(self, fields: Optional[List[str]] = None) -> str:
        """Build a fields fragment for GraphQL queries."""
        if fields is None:
            fields = self.DEFAULT_PROJECT_FIELDS

        return "\n".join(f"      {field}" for field in fields)

    def _build_pagination_args(
        self, first: Optional[int] = None, after: Optional[str] = None
    ) -> str:
        """Build pagination arguments for GraphQL queries."""
        args = []
        if first is not None:
            args.append(f"first: {first}")
        if after is not None:
            args.append(f"after: {self._escape_string(after)}")

        if args:
            return f"({', '.join(args)})"
        return ""

    def list_projects(
        self,
        owner: str,
        first: Optional[int] = None,
        after: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> str:
        """
        Build a query to list projects for a user or organization.

        Args:
            owner: Username or organization name
            first: Number of projects to fetch (pagination)
            after: Cursor for pagination
            fields: List of fields to include in response

        Returns:
            GraphQL query string

        Raises:
            ValueError: If owner is empty or None
        """
        if not owner:
            raise ValueError("Owner is required")

        pagination_args = self._build_pagination_args(first, after)
        fields_fragment = self._build_fields_fragment(fields)

        pagination_info = ""
        if first is not None or after is not None:
            pagination_info = """
      pageInfo {
        hasNextPage
        hasPreviousPage
        startCursor
        endCursor
      }"""

        query = f"""
query {{
  user(login: {self._escape_string(owner)}) {{
    projectsV2{pagination_args} {{
      totalCount{pagination_info}
      nodes {{
{fields_fragment}
      }}
    }}
  }}
}}
""".strip()

        logger.debug(f"Built list projects query for owner: {owner}")
        return query

    def get_project(self, project_id: str, fields: Optional[List[str]] = None) -> str:
        """
        Build a query to get a single project by ID.

        Args:
            project_id: GitHub project ID
            fields: List of fields to include in response

        Returns:
            GraphQL query string

        Raises:
            ValueError: If project_id is empty or None
        """
        if not project_id:
            raise ValueError("Project ID is required")

        fields_fragment = self._build_fields_fragment(fields)

        query = f"""
query {{
  node(id: {self._escape_string(project_id)}) {{
    ... on ProjectV2 {{
{fields_fragment}
    }}
  }}
}}
""".strip()

        logger.debug(f"Built get project query for ID: {project_id}")
        return query

    def get_project_items(
        self,
        project_id: str,
        first: Optional[int] = None,
        after: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> str:
        """
        Build a query to get items from a project.

        Args:
            project_id: GitHub project ID
            first: Number of items to fetch (pagination)
            after: Cursor for pagination
            fields: List of fields to include for items

        Returns:
            GraphQL query string

        Raises:
            ValueError: If project_id is empty or None
        """
        if not project_id:
            raise ValueError("Project ID is required")

        pagination_args = self._build_pagination_args(first, after)

        # Use default item fields if none provided
        if fields is None:
            fields = self.DEFAULT_ITEM_FIELDS

        item_fields = "\n".join(f"        {field}" for field in fields)

        pagination_info = ""
        if first is not None or after is not None:
            pagination_info = """
        pageInfo {
          hasNextPage
          hasPreviousPage
          startCursor
          endCursor
        }"""

        query = f"""
query {{
  node(id: {self._escape_string(project_id)}) {{
    ... on ProjectV2 {{
      items{pagination_args} {{
        totalCount{pagination_info}
        nodes {{
{item_fields}
        }}
      }}
    }}
  }}
}}
""".strip()

        logger.debug(f"Built get project items query for ID: {project_id}")
        return query

    def search_projects(
        self, owner: str, search_term: str, fields: Optional[List[str]] = None
    ) -> str:
        """
        Build a query to search projects (client-side filtering).

        Note: GitHub's Projects v2 API doesn't have native search,
        so this returns all projects for client-side filtering.

        Args:
            owner: Username or organization name
            search_term: Search term (for documentation/client-side use)
            fields: List of fields to include in response

        Returns:
            GraphQL query string
        """
        # For now, return all projects since API doesn't support search
        # Clients can filter the results based on search_term
        logger.debug(
            f"Built search projects query (client-side filtering): {search_term}"
        )
        return self.list_projects(owner, fields=fields)

    def create_project(
        self, owner_id: str, title: str, description: Optional[str] = None
    ) -> str:
        """
        Build a mutation to create a new project.

        Args:
            owner_id: GitHub user or organization ID
            title: Project title
            description: Optional project description

        Returns:
            GraphQL mutation string

        Raises:
            ValueError: If owner_id or title is empty or None
        """
        if not owner_id:
            raise ValueError("Owner ID is required")
        if not title:
            raise ValueError("Title is required")

        input_fields = [
            f"ownerId: {self._escape_string(owner_id)}",
            f"title: {self._escape_string(title)}",
        ]

        if description:
            input_fields.append(f"description: {self._escape_string(description)}")

        mutation = f"""
mutation {{
  createProjectV2(input: {{
    {', '.join(input_fields)}
  }}) {{
    projectV2 {{
      id
      title
      description
      url
      createdAt
    }}
  }}
}}
""".strip()

        logger.debug(f"Built create project mutation: {title}")
        return mutation

    def update_project(
        self,
        project_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """
        Build a mutation to update a project.

        Args:
            project_id: GitHub project ID
            title: New project title
            description: New project description

        Returns:
            GraphQL mutation string

        Raises:
            ValueError: If project_id is empty or no updates provided
        """
        if not project_id:
            raise ValueError("Project ID is required")

        input_fields = [f"projectId: {self._escape_string(project_id)}"]

        if title is not None:
            input_fields.append(f"title: {self._escape_string(title)}")
        if description is not None:
            input_fields.append(f"description: {self._escape_string(description)}")

        if len(input_fields) == 1:  # Only projectId provided
            raise ValueError("At least one field to update is required")

        mutation = f"""
mutation {{
  updateProjectV2(input: {{
    {', '.join(input_fields)}
  }}) {{
    projectV2 {{
      id
      title
      description
      updatedAt
    }}
  }}
}}
""".strip()

        logger.debug(f"Built update project mutation for ID: {project_id}")
        return mutation

    def delete_project(self, project_id: str) -> str:
        """
        Build a mutation to delete a project.

        Args:
            project_id: GitHub project ID

        Returns:
            GraphQL mutation string

        Raises:
            ValueError: If project_id is empty or None
        """
        if not project_id:
            raise ValueError("Project ID is required")

        mutation = f"""
mutation {{
  deleteProjectV2(input: {{
    projectId: {self._escape_string(project_id)}
  }}) {{
    projectV2 {{
      id
    }}
  }}
}}
""".strip()

        logger.debug(f"Built delete project mutation for ID: {project_id}")
        return mutation

    def add_item_to_project(self, project_id: str, content_id: str) -> str:
        """
        Build a mutation to add an item to a project.

        Args:
            project_id: GitHub project ID
            content_id: GitHub content ID (issue, PR, etc.)

        Returns:
            GraphQL mutation string

        Raises:
            ValueError: If project_id or content_id is empty or None
        """
        if not project_id:
            raise ValueError("Project ID is required")
        if not content_id:
            raise ValueError("Content ID is required")

        mutation = f"""
mutation {{
  addProjectV2ItemById(input: {{
    projectId: {self._escape_string(project_id)}
    contentId: {self._escape_string(content_id)}
  }}) {{
    item {{
      id
      createdAt
      content {{
        ... on Issue {{
          id
          title
          number
        }}
        ... on PullRequest {{
          id
          title
          number
        }}
      }}
    }}
  }}
}}
""".strip()

        logger.debug(f"Built add item to project mutation: {project_id} + {content_id}")
        return mutation

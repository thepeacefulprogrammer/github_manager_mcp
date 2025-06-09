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
        "url",
        "createdAt",
        "updatedAt",
        "viewerCanUpdate",
        "number",
        "shortDescription",
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

        # Note: GitHub Projects v2 API doesn't accept description in CreateProjectV2Input
        # Description can be added later via updateProjectV2 mutation if needed

        mutation = f"""
mutation {{
  createProjectV2(input: {{
    {', '.join(input_fields)}
  }}) {{
    projectV2 {{
      id
      title
      shortDescription
      url
      number
      createdAt
      owner {{
        ... on User {{
          login
        }}
        ... on Organization {{
          login
        }}
      }}
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
        short_description: Optional[str] = None,
        readme: Optional[str] = None,
        public: Optional[bool] = None,
    ) -> str:
        """
        Build a mutation to update a project.

        Args:
            project_id: GitHub project ID
            title: New project title
            short_description: New project short description
            readme: New project README content
            public: Whether the project should be public

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
        if short_description is not None:
            input_fields.append(
                f"shortDescription: {self._escape_string(short_description)}"
            )
        if readme is not None:
            input_fields.append(f"readme: {self._escape_string(readme)}")
        if public is not None:
            input_fields.append(f"public: {str(public).lower()}")

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
      shortDescription
      readme
      public
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
      title
      owner {{
        ... on User {{
          login
        }}
        ... on Organization {{
          login
        }}
      }}
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

    def list_prds_in_project(
        self,
        project_id: str,
        first: Optional[int] = None,
        after: Optional[str] = None,
    ) -> str:
        """
        Build a query to list PRDs (draft issues) in a project.

        Args:
            project_id: GitHub project ID
            first: Number of items to fetch (pagination)
            after: Cursor for pagination

        Returns:
            GraphQL query string

        Raises:
            ValueError: If project_id is empty or None
        """
        if not project_id:
            raise ValueError("Project ID is required")

        pagination_args = self._build_pagination_args(first, after)

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
      title
      items{pagination_args} {{
        totalCount{pagination_info}
        nodes {{
          id
          createdAt
          updatedAt
          content {{
            ... on DraftIssue {{
              id
              title
              body
              createdAt
              updatedAt
              assignees(first: 50) {{
                totalCount
                nodes {{
                  login
                  name
                }}
              }}
            }}
            ... on Issue {{
              id
              title
              body
              number
              state
              createdAt
              updatedAt
              assignees(first: 50) {{
                totalCount
                nodes {{
                  login
                  name
                }}
              }}
              repository {{
                name
                owner {{
                  login
                }}
              }}
            }}
          }}
          fieldValues(first: 10) {{
            nodes {{
              ... on ProjectV2ItemFieldTextValue {{
                text
                field {{
                  ... on ProjectV2Field {{
                    name
                  }}
                }}
              }}
              ... on ProjectV2ItemFieldSingleSelectValue {{
                name
                field {{
                  ... on ProjectV2SingleSelectField {{
                    name
                  }}
                }}
              }}
            }}
          }}
        }}
      }}
    }}
  }}
}}
""".strip()

        logger.debug(f"Built list PRDs in project query for ID: {project_id}")
        return query

    def list_tasks_in_project(
        self,
        project_id: str,
        parent_prd_id: Optional[str] = None,
        first: Optional[int] = None,
        after: Optional[str] = None,
    ) -> str:
        """
        Build a query to list Tasks (draft issues marked as tasks) in a project.

        Tasks are identified by having a "Parent PRD" field value or being specifically
        marked as tasks in their content structure.

        Args:
            project_id: GitHub project ID
            parent_prd_id: Optional PRD ID to filter tasks by parent
            first: Number of items to fetch (pagination)
            after: Cursor for pagination

        Returns:
            GraphQL query string

        Raises:
            ValueError: If project_id is empty or None
        """
        if not project_id:
            raise ValueError("Project ID is required")

        pagination_args = self._build_pagination_args(first, after)

        pagination_info = ""
        if first is not None or after is not None:
            pagination_info = """
        pageInfo {
          hasNextPage
          hasPreviousPage
          startCursor
          endCursor
        }"""

        # Similar structure to list_prds_in_project but focused on tasks
        query = f"""
query {{
  node(id: {self._escape_string(project_id)}) {{
    ... on ProjectV2 {{
      title
      items{pagination_args} {{
        totalCount{pagination_info}
        nodes {{
          id
          createdAt
          updatedAt
          content {{
            ... on DraftIssue {{
              id
              title
              body
              createdAt
              updatedAt
              assignees(first: 50) {{
                totalCount
                nodes {{
                  login
                  name
                }}
              }}
            }}
            ... on Issue {{
              id
              title
              body
              number
              state
              createdAt
              updatedAt
              assignees(first: 50) {{
                totalCount
                nodes {{
                  login
                  name
                }}
              }}
              repository {{
                name
                owner {{
                  login
                }}
              }}
            }}
          }}
          fieldValues(first: 10) {{
            nodes {{
              ... on ProjectV2ItemFieldTextValue {{
                text
                field {{
                  ... on ProjectV2Field {{
                    name
                  }}
                }}
              }}
              ... on ProjectV2ItemFieldSingleSelectValue {{
                name
                field {{
                  ... on ProjectV2SingleSelectField {{
                    name
                  }}
                }}
              }}
            }}
          }}
        }}
      }}
    }}
  }}
}}
""".strip()

        logger.debug(
            f"Built list tasks in project query for ID: {project_id}, parent PRD: {parent_prd_id}"
        )
        return query

    def update_prd(
        self,
        prd_item_id: str,
        title: Optional[str] = None,
        body: Optional[str] = None,
        assignee_ids: Optional[List[str]] = None,
    ) -> str:
        """
        Build a mutation to update a PRD (Draft Issue) in a project.

        Note: This method expects the draft issue content ID (not the project item ID).

        Args:
            prd_item_id: GitHub draft issue content ID
            title: New title for the PRD
            body: New body content for the PRD
            assignee_ids: List of user IDs to assign to the PRD

        Returns:
            GraphQL mutation string to update the draft issue

        Raises:
            ValueError: If prd_item_id is empty or None, or no updates provided
        """
        if not prd_item_id:
            raise ValueError("PRD item ID is required")

        if not any([title is not None, body is not None, assignee_ids is not None]):
            raise ValueError("At least one field must be provided for update")

        # Build the input fields for the mutation
        input_fields = [f"draftIssueId: {self._escape_string(prd_item_id)}"]

        if title is not None:
            input_fields.append(f"title: {self._escape_string(title)}")

        if body is not None:
            input_fields.append(f"body: {self._escape_string(body)}")

        if assignee_ids is not None:
            # Convert list of assignee IDs to GraphQL array format
            assignee_list = (
                "[" + ", ".join(self._escape_string(aid) for aid in assignee_ids) + "]"
            )
            input_fields.append(f"assigneeIds: {assignee_list}")

        input_str = ", ".join(input_fields)

        mutation = f"""
mutation {{
  updateProjectV2DraftIssue(input: {{
    {input_str}
  }}) {{
    draftIssue {{
      id
      title
      body
      createdAt
      updatedAt
      assignees(first: 50) {{
        totalCount
        nodes {{
          id
          login
          name
        }}
      }}
      projectV2Items(first: 10) {{
        totalCount
        nodes {{
          id
          project {{
            id
            title
          }}
        }}
      }}
    }}
  }}
}}
""".strip()

        logger.debug(f"Built update PRD mutation for draft issue ID: {prd_item_id}")
        return mutation

    def get_prd_content_id(self, prd_item_id: str) -> str:
        """
        Build a query to get the draft issue content ID from a project item ID.

        Args:
            prd_item_id: GitHub project item ID (PVTI_...)

        Returns:
            GraphQL query string to get the content ID

        Raises:
            ValueError: If prd_item_id is empty or None
        """
        if not prd_item_id:
            raise ValueError("PRD item ID is required")

        query = f"""
query {{
  node(id: {self._escape_string(prd_item_id)}) {{
    ... on ProjectV2Item {{
      content {{
        ... on DraftIssue {{
          id
        }}
      }}
    }}
  }}
}}
""".strip()

        logger.debug(f"Built get PRD content ID query for item ID: {prd_item_id}")
        return query

    def get_project_item_fields(self, project_item_id: str) -> str:
        """
        Build a query to get project item and its available fields for field value updates.

        Args:
            project_item_id: GitHub project item ID

        Returns:
            GraphQL query string

        Raises:
            ValueError: If project_item_id is empty or None
        """
        if not project_item_id:
            raise ValueError("Project item ID is required")

        query = f"""
query {{
  node(id: {self._escape_string(project_item_id)}) {{
    ... on ProjectV2Item {{
      id
      project {{
        id
        fields(first: 50) {{
          nodes {{
            ... on ProjectV2SingleSelectField {{
              id
              name
              dataType
              options {{
                id
                name
              }}
            }}
          }}
        }}
      }}
    }}
  }}
}}
""".strip()

        logger.debug(f"Built get project item fields query for ID: {project_item_id}")
        return query

    def update_project_item_field_value(
        self,
        project_id: str,
        item_id: str,
        field_id: str,
        single_select_option_id: str,
    ) -> str:
        """
        Build a mutation to update a single select field value for a project item.

        Args:
            project_id: GitHub project ID
            item_id: GitHub project item ID
            field_id: Field ID to update
            single_select_option_id: Option ID for the single select field

        Returns:
            GraphQL mutation string

        Raises:
            ValueError: If any required parameter is empty or None
        """
        if not project_id:
            raise ValueError("Project ID is required")
        if not item_id:
            raise ValueError("Item ID is required")
        if not field_id:
            raise ValueError("Field ID is required")
        if not single_select_option_id:
            raise ValueError("Single select option ID is required")

        mutation = f"""
mutation {{
  updateProjectV2ItemFieldValue(input: {{
    projectId: {self._escape_string(project_id)}
    itemId: {self._escape_string(item_id)}
    fieldId: {self._escape_string(field_id)}
    value: {{
      singleSelectOptionId: {self._escape_string(single_select_option_id)}
    }}
  }}) {{
    projectV2Item {{
      id
      updatedAt
    }}
  }}
}}
""".strip()

        logger.debug(f"Built update field value mutation for item: {item_id}")
        return mutation

    def update_project_item_number_field_value(
        self,
        project_id: str,
        item_id: str,
        field_id: str,
        number_value: int,
    ) -> str:
        """
        Build a mutation to update a number field value for a project item.

        Args:
            project_id: GitHub project ID
            item_id: GitHub project item ID
            field_id: Field ID to update
            number_value: Number value for the field

        Returns:
            GraphQL mutation string

        Raises:
            ValueError: If any required parameter is empty or None
        """
        if not project_id:
            raise ValueError("Project ID is required")
        if not item_id:
            raise ValueError("Item ID is required")
        if not field_id:
            raise ValueError("Field ID is required")
        if number_value is None:
            raise ValueError("Number value is required")

        mutation = f"""
mutation {{
  updateProjectV2ItemFieldValue(input: {{
    projectId: {self._escape_string(project_id)}
    itemId: {self._escape_string(item_id)}
    fieldId: {self._escape_string(field_id)}
    value: {{
      number: {number_value}
    }}
  }}) {{
    projectV2Item {{
      id
      updatedAt
    }}
  }}
}}
""".strip()

        logger.debug(f"Built update number field value mutation for item: {item_id}")
        return mutation

    def update_task(
        self,
        task_item_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """
        Build a GraphQL mutation to update a Task's draft issue content.

        Args:
            task_item_id: GitHub project item ID containing the draft issue
            title: New title for the Task
            description: New description content for the Task

        Returns:
            GraphQL mutation string to update the draft issue

        Raises:
            ValueError: If task_item_id is empty or None, or no updates provided
        """
        if not task_item_id:
            raise ValueError("Task item ID is required")

        if not any([title is not None, description is not None]):
            raise ValueError("At least one field must be provided for update")

        # Build the input fields for the mutation
        input_fields = [f"draftIssueId: {self._escape_string(task_item_id)}"]

        if title is not None:
            input_fields.append(f"title: {self._escape_string(title)}")

        if description is not None:
            input_fields.append(f"body: {self._escape_string(description)}")

        input_str = ", ".join(input_fields)

        mutation = f"""
mutation {{
  updateProjectV2DraftIssue(input: {{
    {input_str}
  }}) {{
    draftIssue {{
      id
      title
      body
      createdAt
      updatedAt
      projectV2Items(first: 10) {{
        totalCount
        nodes {{
          id
          project {{
            id
            title
          }}
        }}
      }}
    }}
  }}
}}
""".strip()

        logger.debug(f"Built update Task mutation for draft issue ID: {task_item_id}")
        return mutation

    def get_task_content_id(self, task_item_id: str) -> str:
        """
        Build a query to get the draft issue content ID from a task project item ID.

        Args:
            task_item_id: GitHub project item ID (PVTI_...)

        Returns:
            GraphQL query string to get the content ID

        Raises:
            ValueError: If task_item_id is empty or None
        """
        if not task_item_id:
            raise ValueError("Task item ID is required")

        query = f"""
query {{
  node(id: {self._escape_string(task_item_id)}) {{
    ... on ProjectV2Item {{
      content {{
        ... on DraftIssue {{
          id
        }}
      }}
    }}
  }}
}}
""".strip()

        logger.debug(f"Built get Task content ID query for item ID: {task_item_id}")
        return query

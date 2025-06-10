import asyncio
import sys
from unittest.mock import AsyncMock

sys.path.append("src")
from github_project_manager_mcp.utils.relationship_manager import RelationshipManager


async def test_debug():
    mock_client = AsyncMock()
    manager = RelationshipManager(github_client=mock_client)

    # Test the _is_item_complete method with the exact mock data from the test
    test_item = {
        "id": "PVTI_task1",
        "content": {
            "id": "DI_task1",
            "title": "Task 1",
            "body": "**Parent PRD:** PVTI_prd123\n\nTask 1 description",
        },
        "fieldValues": {"nodes": [{"field": {"name": "Status"}, "value": "Done"}]},
    }

    is_complete = manager._is_item_complete(test_item)
    print(f"Is item complete: {is_complete}")

    # Test the pattern matching more carefully
    import re

    body = "**Parent PRD:** PVTI_prd123\n\nTask 1 description"
    print(f'Body content: "{body}"')

    # Test different patterns
    patterns = [
        r"\*\*Parent PRD:\*\*\s*([A-Z0-9_]+)",
        r"\*\*Parent PRD:\*\*\s*([A-Za-z0-9_]+)",
        r"\*\*Parent PRD:\*\*\s*(\w+)",
        r"\*\*Parent PRD:\*\*\s*([^\s\n]+)",
    ]

    for i, pattern in enumerate(patterns):
        match = re.search(pattern, body)
        print(f"Pattern {i+1}: {pattern}")
        print(f"  Match: {match.group(1) if match else None}")
        print(f"  Full match: {match.group(0) if match else None}")
        print()


asyncio.run(test_debug())

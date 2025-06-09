#!/usr/bin/env python3
"""
Debug script to test PRD creation with GitHub API
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from github_project_manager_mcp.handlers.prd_handlers import add_prd_to_project_handler

# Setup logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")


async def main():
    """Test PRD creation with debug output"""

    # Test arguments
    args = {
        "project_id": "PVT_kwHOAGo2TM4A7DCP",
        "title": "Debug Test PRD",
        "description": "Testing PRD creation with debug output",
    }

    print("Testing PRD creation...")
    print(f"Args: {args}")

    try:
        result = await add_prd_to_project_handler(args)
        print(f"\nResult type: {type(result)}")
        print(f"Is error: {result.isError}")
        if result.content:
            print(f"Content: {result.content[0].text}")
        else:
            print("No content in result")
    except Exception as e:
        print(f"Exception occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

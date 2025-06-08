"""
pytest configuration and fixtures specific to unit tests.
"""

from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_github_client():
    """Provide a mock GitHub client for unit tests."""
    client = Mock()
    client.query = Mock()
    client.mutate = Mock()
    return client


@pytest.fixture
def mock_mcp_server():
    """Provide a mock MCP server for unit tests."""
    server = Mock()
    server.list_tools = Mock()
    server.call_tool = Mock()
    return server


@pytest.fixture
def mock_logger():
    """Provide a mock logger for unit tests."""
    logger = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    return logger

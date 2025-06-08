"""
Shared pytest configuration and fixtures for the entire test suite.
"""

import os
import sys
import pytest
from unittest.mock import Mock

# Add src directory to Python path so tests can import the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture
def mock_github_token():
    """Provide a mock GitHub token for tests."""
    return "test_token_123"

@pytest.fixture
def mock_env_vars(monkeypatch, mock_github_token):
    """Mock environment variables for tests."""
    monkeypatch.setenv("GITHUB_TOKEN", mock_github_token)
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("MCP_SERVER_HOST", "localhost")
    monkeypatch.setenv("MCP_SERVER_PORT", "8000")

@pytest.fixture
def sample_project_data():
    """Provide sample project data for tests."""
    return {
        "id": "test_project_123",
        "name": "Test Project",
        "description": "A test project for development",
        "status": "active"
    }

@pytest.fixture
def sample_prd_data():
    """Provide sample PRD data for tests.""" 
    return {
        "id": "test_prd_456",
        "title": "Test PRD",
        "description": "A test Product Requirements Document",
        "status": "draft",
        "project_id": "test_project_123"
    }

@pytest.fixture
def sample_task_data():
    """Provide sample task data for tests."""
    return {
        "id": "test_task_789",
        "title": "Test Task",
        "description": "A test task",
        "status": "todo",
        "prd_id": "test_prd_456"
    }

@pytest.fixture
def sample_subtask_data():
    """Provide sample subtask data for tests."""
    return {
        "id": "test_subtask_101",
        "title": "Test Subtask",
        "description": "A test subtask",
        "completed": False,
        "task_id": "test_task_789"
    } 
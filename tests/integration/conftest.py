"""
pytest configuration and fixtures specific to integration tests.
"""

import pytest
import os
from unittest.mock import Mock

@pytest.fixture(scope="session")
def integration_github_token():
    """
    Provide GitHub token for integration tests.
    Uses environment variable GITHUB_INTEGRATION_TOKEN if available,
    otherwise skips integration tests.
    """
    token = os.getenv("GITHUB_INTEGRATION_TOKEN")
    if not token:
        pytest.skip("GITHUB_INTEGRATION_TOKEN not set, skipping integration tests")
    return token

@pytest.fixture(scope="session") 
def test_github_repo():
    """
    Provide test GitHub repository for integration tests.
    Uses environment variable GITHUB_TEST_REPO if available,
    otherwise uses a default test repo.
    """
    return os.getenv("GITHUB_TEST_REPO", "test-user/test-repo")

@pytest.fixture
def integration_test_project():
    """Provide test project data for integration tests."""
    return {
        "name": "Integration Test Project",
        "description": "Project created during integration testing"
    }

@pytest.fixture(autouse=True)
def cleanup_test_data():
    """
    Automatically clean up test data after integration tests.
    This fixture runs after each integration test to ensure
    no test data is left behind.
    """
    yield
    # Cleanup logic would go here
    # For now, just a placeholder
    pass 
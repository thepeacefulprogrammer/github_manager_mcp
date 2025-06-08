"""
Placeholder tests to ensure CI passes while we develop the core functionality.
These tests will be replaced with actual tests as we implement features.
"""

import pytest


def test_python_version():
    """Test that we're running on Python 3.10+"""
    import sys

    version = sys.version_info
    assert version.major == 3
    assert (
        version.minor >= 10
    ), f"Python 3.10+ required, got {version.major}.{version.minor}"


def test_imports():
    """Test that our core dependencies can be imported"""
    try:
        import click  # noqa: F401
        import httpx  # noqa: F401
        import mcp  # noqa: F401
        import pydantic  # noqa: F401
    except ImportError as e:
        pytest.fail(f"Failed to import required dependency: {e}")


def test_project_structure():
    """Test that our project structure exists"""
    from pathlib import Path

    # Check that main package directory exists
    package_dir = Path("src/github_project_manager_mcp")
    assert package_dir.exists(), "Main package directory should exist"
    assert (package_dir / "__init__.py").exists(), "Package __init__.py should exist"

    # Check subdirectories
    for subdir in ["handlers", "models", "utils"]:
        subdir_path = package_dir / subdir
        assert subdir_path.exists(), f"{subdir} directory should exist"
        assert (
            subdir_path / "__init__.py"
        ).exists(), f"{subdir}/__init__.py should exist"


def test_configuration_files():
    """Test that configuration files exist and are valid"""
    import os

    import toml

    # Check pyproject.toml exists and is valid
    assert os.path.exists("pyproject.toml"), "pyproject.toml should exist"

    with open("pyproject.toml", "r") as f:
        config = toml.load(f)

    assert "project" in config, "pyproject.toml should have [project] section"
    assert "name" in config["project"], "Project should have a name"
    assert config["project"]["name"] == "github-project-manager-mcp"

    # Check requirements files exist
    assert os.path.exists("requirements.txt"), "requirements.txt should exist"
    assert os.path.exists("requirements-dev.txt"), "requirements-dev.txt should exist"


def test_package_version():
    """Test that package version is accessible"""
    # Add src to path
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

    from github_project_manager_mcp import __version__

    assert __version__ == "0.1.0"


@pytest.mark.asyncio
async def test_async_functionality():
    """Test that async functionality works (needed for MCP)"""
    import asyncio

    async def simple_async_function():
        await asyncio.sleep(0.01)
        return "success"

    result = await simple_async_function()
    assert result == "success"

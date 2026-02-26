"""Pytest configuration and fixtures for RobotEditMCP tests."""

import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables from .env file before running tests.

    This fixture automatically loads environment variables from the .env file
    in the project root, ensuring tests have access to required configuration
    like ROBOT_ADMIN_TOKEN, ROBOT_BASE_URL, TF_NAMESPACE, and TF_ROBOT_ID.
    """
    # Get the project root directory (parent of src/)
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"

    if env_file.exists():
        # Read the .env file and set environment variables
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                # Parse KEY=VALUE format
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
    else:
        pytest.skip(f".env file not found at {env_file}", allow_module_level=True)


@pytest.fixture
def env_vars(load_env):
    """Provide access to loaded environment variables.

    Returns a dictionary of environment variables loaded from .env file.
    """
    return {
        "ROBOT_ADMIN_TOKEN": os.getenv("ROBOT_ADMIN_TOKEN"),
        "ROBOT_BASE_URL": os.getenv("ROBOT_BASE_URL"),
        "TF_NAMESPACE": os.getenv("TF_NAMESPACE"),
        "TF_ROBOT_ID": os.getenv("TF_ROBOT_ID"),
        "ROBOT_LOG_LEVEL": os.getenv("ROBOT_LOG_LEVEL", "INFO"),
        "API_TIMEOUT": os.getenv("API_TIMEOUT", "30"),
        "MAX_CONNECTIONS": os.getenv("MAX_CONNECTIONS", "10"),
    }

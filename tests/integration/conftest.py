"""Pytest configuration for integration tests."""

import os
import pytest
from pathlib import Path
from dotenv import load_dotenv


@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables from .env file for integration tests."""
    # Look for .env in project root
    env_path = Path(__file__).parent.parent.parent / ".env"

    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Loaded environment from {env_path}")
    else:
        print(f"⚠ No .env file found at {env_path}")
        print("  Integration tests will use system environment variables")


@pytest.fixture
def check_env_vars():
    """Check if required environment variables are set."""
    def _check(*var_names: str) -> bool:
        """Check if all given env vars are set.

        Args:
            var_names: Variable names to check

        Returns:
            True if all vars are set, False otherwise
        """
        missing = [var for var in var_names if not os.getenv(var)]
        if missing:
            pytest.skip(f"Missing required env vars: {', '.join(missing)}")
        return True

    return _check


@pytest.fixture
def is_real_test():
    """Marker to indicate this is a real API test (not mock)."""
    return True

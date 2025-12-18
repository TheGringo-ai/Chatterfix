"""
pytest configuration and fixtures
"""

import os
import sys
from unittest.mock import patch

import pytest

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="session", autouse=True)
def mock_firestore():
    """Mock Firestore for all tests"""
    with patch("app.core.firestore_db.FIRESTORE_AVAILABLE", True):
        with patch("app.core.firestore_db.firestore_db"):
            yield


@pytest.fixture(scope="session", autouse=True)
def mock_environment():
    """Set up test environment variables"""
    os.environ["GEMINI_API_KEY"] = "test_gemini_key"
    os.environ["USE_FIRESTORE"] = "true"
    yield

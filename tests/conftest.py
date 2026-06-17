"""
Pytest configuration and fixtures for FastAPI app tests.

Fixtures:
- client: TestClient for making requests to the app
- reset_activities: Fixture that resets the activities database before each test
"""

import pytest
from fastapi.testclient import TestClient
from copy import deepcopy
from src.app import app, activities


@pytest.fixture
def client():
    """
    Provides a TestClient for making HTTP requests to the FastAPI app.
    
    Yields:
        TestClient: FastAPI test client
    """
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Fixture that resets the in-memory activities database before each test.
    
    This ensures test isolation by saving the original state of activities
    and restoring it after each test.
    
    Yields:
        None (fixture is used for side effects)
    """
    # Save the original state
    original_activities = deepcopy(activities)
    
    yield
    
    # Restore the original state after the test
    activities.clear()
    activities.update(original_activities)

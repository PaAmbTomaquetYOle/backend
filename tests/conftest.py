"""Shared pytest fixtures."""

import pytest
import jwt as pyjwt
from fastapi.testclient import TestClient

from app.main import create_app

TEST_JWT_SECRET = "test-secret-for-testing-only-32chars!!"
TEST_JWT_AUDIENCE = "braintrust-backend"
TEST_JWT_ALGORITHM = "HS256"


@pytest.fixture
def client() -> TestClient:
    """Provide a TestClient bound to a fresh application instance."""
    return TestClient(create_app())


@pytest.fixture
def jwt_secret() -> str:
    """Return the shared test JWT secret."""
    return TEST_JWT_SECRET


@pytest.fixture
def auth_headers() -> dict:
    """Return Authorization headers with a valid JWT token for tests."""
    token = pyjwt.encode(
        {"iss": "test-service", "aud": TEST_JWT_AUDIENCE, "sub": "test"},
        TEST_JWT_SECRET,
        algorithm=TEST_JWT_ALGORITHM,
    )
    return {"Authorization": f"Bearer {token}"}

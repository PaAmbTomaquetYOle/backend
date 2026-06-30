"""Tests for JWT Bearer authentication."""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import jwt as pyjwt
import pytest
from fastapi.testclient import TestClient

from app.application.services.offboarding_facade_service import OffboardingFacadeService
from app.infrastructure.config.settings import Settings, get_settings
from app.infrastructure.api.dependencies import (
    offboarding_process_facade_dependency,
)
from app.main import create_app

TEST_SECRET = "test-secret-for-jwt-testing-32chars!!"
TEST_AUDIENCE = "offboardme-backend"
TEST_ALGORITHM = "HS256"


def _make_settings(**overrides) -> Settings:
    return Settings(
        jwt_secret=TEST_SECRET,
        jwt_audience=TEST_AUDIENCE,
        jwt_algorithm=TEST_ALGORITHM,
        kafka_bootstrap_servers="",
        **overrides,
    )


def _make_token(payload: dict, secret: str = TEST_SECRET) -> str:
    return pyjwt.encode(payload, secret, algorithm=TEST_ALGORITHM)


def _make_valid_token() -> str:
    return _make_token({
        "iss": "slack-agent",
        "aud": TEST_AUDIENCE,
        "sub": "slack-agent",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    })


@pytest.fixture
def auth_client() -> TestClient:
    """Client with real JWT validation using TEST_SECRET."""
    mock_facade = AsyncMock(spec=OffboardingFacadeService)
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: _make_settings()
    app.dependency_overrides[offboarding_process_facade_dependency] = lambda: mock_facade
    return TestClient(app, raise_server_exceptions=False)


class TestJWTAuthentication:
    def test_valid_token_returns_200(self, auth_client: TestClient) -> None:
        headers = {"Authorization": f"Bearer {_make_valid_token()}"}
        r = auth_client.get("/api/v1/offboarding", headers=headers)
        assert r.status_code != 401

    def test_missing_token_returns_401(self, auth_client: TestClient) -> None:
        r = auth_client.get("/api/v1/offboarding")
        assert r.status_code == 401
        assert "Missing authentication token" in r.json()["detail"]

    def test_expired_token_returns_401(self, auth_client: TestClient) -> None:
        token = _make_token({
            "iss": "slack-agent",
            "aud": TEST_AUDIENCE,
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        })
        r = auth_client.get("/api/v1/offboarding", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401
        assert "expired" in r.json()["detail"].lower()

    def test_invalid_signature_returns_401(self, auth_client: TestClient) -> None:
        token = _make_token(
            {"iss": "slack-agent", "aud": TEST_AUDIENCE, "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            secret="wrong-secret",
        )
        r = auth_client.get("/api/v1/offboarding", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401
        assert "Invalid token" in r.json()["detail"]

    def test_wrong_audience_returns_401(self, auth_client: TestClient) -> None:
        token = _make_token({
            "iss": "slack-agent",
            "aud": "wrong-audience",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        })
        r = auth_client.get("/api/v1/offboarding", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401

    def test_missing_iss_returns_401(self, auth_client: TestClient) -> None:
        token = _make_token({
            "aud": TEST_AUDIENCE,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        })
        r = auth_client.get("/api/v1/offboarding", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401
        assert "issuer" in r.json()["detail"].lower()

    def test_health_endpoint_no_auth_needed(self, auth_client: TestClient) -> None:
        r = auth_client.get("/api/v1/health")
        assert r.status_code == 200

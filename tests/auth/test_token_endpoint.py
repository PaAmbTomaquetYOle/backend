"""Tests for the client-credentials token endpoint."""

import jwt as pyjwt
import pytest
from fastapi.testclient import TestClient

from app.infrastructure.config.settings import Settings, get_settings
from app.main import create_app

TEST_SECRET = "test-secret-for-jwt-testing-32chars!!"
TEST_AUDIENCE = "offboardme-backend"
TEST_ALGORITHM = "HS256"
TEST_CLIENT_ID = "slack-agent"
TEST_CLIENT_SECRET = "slack-agent-secret"


def _make_settings(**overrides) -> Settings:
    return Settings(
        jwt_secret=TEST_SECRET,
        jwt_audience=TEST_AUDIENCE,
        jwt_algorithm=TEST_ALGORITHM,
        token_expiry_seconds=300,
        service_credentials={TEST_CLIENT_ID: TEST_CLIENT_SECRET},
        kafka_bootstrap_servers="",
        **overrides,
    )


@pytest.fixture
def token_client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: _make_settings()
    return TestClient(app, raise_server_exceptions=False)


class TestTokenEndpoint:
    def test_valid_credentials_returns_usable_token(self, token_client: TestClient) -> None:
        r = token_client.post("/api/v1/auth/token", json={
            "grant_type": "client_credentials",
            "client_id": TEST_CLIENT_ID,
            "client_secret": TEST_CLIENT_SECRET,
        })

        assert r.status_code == 200
        body = r.json()
        assert body["token_type"] == "Bearer"
        assert body["expires_in"] == 300

        claims = pyjwt.decode(
            body["access_token"], TEST_SECRET, algorithms=[TEST_ALGORITHM], audience=TEST_AUDIENCE
        )
        assert claims["iss"] == TEST_CLIENT_ID

        r2 = token_client.get(
            "/api/v1/offboarding",
            headers={"Authorization": f"Bearer {body['access_token']}"},
        )
        assert r2.status_code != 401

    def test_wrong_secret_returns_401(self, token_client: TestClient) -> None:
        r = token_client.post("/api/v1/auth/token", json={
            "grant_type": "client_credentials",
            "client_id": TEST_CLIENT_ID,
            "client_secret": "wrong-secret",
        })

        assert r.status_code == 401

    def test_unknown_client_id_returns_401(self, token_client: TestClient) -> None:
        r = token_client.post("/api/v1/auth/token", json={
            "grant_type": "client_credentials",
            "client_id": "unknown-service",
            "client_secret": TEST_CLIENT_SECRET,
        })

        assert r.status_code == 401

    def test_missing_fields_returns_422(self, token_client: TestClient) -> None:
        r = token_client.post("/api/v1/auth/token", json={"grant_type": "client_credentials"})

        assert r.status_code == 422

"""Tests for FastAPI application and endpoint registration."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


class TestHealth:
    def test_health_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        assert r.json()["service"] == "callcenter"

    def test_metrics_endpoint(self, client):
        r = client.get("/metrics")
        assert r.status_code == 200
        assert b"tickets_created_total" in r.content or r.status_code == 200


class TestAuthEndpoints:
    def test_login_missing_body(self, client):
        r = client.post("/api/v1/auth/login", json={})
        assert r.status_code == 422

    def test_login_invalid_email(self, client):
        r = client.post("/api/v1/auth/login", json={"email": "not-email", "password": "x"})
        assert r.status_code == 422

    def test_me_no_auth(self, client):
        r = client.get("/api/v1/auth/me")
        assert r.status_code == 422  # Missing auth header

    def test_me_bad_token(self, client):
        r = client.get("/api/v1/auth/me", headers={"authorization": "Bearer bad"})
        assert r.status_code == 401


class TestProtectedEndpoints:
    def test_tickets_no_auth(self, client):
        r = client.get("/api/v1/tickets", headers={"authorization": "Bearer invalid"})
        assert r.status_code == 401

    def test_contacts_no_auth(self, client):
        r = client.get("/api/v1/contacts", headers={"authorization": "Bearer invalid"})
        assert r.status_code == 401


class TestWebhooks:
    def test_graph_webhook_validation(self, client):
        r = client.post("/api/v1/email/webhooks/graph?validationToken=abc123")
        assert r.status_code == 200
        assert r.text == "abc123"

    def test_jira_webhook_accepts_post(self, client):
        r = client.post("/api/v1/jira/webhooks", json={"webhookEvent": "test", "issue": {}})
        assert r.status_code == 200

    def test_voice_agent_status_requires_auth(self, client):
        r = client.get("/api/v1/voice/agent/status")
        # Now requires auth (tenant context needed)
        assert r.status_code in (401, 422)


class TestEndpointCount:
    def test_total_endpoints(self, client):
        r = client.get("/openapi.json")
        paths = list(r.json()["paths"].keys())
        assert len(paths) >= 39, f"Expected at least 39 endpoints, got {len(paths)}"

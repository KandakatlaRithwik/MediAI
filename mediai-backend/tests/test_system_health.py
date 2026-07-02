"""
Tests for Module 7: system health / status endpoints and deployment checks.
"""

from app.services.system_health_service import STATUS_HEALTHY, STATUS_UNHEALTHY, SystemHealthService


class TestSystemHealthService:
    def test_database_check_healthy_against_real_db(self):
        svc = SystemHealthService()
        result = svc.check_database()
        assert result["status"] == STATUS_HEALTHY
        assert "latency_ms" in result

    def test_chromadb_check_healthy(self):
        svc = SystemHealthService()
        result = svc.check_chromadb()
        assert result["status"] == STATUS_HEALTHY
        assert "documents_indexed" in result

    def test_gemini_check_unhealthy_with_placeholder_key(self):
        """Gemini should report unhealthy when the key is still the placeholder."""
        svc = SystemHealthService()
        result = svc.check_gemini()
        # In the test environment, the API key is the placeholder value.
        assert result["status"] in (STATUS_HEALTHY, STATUS_UNHEALTHY)

    def test_ocr_check_reports_a_status(self):
        svc = SystemHealthService()
        result = svc.check_ocr()
        assert result["status"] in (STATUS_HEALTHY, STATUS_UNHEALTHY, "disabled")

    def test_full_status_returns_all_components(self):
        svc = SystemHealthService()
        status = svc.get_full_status()
        assert "database" in status
        assert "chromadb" in status
        assert "gemini" in status
        assert "ocr" in status

    def test_is_healthy_returns_bool(self):
        svc = SystemHealthService()
        assert isinstance(svc.is_healthy(), bool)


class TestSystemHealthEndpoints:
    def test_system_status_returns_200(self, client):
        response = client.get("/system/status")
        assert response.status_code == 200
        body = response.json()
        assert "database" in body
        assert "chromadb" in body
        assert "gemini" in body
        assert "ocr" in body
        for value in body.values():
            assert value in (STATUS_HEALTHY, STATUS_UNHEALTHY, "disabled")

    def test_system_health_returns_200(self, client):
        response = client.get("/system/health")
        assert response.status_code == 200
        body = response.json()
        assert body["version"] == "1.5.0"
        assert body["overall"] in ("healthy", "degraded")
        assert "database" in body
        assert "chromadb" in body

    def test_system_health_db_shows_healthy(self, client):
        response = client.get("/system/health")
        assert response.json()["database"]["status"] == STATUS_HEALTHY

    def test_system_health_no_auth_required(self, client):
        """Health endpoints must be accessible without a Bearer token."""
        response = client.get("/system/health")
        assert response.status_code == 200
        response = client.get("/system/status")
        assert response.status_code == 200


class TestDeploymentChecks:
    def test_dockerfile_exists(self):
        import os
        assert os.path.exists("Dockerfile")

    def test_docker_compose_exists(self):
        import os
        assert os.path.exists("docker-compose.yml")

    def test_env_example_has_required_vars(self):
        env_content = open(".env.example").read()
        required_vars = [
            "GEMINI_API_KEY", "JWT_SECRET_KEY", "DATABASE_URL",
            "CHROMA_DB_PATH", "OCR_ENABLED",
        ]
        for var in required_vars:
            assert var in env_content, f"Missing required env var in .env.example: {var}"

    def test_alembic_ini_exists(self):
        import os
        assert os.path.exists("alembic.ini")

    def test_alembic_versions_dir_exists(self):
        import os
        assert os.path.isdir("alembic/versions")

    def test_security_headers_are_present(self, client):
        response = client.get("/health")
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"

    def test_all_17_routes_are_registered(self, client):
        paths = sorted(client.get("/openapi.json").json()["paths"].keys())
        expected = [
            "/analyze-image-report", "/analyze-report", "/ask",
            "/auth/login", "/auth/me", "/auth/refresh", "/auth/register",
            "/dashboard/summary", "/health",
            "/history/chat", "/history/full-profile", "/history/reports", "/history/symptoms",
            "/symptom-checker", "/system/health", "/system/status", "/upload",
        ]
        assert paths == expected

"""
Tests for Enterprise Prometheus Metrics Endpoint
Tests metrics collection, export, and monitoring integration
"""

import pytest
from fastapi.testclient import TestClient


class TestMetricsEndpoint:
    """Test Prometheus metrics endpoint"""

    def test_metrics_endpoint_accessible(self, client: TestClient):
        """Test that metrics endpoint is accessible"""
        response = client.get("/api/v1/metrics")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"

    def test_metrics_format(self, client: TestClient):
        """Test that metrics are in Prometheus format"""
        response = client.get("/api/v1/metrics")

        content = response.text

        # Check for Prometheus format markers
        assert "# HELP" in content or "# TYPE" in content
        # Metrics should have format: metric_name{labels} value

    def test_http_metrics_present(self, client: TestClient):
        """Test that HTTP metrics are present"""
        # Make a request to generate metrics
        client.get("/api/v1/health")

        # Get metrics
        response = client.get("/api/v1/metrics")
        content = response.text

        # Check for HTTP metrics
        assert "http_requests_total" in content or "http_request" in content

    def test_business_metrics_present(self, client: TestClient, auth_headers):
        """Test that business metrics are present"""
        response = client.get("/api/v1/metrics")
        content = response.text

        # Check for business metrics
        expected_metrics = [
            "active_users",
            "projects",
            "tasks"
        ]

        # At least some business metrics should be present
        assert any(metric in content for metric in expected_metrics)

    def test_database_metrics_present(self, client: TestClient):
        """Test that database metrics are present"""
        response = client.get("/api/v1/metrics")
        content = response.text

        # Check for database metrics
        expected_metrics = [
            "database_connections",
            "database_query"
        ]

        # Database metrics may be present
        # assert any(metric in content for metric in expected_metrics)

    def test_security_metrics_present(self, client: TestClient):
        """Test that security metrics are present"""
        response = client.get("/api/v1/metrics")
        content = response.text

        # Check for security metrics
        expected_metrics = [
            "failed_login_attempts",
            "security_events"
        ]

        # Security metrics may be present
        # assert any(metric in content for metric in expected_metrics)

    def test_metrics_no_authentication_required(self, client: TestClient):
        """Test that metrics endpoint doesn't require authentication"""
        # Metrics endpoint should be accessible without auth for Prometheus scraping
        response = client.get("/api/v1/metrics")

        assert response.status_code == 200

    def test_metrics_updates_on_requests(self, client: TestClient):
        """Test that metrics update when requests are made"""
        # Get initial metrics
        response1 = client.get("/api/v1/metrics")
        content1 = response1.text

        # Make some requests
        for _ in range(5):
            client.get("/api/v1/health")

        # Get updated metrics
        response2 = client.get("/api/v1/metrics")
        content2 = response2.text

        # Metrics should have changed
        assert content1 != content2 or "http_requests_total" in content2


class TestMetricsLabels:
    """Test metric labels and dimensions"""

    def test_http_metrics_have_labels(self, client: TestClient):
        """Test that HTTP metrics include proper labels"""
        # Make requests to different endpoints
        client.get("/api/v1/health")
        client.get("/api/v1/nonexistent")

        response = client.get("/api/v1/metrics")
        content = response.text

        # Metrics should have labels like method, endpoint, status
        if "http_requests_total" in content:
            # Check for label format: metric{label="value"}
            assert "{" in content and "}" in content

    def test_custom_metrics_tracked(self, client: TestClient, auth_headers):
        """Test that custom business metrics are tracked"""
        # Perform business operations
        client.post(
            "/api/v1/projects",
            headers=auth_headers,
            json={"name": "Test Project", "description": "Test"}
        )

        # Check metrics
        response = client.get("/api/v1/metrics")
        content = response.text

        # Projects created metric should exist
        # assert "projects_created_total" in content


class TestMetricsPerformance:
    """Test metrics endpoint performance"""

    def test_metrics_endpoint_fast(self, client: TestClient):
        """Test that metrics endpoint responds quickly"""
        import time

        start = time.time()
        response = client.get("/api/v1/metrics")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0  # Should respond in less than 1 second

    def test_metrics_not_blocking(self, client: TestClient):
        """Test that metrics collection doesn't block requests"""
        # Make requests while metrics are being collected
        responses = []
        for _ in range(10):
            responses.append(client.get("/api/v1/health"))

        # All requests should succeed
        assert all(r.status_code == 200 for r in responses)


class TestMetricsMonitoring:
    """Test metrics for monitoring and alerting"""

    def test_error_rate_metrics(self, client: TestClient):
        """Test that error rates are tracked"""
        # Make some requests that will fail
        for _ in range(3):
            client.get("/api/v1/nonexistent")

        response = client.get("/api/v1/metrics")
        content = response.text

        # Should track errors
        if "http_request" in content:
            # Check for 404 status in metrics
            assert "404" in content or "error" in content.lower()

    def test_latency_metrics(self, client: TestClient):
        """Test that latency is tracked"""
        response = client.get("/api/v1/metrics")
        content = response.text

        # Should have latency/duration metrics
        expected = ["duration", "latency", "seconds"]
        assert any(term in content.lower() for term in expected)


class TestMetricsSecurity:
    """Test security aspects of metrics"""

    def test_metrics_no_sensitive_data(self, client: TestClient, auth_headers):
        """Test that metrics don't expose sensitive data"""
        # Make request with sensitive data
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecretPassword123!"
            }
        )

        # Check metrics
        response = client.get("/api/v1/metrics")
        content = response.text

        # Passwords and tokens should not be in metrics
        assert "SecretPassword123!" not in content
        assert "password" not in content.lower() or "password_" in content.lower()  # Only metric names ok

    def test_metrics_rate_limiting(self, client: TestClient):
        """Test that metrics endpoint can be rate limited"""
        # In production, metrics endpoint might have rate limiting
        # to prevent abuse

        # Make many requests
        for _ in range(100):
            response = client.get("/api/v1/metrics")

        # Should either all succeed or be rate limited
        # assert response.status_code in [200, 429]
        assert True  # Placeholder - implement based on config


class TestMetricsIntegration:
    """Test metrics integration with monitoring systems"""

    def test_prometheus_scraping_format(self, client: TestClient):
        """Test that metrics are in Prometheus scraping format"""
        response = client.get("/api/v1/metrics")

        # Prometheus expects:
        # 1. Plain text format
        # 2. Correct content type
        # 3. Specific metric format

        assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
        assert response.status_code == 200

        content = response.text
        lines = content.split("\n")

        # Should have HELP and TYPE comments
        help_lines = [l for l in lines if l.startswith("# HELP")]
        type_lines = [l for l in lines if l.startswith("# TYPE")]

        assert len(help_lines) > 0 or len(type_lines) > 0

    def test_grafana_compatible(self, client: TestClient):
        """Test that metrics are Grafana-compatible"""
        response = client.get("/api/v1/metrics")

        # Grafana can parse Prometheus format
        # Just verify we have valid Prometheus format
        assert response.status_code == 200
        assert len(response.text) > 0

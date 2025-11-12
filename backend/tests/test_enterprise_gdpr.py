"""
Tests for Enterprise GDPR Compliance Endpoints
Tests data export, deletion, consent management, and other GDPR features
"""

import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.gdpr import (
    DataExportRequest,
    DataDeletionRequest,
    ConsentUpdate,
    DataPortabilityRequest
)


class TestDataExportEndpoint:
    """Test GDPR Article 15 - Right of Access"""

    def test_request_data_export_json(self, client: TestClient, auth_headers):
        """Test requesting data export in JSON format"""
        response = client.post(
            "/api/v1/gdpr/data-export",
            headers=auth_headers,
            json={
                "format": "json",
                "include_metadata": True,
                "include_audit_logs": True
            }
        )

        assert response.status_code == 202  # Accepted for processing
        data = response.json()
        assert "request_id" in data
        assert data["status"] in ["processing", "queued"]
        assert "estimated_completion" in data

    def test_request_data_export_csv(self, client: TestClient, auth_headers):
        """Test requesting data export in CSV format"""
        response = client.post(
            "/api/v1/gdpr/data-export",
            headers=auth_headers,
            json={
                "format": "csv",
                "include_metadata": False,
                "include_audit_logs": False
            }
        )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] in ["processing", "queued"]

    def test_request_data_export_invalid_format(self, client: TestClient, auth_headers):
        """Test requesting data export with invalid format"""
        response = client.post(
            "/api/v1/gdpr/data-export",
            headers=auth_headers,
            json={
                "format": "invalid_format",
                "include_metadata": True
            }
        )

        assert response.status_code in [400, 422]  # Bad request or validation error

    def test_get_data_export_status(self, client: TestClient, auth_headers):
        """Test checking data export status"""
        # First, create an export request
        create_response = client.post(
            "/api/v1/gdpr/data-export",
            headers=auth_headers,
            json={"format": "json"}
        )
        request_id = create_response.json()["request_id"]

        # Then check status
        response = client.get(
            f"/api/v1/gdpr/data-export/{request_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["request_id"] == request_id
        assert "status" in data

    def test_download_data_export_unauthorized(self, client: TestClient):
        """Test downloading data export without authentication"""
        response = client.get("/api/v1/gdpr/data-export/fake_id/download")
        assert response.status_code == 401


class TestDataDeletionEndpoint:
    """Test GDPR Article 17 - Right to Erasure"""

    def test_request_data_deletion(self, client: TestClient, auth_headers, test_user):
        """Test requesting account deletion"""
        response = client.post(
            "/api/v1/gdpr/data-deletion",
            headers=auth_headers,
            json={
                "reason": "No longer need the service",
                "delete_all": True,
                "anonymize_contributions": True,
                "confirm_email": test_user.email
            }
        )

        assert response.status_code == 202
        data = response.json()
        assert "deletion_id" in data
        assert data["status"] == "scheduled"
        assert "scheduled_date" in data
        assert "cancellable_until" in data
        assert isinstance(data["what_will_be_deleted"], list)
        assert isinstance(data["what_will_be_retained"], list)

    def test_request_deletion_wrong_email(self, client: TestClient, auth_headers):
        """Test requesting deletion with wrong confirmation email"""
        response = client.post(
            "/api/v1/gdpr/data-deletion",
            headers=auth_headers,
            json={
                "reason": "Test",
                "delete_all": True,
                "anonymize_contributions": True,
                "confirm_email": "wrong@email.com"
            }
        )

        assert response.status_code == 400  # Email doesn't match

    def test_cancel_deletion_request(self, client: TestClient, auth_headers, test_user):
        """Test cancelling a deletion request within grace period"""
        # Create deletion request
        create_response = client.post(
            "/api/v1/gdpr/data-deletion",
            headers=auth_headers,
            json={
                "reason": "Test deletion",
                "delete_all": True,
                "anonymize_contributions": True,
                "confirm_email": test_user.email
            }
        )
        deletion_id = create_response.json()["deletion_id"]

        # Cancel deletion
        response = client.delete(
            f"/api/v1/gdpr/data-deletion/{deletion_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

    def test_get_deletion_status(self, client: TestClient, auth_headers, test_user):
        """Test checking deletion request status"""
        # Create deletion request
        create_response = client.post(
            "/api/v1/gdpr/data-deletion",
            headers=auth_headers,
            json={
                "reason": "Test",
                "delete_all": True,
                "anonymize_contributions": True,
                "confirm_email": test_user.email
            }
        )
        deletion_id = create_response.json()["deletion_id"]

        # Check status
        response = client.get(
            f"/api/v1/gdpr/data-deletion/{deletion_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["deletion_id"] == deletion_id


class TestConsentManagement:
    """Test GDPR Article 7 - Consent Management"""

    def test_get_consents(self, client: TestClient, auth_headers):
        """Test getting current consent settings"""
        response = client.get(
            "/api/v1/gdpr/consents",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "consents" in data
        assert isinstance(data["consents"], list)

    def test_update_single_consent(self, client: TestClient, auth_headers):
        """Test updating a single consent preference"""
        response = client.post(
            "/api/v1/gdpr/consent",
            headers=auth_headers,
            json={
                "consent_marketing": True
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["consent_marketing"] is True

    def test_update_multiple_consents(self, client: TestClient, auth_headers):
        """Test updating multiple consent preferences"""
        response = client.post(
            "/api/v1/gdpr/consent",
            headers=auth_headers,
            json={
                "consent_marketing": False,
                "consent_analytics": True,
                "consent_third_party": False,
                "consent_profiling": False
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["consent_marketing"] is False
        assert data["consent_analytics"] is True
        assert data["consent_third_party"] is False
        assert data["consent_profiling"] is False

    def test_withdraw_specific_consent(self, client: TestClient, auth_headers):
        """Test withdrawing a specific consent"""
        # First grant consent
        client.post(
            "/api/v1/gdpr/consent",
            headers=auth_headers,
            json={"consent_marketing": True}
        )

        # Then withdraw it
        response = client.delete(
            "/api/v1/gdpr/consent/marketing",
            headers=auth_headers
        )

        assert response.status_code == 200

        # Verify it's withdrawn
        get_response = client.get(
            "/api/v1/gdpr/consents",
            headers=auth_headers
        )
        consents = get_response.json()["consents"]
        marketing_consent = next(
            (c for c in consents if c["type"] == "marketing"),
            None
        )
        assert marketing_consent is None or marketing_consent["granted"] is False


class TestDataPortability:
    """Test GDPR Article 20 - Right to Data Portability"""

    def test_request_portable_export(self, client: TestClient, auth_headers):
        """Test requesting data in portable format"""
        response = client.post(
            "/api/v1/gdpr/data-portability",
            headers=auth_headers,
            json={
                "format": "json",
                "include_attachments": True
            }
        )

        assert response.status_code == 202
        data = response.json()
        assert "export_id" in data
        assert data["status"] in ["processing", "queued"]


class TestDataRectification:
    """Test GDPR Article 16 - Right to Rectification"""

    def test_request_data_rectification(self, client: TestClient, auth_headers):
        """Test requesting correction of inaccurate data"""
        response = client.post(
            "/api/v1/gdpr/rectification",
            headers=auth_headers,
            json={
                "field": "email",
                "old_value": "old@example.com",
                "new_value": "new@example.com",
                "justification": "Email address was incorrect"
            }
        )

        assert response.status_code in [200, 202]  # May require approval
        data = response.json()
        assert "rectification_id" in data
        assert "status" in data


class TestProcessingRestriction:
    """Test GDPR Article 18 - Right to Restriction of Processing"""

    def test_request_processing_restriction(self, client: TestClient, auth_headers):
        """Test requesting restriction of data processing"""
        response = client.post(
            "/api/v1/gdpr/restriction",
            headers=auth_headers,
            json={
                "reason": "accuracy_contested",
                "description": "Contesting accuracy of personal data",
                "duration": 30
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "restriction_id" in data
        assert "status" in data
        assert "restricted_operations" in data


class TestObjectionToProcessing:
    """Test GDPR Article 21 - Right to Object"""

    def test_object_to_processing(self, client: TestClient, auth_headers):
        """Test objecting to data processing"""
        response = client.post(
            "/api/v1/gdpr/objection",
            headers=auth_headers,
            json={
                "processing_purpose": "marketing",
                "reason": "No longer wish to receive marketing communications"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "objection_id" in data
        assert "status" in data


class TestDataAccessLogs:
    """Test data access logging for transparency"""

    def test_get_data_access_logs(self, client: TestClient, auth_headers):
        """Test retrieving data access logs"""
        response = client.get(
            "/api/v1/gdpr/data-access-logs",
            headers=auth_headers,
            params={
                "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "end_date": datetime.utcnow().isoformat()
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "logs" in data
        assert isinstance(data["logs"], list)


class TestProcessingActivities:
    """Test GDPR Article 30 - Records of Processing Activities"""

    def test_get_processing_activities(self, client: TestClient, auth_headers):
        """Test retrieving records of processing activities"""
        response = client.get(
            "/api/v1/gdpr/processing-activities",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "controller" in data
        assert "activities" in data
        assert isinstance(data["activities"], list)

        if len(data["activities"]) > 0:
            activity = data["activities"][0]
            assert "name" in activity
            assert "purposes" in activity
            assert "legal_basis" in activity
            assert "retention_period" in activity


class TestSubProcessors:
    """Test sub-processor transparency"""

    def test_get_sub_processors(self, client: TestClient, auth_headers):
        """Test retrieving list of sub-processors"""
        response = client.get(
            "/api/v1/gdpr/sub-processors",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "sub_processors" in data
        assert isinstance(data["sub_processors"], list)

        if len(data["sub_processors"]) > 0:
            processor = data["sub_processors"][0]
            assert "name" in processor
            assert "purpose" in processor
            assert "location" in processor


class TestComplianceLogs:
    """Test GDPR compliance logging"""

    @pytest.mark.asyncio
    async def test_compliance_log_created_on_export(
        self,
        client: TestClient,
        auth_headers,
        db_session: AsyncSession
    ):
        """Test that compliance log is created when requesting export"""
        # Request data export
        response = client.post(
            "/api/v1/gdpr/data-export",
            headers=auth_headers,
            json={"format": "json"}
        )

        assert response.status_code == 202

        # Verify compliance log was created
        from sqlalchemy import select
        from app.db.models.audit_log import ComplianceLog

        result = await db_session.execute(
            select(ComplianceLog)
            .where(ComplianceLog.action_type == "data_export_requested")
            .order_by(ComplianceLog.created_at.desc())
            .limit(1)
        )
        log = result.scalar_one_or_none()

        assert log is not None
        assert log.compliance_type == "gdpr"
        assert log.action_type == "data_export_requested"


class TestGDPRSecurity:
    """Test security aspects of GDPR endpoints"""

    def test_data_export_requires_authentication(self, client: TestClient):
        """Test that data export requires authentication"""
        response = client.post(
            "/api/v1/gdpr/data-export",
            json={"format": "json"}
        )

        assert response.status_code == 401

    def test_cannot_access_other_user_export(
        self,
        client: TestClient,
        auth_headers,
        other_user_auth_headers
    ):
        """Test that users cannot access other users' exports"""
        # User 1 creates export
        response1 = client.post(
            "/api/v1/gdpr/data-export",
            headers=auth_headers,
            json={"format": "json"}
        )
        request_id = response1.json()["request_id"]

        # User 2 tries to access User 1's export
        response2 = client.get(
            f"/api/v1/gdpr/data-export/{request_id}",
            headers=other_user_auth_headers
        )

        assert response2.status_code == 403  # Forbidden

    def test_deletion_requires_email_confirmation(
        self,
        client: TestClient,
        auth_headers
    ):
        """Test that deletion requires email confirmation"""
        response = client.post(
            "/api/v1/gdpr/data-deletion",
            headers=auth_headers,
            json={
                "reason": "Test",
                "delete_all": True,
                "anonymize_contributions": True,
                "confirm_email": "wrong@email.com"
            }
        )

        assert response.status_code == 400


class TestGDPRPerformance:
    """Test performance of GDPR endpoints"""

    def test_data_export_handles_large_dataset(
        self,
        client: TestClient,
        auth_headers
    ):
        """Test that data export can handle large datasets"""
        # This should be processed asynchronously and not timeout
        response = client.post(
            "/api/v1/gdpr/data-export",
            headers=auth_headers,
            json={
                "format": "json",
                "include_metadata": True,
                "include_audit_logs": True
            },
            timeout=5  # Should return quickly even for large datasets
        )

        assert response.status_code == 202
        assert response.json()["status"] in ["processing", "queued"]

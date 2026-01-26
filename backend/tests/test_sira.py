# tests/test_sira.py
"""
Comprehensive tests for SIRA Platform endpoints.
Tests movements, alerts, cases, playbooks, and evidence APIs.
"""
import pytest


class TestMovements:
    """Tests for the movements API."""

    def test_create_movement(self, client, auth_headers, sample_movement_data):
        """Test creating a new movement."""
        response = client.post(
            "/movements/",
            json=sample_movement_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["cargo"] == sample_movement_data["cargo"]
        assert data["route"] == sample_movement_data["route"]
        assert "id" in data

    def test_create_movement_unauthorized(self, client, sample_movement_data):
        """Test creating movement without authentication fails."""
        response = client.post("/movements/", json=sample_movement_data)
        assert response.status_code == 401

    def test_list_movements(self, client, auth_headers, sample_movement_data):
        """Test listing movements."""
        # Create a movement first
        client.post("/movements/", json=sample_movement_data, headers=auth_headers)

        response = client.get("/movements/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_movement(self, client, auth_headers, sample_movement_data):
        """Test getting a single movement."""
        # Create a movement first
        create_response = client.post(
            "/movements/",
            json=sample_movement_data,
            headers=auth_headers
        )
        movement_id = create_response.json()["id"]

        response = client.get(f"/movements/{movement_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == movement_id

    def test_get_movement_not_found(self, client, auth_headers):
        """Test getting non-existent movement returns 404."""
        response = client.get("/movements/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_update_movement(self, client, auth_headers, sample_movement_data):
        """Test updating a movement."""
        # Create a movement first
        create_response = client.post(
            "/movements/",
            json=sample_movement_data,
            headers=auth_headers
        )
        movement_id = create_response.json()["id"]

        update_data = {"cargo": "Updated Cargo - 100,000 barrels"}
        response = client.put(
            f"/movements/{movement_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["cargo"] == "Updated Cargo - 100,000 barrels"

    def test_delete_movement(self, client, auth_headers, sample_movement_data):
        """Test deleting a movement."""
        # Create a movement first
        create_response = client.post(
            "/movements/",
            json=sample_movement_data,
            headers=auth_headers
        )
        movement_id = create_response.json()["id"]

        response = client.delete(f"/movements/{movement_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(f"/movements/{movement_id}", headers=auth_headers)
        assert get_response.status_code == 404


class TestShipmentEvents:
    """Tests for shipment events within movements."""

    def test_create_shipment_event(self, client, auth_headers, sample_movement_data):
        """Test creating a shipment event."""
        # Create a movement first
        create_response = client.post(
            "/movements/",
            json=sample_movement_data,
            headers=auth_headers
        )
        movement_id = create_response.json()["id"]

        event_data = {
            "movement_id": movement_id,
            "timestamp": "2026-01-26T10:00:00",
            "location": "Lagos Port",
            "actor": "Port Authority",
            "evidence_ref": "/logs/departure.json",
            "event_type": "actual"
        }

        response = client.post(
            f"/movements/{movement_id}/events",
            json=event_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        assert response.json()["location"] == "Lagos Port"

    def test_list_shipment_events(self, client, auth_headers, sample_movement_data):
        """Test listing shipment events for a movement."""
        # Create a movement and event
        create_response = client.post(
            "/movements/",
            json=sample_movement_data,
            headers=auth_headers
        )
        movement_id = create_response.json()["id"]

        event_data = {
            "movement_id": movement_id,
            "location": "Lagos Port",
            "actor": "Port Authority",
            "event_type": "actual"
        }
        client.post(
            f"/movements/{movement_id}/events",
            json=event_data,
            headers=auth_headers
        )

        response = client.get(f"/movements/{movement_id}/events", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestAlerts:
    """Tests for the alerts API."""

    def test_create_alert(self, client, security_lead_auth_headers, sample_alert_data):
        """Test creating a new alert (requires security_lead role)."""
        response = client.post(
            "/alerts/",
            json=sample_alert_data,
            headers=security_lead_auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["severity"] == sample_alert_data["severity"]
        assert data["status"] == "open"

    def test_create_alert_forbidden(self, client, auth_headers, sample_alert_data):
        """Test that operators cannot create alerts."""
        response = client.post(
            "/alerts/",
            json=sample_alert_data,
            headers=auth_headers
        )
        assert response.status_code == 403

    def test_list_alerts(self, client, auth_headers, security_lead_auth_headers, sample_alert_data):
        """Test listing alerts with filtering."""
        # Create an alert first
        client.post("/alerts/", json=sample_alert_data, headers=security_lead_auth_headers)

        response = client.get("/alerts/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_alerts_with_filter(self, client, auth_headers, security_lead_auth_headers, sample_alert_data):
        """Test filtering alerts by domain."""
        client.post("/alerts/", json=sample_alert_data, headers=security_lead_auth_headers)

        response = client.get(
            "/alerts/",
            params={"domain": "Maritime Security"},
            headers=auth_headers
        )
        assert response.status_code == 200
        for alert in response.json():
            assert alert["domain"] == "Maritime Security"

    def test_acknowledge_alert(self, client, auth_headers, security_lead_auth_headers, sample_alert_data):
        """Test acknowledging an alert."""
        create_response = client.post(
            "/alerts/",
            json=sample_alert_data,
            headers=security_lead_auth_headers
        )
        alert_id = create_response.json()["id"]

        response = client.post(
            f"/alerts/{alert_id}/acknowledge",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "acknowledged"

    def test_close_alert(self, client, auth_headers, security_lead_auth_headers, sample_alert_data):
        """Test closing an alert."""
        create_response = client.post(
            "/alerts/",
            json=sample_alert_data,
            headers=security_lead_auth_headers
        )
        alert_id = create_response.json()["id"]

        response = client.post(
            f"/alerts/{alert_id}/close",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "closed"


class TestCases:
    """Tests for the cases API."""

    def test_create_case(self, client, auth_headers, sample_case_data):
        """Test creating a new case."""
        response = client.post(
            "/cases/",
            json=sample_case_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["overview"] == sample_case_data["overview"]
        assert data["status"] == "open"

    def test_list_cases(self, client, auth_headers, sample_case_data):
        """Test listing cases."""
        client.post("/cases/", json=sample_case_data, headers=auth_headers)

        response = client.get("/cases/", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_case(self, client, auth_headers, sample_case_data):
        """Test getting a single case."""
        create_response = client.post(
            "/cases/",
            json=sample_case_data,
            headers=auth_headers
        )
        case_id = create_response.json()["id"]

        response = client.get(f"/cases/{case_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == case_id

    def test_update_case(self, client, auth_headers, sample_case_data):
        """Test updating a case."""
        create_response = client.post(
            "/cases/",
            json=sample_case_data,
            headers=auth_headers
        )
        case_id = create_response.json()["id"]

        update_data = {"costs": 5000.0}
        response = client.put(
            f"/cases/{case_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["costs"] == 5000.0

    def test_close_case(self, client, security_lead_auth_headers, sample_case_data):
        """Test closing a case."""
        create_response = client.post(
            "/cases/",
            json=sample_case_data,
            headers=security_lead_auth_headers
        )
        case_id = create_response.json()["id"]

        response = client.put(
            f"/cases/{case_id}/close",
            json={"closure_code": "RESOLVED_NO_INCIDENT"},
            headers=security_lead_auth_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "closed"
        assert response.json()["closure_code"] == "RESOLVED_NO_INCIDENT"

    def test_close_case_forbidden(self, client, auth_headers, sample_case_data):
        """Test that operators cannot close cases."""
        create_response = client.post(
            "/cases/",
            json=sample_case_data,
            headers=auth_headers
        )
        case_id = create_response.json()["id"]

        response = client.put(
            f"/cases/{case_id}/close",
            json={"closure_code": "RESOLVED"},
            headers=auth_headers
        )
        assert response.status_code == 403

    def test_export_case(self, client, auth_headers, sample_case_data):
        """Test exporting case compliance pack."""
        create_response = client.post(
            "/cases/",
            json=sample_case_data,
            headers=auth_headers
        )
        case_id = create_response.json()["id"]

        response = client.get(f"/cases/{case_id}/export", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["case_id"] == case_id


class TestPlaybooks:
    """Tests for the playbooks API."""

    def test_create_playbook(self, client, security_lead_auth_headers, sample_playbook_data):
        """Test creating a new playbook."""
        response = client.post(
            "/playbooks/",
            json=sample_playbook_data,
            headers=security_lead_auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["incident_type"] == sample_playbook_data["incident_type"]

    def test_create_playbook_forbidden(self, client, auth_headers, sample_playbook_data):
        """Test that operators cannot create playbooks."""
        response = client.post(
            "/playbooks/",
            json=sample_playbook_data,
            headers=auth_headers
        )
        assert response.status_code == 403

    def test_list_playbooks(self, client, auth_headers, security_lead_auth_headers, sample_playbook_data):
        """Test listing playbooks."""
        client.post("/playbooks/", json=sample_playbook_data, headers=security_lead_auth_headers)

        response = client.get("/playbooks/", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_filter_playbooks_by_incident_type(
        self, client, auth_headers, security_lead_auth_headers, sample_playbook_data
    ):
        """Test filtering playbooks by incident type."""
        client.post("/playbooks/", json=sample_playbook_data, headers=security_lead_auth_headers)

        response = client.get(
            "/playbooks/",
            params={"incident_type": "Piracy Attempt"},
            headers=auth_headers
        )
        assert response.status_code == 200
        for playbook in response.json():
            assert playbook["incident_type"] == "Piracy Attempt"

    def test_delete_playbook(self, client, security_lead_auth_headers, sample_playbook_data):
        """Test deleting a playbook."""
        create_response = client.post(
            "/playbooks/",
            json=sample_playbook_data,
            headers=security_lead_auth_headers
        )
        playbook_id = create_response.json()["id"]

        response = client.delete(
            f"/playbooks/{playbook_id}",
            headers=security_lead_auth_headers
        )
        assert response.status_code == 204


class TestEvidence:
    """Tests for the evidence API."""

    def test_upload_evidence(self, client, auth_headers, sample_case_data, sample_evidence_data):
        """Test uploading evidence."""
        # Create a case first
        case_response = client.post(
            "/cases/",
            json=sample_case_data,
            headers=auth_headers
        )
        case_id = case_response.json()["id"]

        evidence_data = {**sample_evidence_data, "case_id": case_id}
        response = client.post(
            "/evidence/",
            json=evidence_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["file_ref"] == sample_evidence_data["file_ref"]
        assert data["verification_status"] == "pending"
        assert "file_hash" in data

    def test_list_evidence(self, client, auth_headers, sample_case_data, sample_evidence_data):
        """Test listing evidence."""
        # Create case and evidence
        case_response = client.post(
            "/cases/",
            json=sample_case_data,
            headers=auth_headers
        )
        case_id = case_response.json()["id"]

        evidence_data = {**sample_evidence_data, "case_id": case_id}
        client.post("/evidence/", json=evidence_data, headers=auth_headers)

        response = client.get("/evidence/", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_evidence_by_case(self, client, auth_headers, sample_case_data, sample_evidence_data):
        """Test filtering evidence by case."""
        case_response = client.post(
            "/cases/",
            json=sample_case_data,
            headers=auth_headers
        )
        case_id = case_response.json()["id"]

        evidence_data = {**sample_evidence_data, "case_id": case_id}
        client.post("/evidence/", json=evidence_data, headers=auth_headers)

        response = client.get(
            "/evidence/",
            params={"case_id": case_id},
            headers=auth_headers
        )
        assert response.status_code == 200
        for evidence in response.json():
            assert evidence["case_id"] == case_id

    def test_verify_evidence(
        self, client, auth_headers, security_lead_auth_headers, sample_case_data, sample_evidence_data
    ):
        """Test verifying evidence."""
        case_response = client.post(
            "/cases/",
            json=sample_case_data,
            headers=auth_headers
        )
        case_id = case_response.json()["id"]

        evidence_data = {**sample_evidence_data, "case_id": case_id}
        evidence_response = client.post(
            "/evidence/",
            json=evidence_data,
            headers=auth_headers
        )
        evidence_id = evidence_response.json()["id"]

        response = client.post(
            f"/evidence/{evidence_id}/verify",
            headers=security_lead_auth_headers
        )
        assert response.status_code == 200
        assert response.json()["verification_status"] == "verified"

    def test_verify_evidence_forbidden(
        self, client, auth_headers, sample_case_data, sample_evidence_data
    ):
        """Test that operators cannot verify evidence."""
        case_response = client.post(
            "/cases/",
            json=sample_case_data,
            headers=auth_headers
        )
        case_id = case_response.json()["id"]

        evidence_data = {**sample_evidence_data, "case_id": case_id}
        evidence_response = client.post(
            "/evidence/",
            json=evidence_data,
            headers=auth_headers
        )
        evidence_id = evidence_response.json()["id"]

        response = client.post(
            f"/evidence/{evidence_id}/verify",
            headers=auth_headers
        )
        assert response.status_code == 403

    def test_verify_integrity(
        self, client, auth_headers, sample_case_data, sample_evidence_data
    ):
        """Test evidence integrity verification."""
        case_response = client.post(
            "/cases/",
            json=sample_case_data,
            headers=auth_headers
        )
        case_id = case_response.json()["id"]

        evidence_data = {**sample_evidence_data, "case_id": case_id}
        evidence_response = client.post(
            "/evidence/",
            json=evidence_data,
            headers=auth_headers
        )
        evidence_id = evidence_response.json()["id"]

        response = client.get(
            f"/evidence/{evidence_id}/verify-integrity",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["integrity_valid"] is True
        assert "stored_hash" in data
        assert "computed_hash" in data


class TestRBAC:
    """Tests for Role-Based Access Control."""

    def test_viewer_cannot_create_movement(self, client, db_session):
        """Test that viewers cannot create movements."""
        from backend.models import User
        from backend.auth import get_password_hash, create_access_token
        from datetime import timedelta

        viewer = User(
            username="testviewer",
            hashed_password=get_password_hash("viewerpass"),
            role="viewer"
        )
        db_session.add(viewer)
        db_session.commit()

        token = create_access_token(
            data={"sub": viewer.username},
            expires_delta=timedelta(minutes=30)
        )
        headers = {"Authorization": f"Bearer {token}"}

        movement_data = {
            "cargo": "Test Cargo",
            "route": "A to B"
        }
        response = client.post("/movements/", json=movement_data, headers=headers)
        assert response.status_code == 403

    def test_admin_can_do_everything(
        self, client, admin_auth_headers, sample_movement_data, sample_alert_data
    ):
        """Test that admin can perform all operations."""
        # Create movement
        movement_response = client.post(
            "/movements/",
            json=sample_movement_data,
            headers=admin_auth_headers
        )
        assert movement_response.status_code == 201

        # Create alert
        alert_response = client.post(
            "/alerts/",
            json=sample_alert_data,
            headers=admin_auth_headers
        )
        assert alert_response.status_code == 201

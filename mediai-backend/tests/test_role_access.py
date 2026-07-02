"""Tests for role-based access control (Module 4) on history/dashboard endpoints."""

from tests.conftest import register_and_login


def test_patient_cannot_view_another_patients_history(client, db_session):
    p1_uuid, p1_headers, _ = register_and_login(client, "rbac_p1@example.com", role="PATIENT")
    _, p2_headers, _ = register_and_login(client, "rbac_p2@example.com", role="PATIENT")

    response = client.get(f"/history/symptoms?patient_uuid={p1_uuid}", headers=p2_headers)
    assert response.status_code == 403


def test_patient_can_view_own_history(client, db_session):
    _, p1_headers, _ = register_and_login(client, "rbac_p3@example.com", role="PATIENT")
    response = client.get("/history/symptoms", headers=p1_headers)
    assert response.status_code == 200


def test_doctor_can_view_any_patients_history(client, db_session):
    p1_uuid, _, _ = register_and_login(client, "rbac_p4@example.com", role="PATIENT")
    _, doctor_headers, _ = register_and_login(client, "rbac_doc1@example.com", role="DOCTOR")

    response = client.get(f"/history/symptoms?patient_uuid={p1_uuid}", headers=doctor_headers)
    assert response.status_code == 200


def test_admin_can_view_any_patients_dashboard(client, db_session):
    p1_uuid, _, _ = register_and_login(client, "rbac_p5@example.com", role="PATIENT")
    _, admin_headers, _ = register_and_login(client, "rbac_admin1@example.com", role="ADMIN")

    response = client.get(f"/dashboard/summary?patient_uuid={p1_uuid}", headers=admin_headers)
    assert response.status_code == 200


def test_doctor_viewing_nonexistent_patient_returns_404(client, db_session):
    _, doctor_headers, _ = register_and_login(client, "rbac_doc2@example.com", role="DOCTOR")
    response = client.get(
        "/history/symptoms?patient_uuid=00000000-0000-0000-0000-000000000000", headers=doctor_headers
    )
    assert response.status_code == 404


def test_unauthenticated_request_to_history_returns_401(client, db_session):
    response = client.get("/history/symptoms")
    assert response.status_code == 401


def test_unauthenticated_request_to_dashboard_returns_401(client, db_session):
    response = client.get("/dashboard/summary")
    assert response.status_code == 401


def test_full_profile_requires_auth_and_returns_own_data_by_default(client, db_session):
    _, headers, _ = register_and_login(client, "rbac_p6@example.com", role="PATIENT")
    response = client.get("/history/full-profile", headers=headers)
    assert response.status_code == 200
    assert response.json()["patient_info"]["email"] == "rbac_p6@example.com"

"""Tests for /auth/* endpoints (Module 4), against the real configured database."""


def test_register_creates_user(client, db_session):
    response = client.post(
        "/auth/register",
        json={"full_name": "Alice Patient", "email": "alice@example.com", "password": "password123", "role": "PATIENT"},
    )
    assert response.status_code == 201
    assert response.json() == {"message": "User created successfully"}


def test_register_duplicate_email_returns_409(client, db_session):
    payload = {"full_name": "Bob", "email": "bob@example.com", "password": "password123", "role": "PATIENT"}
    client.post("/auth/register", json=payload)
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json()["status"] == "error"


def test_register_rejects_weak_password_too_short(client, db_session):
    response = client.post(
        "/auth/register",
        json={"full_name": "Carl", "email": "carl@example.com", "password": "short1", "role": "PATIENT"},
    )
    assert response.status_code == 422


def test_register_rejects_password_without_digit(client, db_session):
    response = client.post(
        "/auth/register",
        json={"full_name": "Dana", "email": "dana@example.com", "password": "alllettersnodigits", "role": "PATIENT"},
    )
    assert response.status_code == 422


def test_register_rejects_invalid_email(client, db_session):
    response = client.post(
        "/auth/register",
        json={"full_name": "Eve", "email": "not-an-email", "password": "password123", "role": "PATIENT"},
    )
    assert response.status_code == 422


def test_register_defaults_to_patient_role(client, db_session):
    client.post(
        "/auth/register",
        json={"full_name": "Frank", "email": "frank@example.com", "password": "password123"},
    )
    tokens = client.post("/auth/login", json={"email": "frank@example.com", "password": "password123"}).json()
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}).json()
    assert me["role"] == "PATIENT"


def test_login_success_returns_token_pair(client, db_session):
    client.post(
        "/auth/register",
        json={"full_name": "Grace", "email": "grace@example.com", "password": "password123", "role": "PATIENT"},
    )
    response = client.post("/auth/login", json={"email": "grace@example.com", "password": "password123"})
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body and len(body["access_token"]) > 0
    assert "refresh_token" in body and len(body["refresh_token"]) > 0
    assert body["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client, db_session):
    client.post(
        "/auth/register",
        json={"full_name": "Hank", "email": "hank@example.com", "password": "password123", "role": "PATIENT"},
    )
    response = client.post("/auth/login", json={"email": "hank@example.com", "password": "wrongpassword"})
    assert response.status_code == 401


def test_login_nonexistent_email_returns_401(client, db_session):
    response = client.post("/auth/login", json={"email": "nobody@example.com", "password": "password123"})
    assert response.status_code == 401


def test_me_requires_authentication(client, db_session):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_rejects_malformed_token(client, db_session):
    response = client.get("/auth/me", headers={"Authorization": "Bearer not.a.valid.jwt"})
    assert response.status_code == 401


def test_me_returns_correct_profile(client, db_session):
    client.post(
        "/auth/register",
        json={"full_name": "Ivy Patient", "email": "ivy@example.com", "password": "password123", "phone": "555-1234", "role": "PATIENT"},
    )
    tokens = client.post("/auth/login", json={"email": "ivy@example.com", "password": "password123"}).json()
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    body = response.json()
    assert body["full_name"] == "Ivy Patient"
    assert body["email"] == "ivy@example.com"
    assert body["phone"] == "555-1234"
    assert body["is_active"] is True


def test_refresh_token_returns_new_token_pair(client, db_session):
    client.post(
        "/auth/register",
        json={"full_name": "Jack", "email": "jack@example.com", "password": "password123", "role": "PATIENT"},
    )
    tokens = client.post("/auth/login", json={"email": "jack@example.com", "password": "password123"}).json()
    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    new_tokens = response.json()
    assert new_tokens["access_token"] != tokens["access_token"]


def test_refresh_rejects_access_token_used_as_refresh_token(client, db_session):
    client.post(
        "/auth/register",
        json={"full_name": "Karl", "email": "karl@example.com", "password": "password123", "role": "PATIENT"},
    )
    tokens = client.post("/auth/login", json={"email": "karl@example.com", "password": "password123"}).json()
    # Deliberately pass the access token where a refresh token is expected.
    response = client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert response.status_code == 401


def test_passwords_are_never_stored_in_plaintext(client, db_session):
    client.post(
        "/auth/register",
        json={"full_name": "Liam", "email": "liam@example.com", "password": "password123", "role": "PATIENT"},
    )
    from app.database.models import User

    user = db_session.query(User).filter(User.email == "liam@example.com").first()
    assert user.password_hash != "password123"
    assert user.password_hash.startswith("$2b$")

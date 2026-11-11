"""Tests for registration, login, and the current-user endpoint."""


async def _register(client, email="alice@example.com", password="correct-horse", name="Alice"):
    return await client.post(
        "/auth/register",
        json={"email": email, "password": password, "display_name": name},
    )


async def test_register_creates_a_user(client):
    response = await _register(client)
    assert response.status_code == 201

    data = response.json()
    assert data["email"] == "alice@example.com"
    assert data["display_name"] == "Alice"
    assert "password" not in data
    assert "hashed_password" not in data


async def test_register_rejects_duplicate_email(client):
    await _register(client)
    response = await _register(client)
    assert response.status_code == 400


async def test_register_rejects_short_password(client):
    response = await client.post(
        "/auth/register",
        json={"email": "bob@example.com", "password": "short", "display_name": "Bob"},
    )
    assert response.status_code == 422


async def test_login_with_correct_credentials_returns_a_token(client):
    await _register(client)
    response = await client.post(
        "/auth/login",
        data={"username": "alice@example.com", "password": "correct-horse"},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]


async def test_login_with_wrong_password_is_rejected(client):
    await _register(client)
    response = await client.post(
        "/auth/login",
        data={"username": "alice@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


async def test_login_with_unknown_email_is_rejected(client):
    response = await client.post(
        "/auth/login",
        data={"username": "nobody@example.com", "password": "whatever123"},
    )
    assert response.status_code == 401


async def test_me_requires_a_token(client):
    response = await client.get("/auth/me")
    assert response.status_code == 401


async def test_me_returns_the_authenticated_user(client):
    await _register(client)
    login_response = await client.post(
        "/auth/login",
        data={"username": "alice@example.com", "password": "correct-horse"},
    )
    token = login_response.json()["access_token"]

    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "alice@example.com"


async def test_me_rejects_a_malformed_token(client):
    response = await client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401

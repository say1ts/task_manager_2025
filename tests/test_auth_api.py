import pytest
from httpx import AsyncClient
from fastapi import status

pytestmark = pytest.mark.asyncio

USER_PAYLOAD = {"email": "testuser@example.com", "password": "strongpassword123"}


async def test_register_user_success(client: AsyncClient):
    """Тест успешной регистрации пользователя."""
    response = await client.post("/auth/register", json=USER_PAYLOAD)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == USER_PAYLOAD["email"]
    assert "user_id" in data
    assert "is_active" in data


async def test_register_user_conflict(client: AsyncClient):
    """Тест регистрации пользователя с уже существующим email."""
    await client.post("/auth/register", json=USER_PAYLOAD)
    response = await client.post("/auth/register", json=USER_PAYLOAD)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in response.json()["detail"]


async def test_login_success(client: AsyncClient):
    """Тест успешного входа в систему."""
    await client.post("/auth/register", json=USER_PAYLOAD)
    login_payload = {
        "username": USER_PAYLOAD["email"],
        "password": USER_PAYLOAD["password"],
    }
    response = await client.post("/auth/login", data=login_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_failure_wrong_password(client: AsyncClient):
    """Тест входа с неверным паролем."""
    await client.post("/auth/register", json=USER_PAYLOAD)
    login_payload = {"username": USER_PAYLOAD["email"], "password": "wrongpassword"}
    response = await client.post("/auth/login", data=login_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid email or password" in response.json()["detail"]


async def test_read_me_success(client: AsyncClient):
    """Тест получения данных о себе для аутентифицированного пользователя."""
    await client.post("/auth/register", json=USER_PAYLOAD)
    login_payload = {
        "username": USER_PAYLOAD["email"],
        "password": USER_PAYLOAD["password"],
    }
    login_response = await client.post("/auth/login", data=login_payload)
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/auth/me", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == USER_PAYLOAD["email"]


async def test_read_me_unauthorized_no_token(client: AsyncClient):
    """Тест доступа к /me без токена."""
    response = await client.get("/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Not authenticated" in response.json()["detail"]

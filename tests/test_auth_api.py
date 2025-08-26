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


@pytest.mark.parametrize(
    "email, password, expected_status, expected_detail",
    [
        (USER_PAYLOAD["email"], USER_PAYLOAD["password"], status.HTTP_200_OK, None),
        (
            USER_PAYLOAD["email"],
            "wrongpassword",
            status.HTTP_401_UNAUTHORIZED,
            "Invalid email or password",
        ),
        (
            "nonexistent@example.com",
            "password123",
            status.HTTP_401_UNAUTHORIZED,
            "Invalid email or password",
        ),
    ],
    ids=["success", "wrong_password", "nonexistent_user"],
)
async def test_login(
    client: AsyncClient, email, password, expected_status, expected_detail
):
    """Тест входа в систему с разными сценариями."""
    await client.post(
        "/auth/register", json=USER_PAYLOAD
    )  # Регистрируем пользователя для успешного сценария
    login_payload = {"username": email, "password": password}
    response = await client.post("/auth/login", data=login_payload)
    assert response.status_code == expected_status
    data = response.json()
    if expected_status == status.HTTP_200_OK:
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    else:
        assert expected_detail in data["detail"]


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


@pytest.mark.parametrize(
    "email, expected_status, expected_detail",
    [
        (USER_PAYLOAD["email"], status.HTTP_409_CONFLICT, "already exists"),
        (USER_PAYLOAD["email"], status.HTTP_409_CONFLICT, "already exists"),
    ],
    ids=["first_attempt", "second_attempt"],
)
async def test_register_user_conflict(
    client: AsyncClient, email, expected_status, expected_detail
):
    """Тест регистрации пользователя с уже существующим email."""
    await client.post("/auth/register", json=USER_PAYLOAD)
    response = await client.post(
        "/auth/register", json={"email": email, "password": "newpassword123"}
    )
    assert response.status_code == expected_status
    assert expected_detail in response.json()["detail"]

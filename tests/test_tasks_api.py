import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi import status
from uuid_extensions import uuid7

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def user_one_payload():
    return {"email": "user.one@example.com", "password": "password123"}


@pytest_asyncio.fixture
async def user_two_payload():
    return {"email": "user.two@example.com", "password": "password456"}


@pytest_asyncio.fixture
async def authenticated_client_one(
    client: AsyncClient, user_one_payload
) -> AsyncClient:
    """Фикстура для создания аутентифицированного клиента для первого пользователя."""
    await client.post("/auth/register", json=user_one_payload)
    login_response = await client.post(
        "/auth/login",
        data={
            "username": user_one_payload["email"],
            "password": user_one_payload["password"],
        },
    )
    token = login_response.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}
    return client


@pytest_asyncio.fixture
async def authenticated_client_two(
    client: AsyncClient, user_two_payload
) -> AsyncClient:
    """Фикстура для создания аутентифицированного клиента для второго пользователя."""
    await client.post("/auth/register", json=user_two_payload)
    login_response = await client.post(
        "/auth/login",
        data={
            "username": user_two_payload["email"],
            "password": user_two_payload["password"],
        },
    )
    token = login_response.json()["access_token"]
    # Создаем новый клиент, чтобы заголовки не пересекались
    new_client = AsyncClient(transport=client._transport, base_url=client.base_url)
    new_client.headers = {"Authorization": f"Bearer {token}"}
    return new_client


async def test_create_task(authenticated_client_one: AsyncClient):
    task_payload = {
        "title": "Test Task",
        "description": "Test Description",
        "status": "created",
    }
    response = await authenticated_client_one.post("/tasks/", json=task_payload)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == task_payload["title"]
    assert "task_id" in data
    assert "user_id" in data  # Проверяем наличие user_id


async def test_get_all_tasks_isolates_users(
    authenticated_client_one: AsyncClient, authenticated_client_two: AsyncClient
):
    """Проверяем, что пользователи видят только свои задачи."""
    # Пользователь 1 создает задачу
    await authenticated_client_one.post(
        "/tasks/", json={"title": "User One's Task", "status": "created"}
    )

    # Пользователь 2 создает задачу
    await authenticated_client_two.post(
        "/tasks/", json={"title": "User Two's Task", "status": "created"}
    )

    # Пользователь 1 запрашивает свои задачи
    response_one = await authenticated_client_one.get("/tasks/")
    assert response_one.status_code == status.HTTP_200_OK
    data_one = response_one.json()
    assert len(data_one) == 1
    assert data_one[0]["title"] == "User One's Task"
    assert "user_id" in data_one[0]  # Проверяем наличие user_id

    # Пользователь 2 запрашивает свои задачи
    response_two = await authenticated_client_two.get("/tasks/")
    assert response_two.status_code == status.HTTP_200_OK
    data_two = response_two.json()
    assert len(data_two) == 1
    assert data_two[0]["title"] == "User Two's Task"
    assert "user_id" in data_two[0]  # Проверяем наличие user_id


async def test_user_cannot_access_another_users_task(
    authenticated_client_one: AsyncClient, authenticated_client_two: AsyncClient
):
    """Проверяем, что пользователь не может получить, обновить или удалить чужую задачу."""
    # Пользователь 1 создает задачу
    create_response = await authenticated_client_one.post(
        "/tasks/", json={"title": "Private Task", "status": "created"}
    )
    task_id = create_response.json()["task_id"]

    # Пользователь 2 пытается получить доступ к задаче пользователя 1
    response = await authenticated_client_two.get(f"/tasks/{task_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Пользователь 2 пытается обновить задачу пользователя 1
    update_payload = {"title": "Hacked", "status": "completed"}
    response = await authenticated_client_two.put(
        f"/tasks/{task_id}", json=update_payload
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Пользователь 2 пытается удалить задачу пользователя 1
    response = await authenticated_client_two.delete(f"/tasks/{task_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_access_tasks_unauthorized(client: AsyncClient):
    """Тест доступа к эндпоинтам задач без токена аутентификации."""
    response = await client.get("/tasks/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = await client.post("/tasks/", json={"title": "task", "status": "created"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_create_task_with_invalid_data(authenticated_client_one: AsyncClient):
    """Тест создания задачи с невалидными данными (пустой заголовок)."""
    response = await authenticated_client_one.post(
        "/tasks/", json={"title": "", "status": "created"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_get_task_not_found(authenticated_client_one: AsyncClient):
    """Тест запроса несуществующей задачи."""
    non_existent_id = uuid7()
    response = await authenticated_client_one.get(f"/tasks/{non_existent_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

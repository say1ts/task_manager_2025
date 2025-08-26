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
    new_client = AsyncClient(transport=client._transport, base_url=client.base_url)
    new_client.headers = {"Authorization": f"Bearer {token}"}
    return new_client


@pytest.mark.parametrize(
    "task_payload, expected_status, expected_title",
    [
        (
            {
                "title": "Test Task",
                "description": "Test Description",
                "status": "created",
            },
            status.HTTP_201_CREATED,
            "Test Task",
        ),
        (
            {"title": "Another Task", "description": None, "status": "in_progress"},
            status.HTTP_201_CREATED,
            "Another Task",
        ),
        (
            {"title": "", "description": "Invalid", "status": "created"},
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            None,
        ),
    ],
    ids=["valid_task", "valid_task_no_description", "invalid_empty_title"],
)
async def test_create_task(
    authenticated_client_one: AsyncClient, task_payload, expected_status, expected_title
):
    """Тест создания задачи с разными входными данными."""
    response = await authenticated_client_one.post("/tasks/", json=task_payload)
    assert response.status_code == expected_status
    if expected_status == status.HTTP_201_CREATED:
        data = response.json()
        assert data["title"] == expected_title
        assert "task_id" in data
        assert "user_id" in data


async def test_get_all_tasks_isolates_users(
    authenticated_client_one: AsyncClient, authenticated_client_two: AsyncClient
):
    """Проверяем, что пользователи видят только свои задачи."""
    await authenticated_client_one.post(
        "/tasks/", json={"title": "User One's Task", "status": "created"}
    )
    await authenticated_client_two.post(
        "/tasks/", json={"title": "User Two's Task", "status": "created"}
    )

    response_one = await authenticated_client_one.get("/tasks/")
    assert response_one.status_code == status.HTTP_200_OK
    data_one = response_one.json()
    assert len(data_one) == 1
    assert data_one[0]["title"] == "User One's Task"
    assert "user_id" in data_one[0]

    response_two = await authenticated_client_two.get("/tasks/")
    assert response_two.status_code == status.HTTP_200_OK
    data_two = response_two.json()
    assert len(data_two) == 1
    assert data_two[0]["title"] == "User Two's Task"
    assert "user_id" in data_two[0]


@pytest.mark.parametrize(
    "method, endpoint, payload",
    [
        ("get", "/tasks/{}", None),
        ("put", "/tasks/{}", {"title": "Hacked", "status": "completed"}),
        ("delete", "/tasks/{}", None),
    ],
    ids=["get_task", "update_task", "delete_task"],
)
async def test_user_cannot_access_another_users_task(
    authenticated_client_one: AsyncClient,
    authenticated_client_two: AsyncClient,
    method,
    endpoint,
    payload,
):
    """Проверяем, что пользователь не может получить, обновить или удалить чужую задачу."""
    create_response = await authenticated_client_one.post(
        "/tasks/", json={"title": "Private Task", "status": "created"}
    )
    task_id = create_response.json()["task_id"]

    client_method = getattr(authenticated_client_two, method)
    if method in ("post", "put"):
        response = await client_method(endpoint.format(task_id), json=payload)
    else:
        response = await client_method(endpoint.format(task_id))
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    "method, endpoint, payload",
    [
        ("get", "/tasks/", None),
        ("post", "/tasks/", {"title": "task", "status": "created"}),
    ],
    ids=["get_tasks", "create_task"],
)
async def test_access_tasks_unauthorized(
    client: AsyncClient, method, endpoint, payload
):
    """Тест доступа к эндпоинтам задач без токена аутентификации."""
    client_method = getattr(client, method)
    if method in ("post", "put"):
        response = await client_method(endpoint, json=payload)
    else:
        response = await client_method(endpoint)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_get_task_not_found(authenticated_client_one: AsyncClient):
    """Тест запроса несуществующей задачи."""
    non_existent_id = uuid7()
    response = await authenticated_client_one.get(f"/tasks/{non_existent_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

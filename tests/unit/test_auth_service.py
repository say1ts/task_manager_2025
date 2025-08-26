import pytest
from unittest.mock import AsyncMock
from uuid_extensions import uuid7
from app.auth import AuthService, UserAlreadyExistsError, InvalidCredentialsError
from app.auth.schemas import UserCreate, UserLogin, User
from passlib.context import CryptContext

pytestmark = pytest.mark.asyncio

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.fixture
def mock_user_repository():
    """Фикстура, создающая мок-объект для UserRepository."""
    return AsyncMock()


@pytest.fixture
def auth_service(mock_user_repository):
    """Фикстура, создающая экземпляр AuthService с мок-репозиторием."""
    return AuthService(mock_user_repository)


async def test_register_user_success(auth_service: AuthService, mock_user_repository):
    """Тест успешной регистрации нового пользователя."""
    user_data = UserCreate(email="newuser@example.com", password="password123")

    mock_user_repository.get_by_email.return_value = None
    created_user = User(
        user_id=uuid7(),
        email=user_data.email,
        is_active=True,
        hashed_password=pwd_context.hash(user_data.password),
    )
    mock_user_repository.create.return_value = created_user

    result = await auth_service.register_user(user_data)

    mock_user_repository.get_by_email.assert_called_once_with(user_data.email)
    mock_user_repository.create.assert_called_once_with(user_data)
    assert isinstance(result, User)
    assert result.email == user_data.email
    assert result.user_id == created_user.user_id
    assert result.is_active == created_user.is_active


async def test_register_user_already_exists(
    auth_service: AuthService, mock_user_repository
):
    """Тест попытки регистрации пользователя, который уже существует."""
    user_data = UserCreate(email="existing@example.com", password="password123")
    existing_user = User(
        user_id=uuid7(),
        email=user_data.email,
        is_active=True,
        hashed_password=pwd_context.hash(user_data.password),
    )
    mock_user_repository.get_by_email.return_value = existing_user

    with pytest.raises(UserAlreadyExistsError):
        await auth_service.register_user(user_data)

    mock_user_repository.create.assert_not_called()


@pytest.mark.parametrize(
    "email, password, mock_user, expected_exception",
    [
        (
            "test@example.com",
            "password123",
            User(
                user_id=uuid7(),
                email="test@example.com",
                is_active=True,
                hashed_password=pwd_context.hash("password123"),
            ),
            None,
        ),
        ("nouser@example.com", "password123", None, InvalidCredentialsError),
        (
            "test@example.com",
            "wrongpassword",
            User(
                user_id=uuid7(),
                email="test@example.com",
                is_active=True,
                hashed_password=pwd_context.hash("correctpassword"),
            ),
            InvalidCredentialsError,
        ),
    ],
    ids=["success", "not_found", "wrong_password"],
)
async def test_authenticate_user(
    auth_service: AuthService,
    mock_user_repository,
    email,
    password,
    mock_user,
    expected_exception,
):
    """Тест аутентификации с разными сценариями."""
    login_data = UserLogin(email=email, password=password)
    mock_user_repository.get_by_email.return_value = mock_user

    if expected_exception:
        with pytest.raises(expected_exception):
            await auth_service.authenticate_user(login_data)
    else:
        result = await auth_service.authenticate_user(login_data)
        assert isinstance(result, User)
        assert result.email == login_data.email
        assert result.is_active

    mock_user_repository.get_by_email.assert_called_once_with(login_data.email)

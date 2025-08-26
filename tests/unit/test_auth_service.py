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

    # Настраиваем мок: get_by_email должен вернуть None (пользователя нет)
    mock_user_repository.get_by_email.return_value = None

    # Настраиваем мок: create должен вернуть созданного пользователя
    created_user = User(
        user_id=uuid7(),
        email=user_data.email,
        is_active=True,
        hashed_password=pwd_context.hash(user_data.password),
    )
    mock_user_repository.create.return_value = created_user

    # Вызываем тестируемый метод
    result = await auth_service.register_user(user_data)

    # Проверяем, что методы мока были вызваны с правильными аргументами
    mock_user_repository.get_by_email.assert_called_once_with(user_data.email)
    mock_user_repository.create.assert_called_once_with(user_data)

    # Проверяем результат
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


async def test_authenticate_user_success(
    auth_service: AuthService, mock_user_repository
):
    """Тест успешной аутентификации."""
    login_data = UserLogin(email="test@example.com", password="password123")

    # мок пользователя
    user = User(
        user_id=uuid7(),
        email=login_data.email,
        is_active=True,
        hashed_password=pwd_context.hash(login_data.password),
    )

    # мок для возврата пользователя
    mock_user_repository.get_by_email.return_value = user

    result = await auth_service.authenticate_user(login_data)

    mock_user_repository.get_by_email.assert_called_once_with(login_data.email)
    assert isinstance(result, User)
    assert result.email == login_data.email
    assert result.user_id == user.user_id
    assert result.is_active == user.is_active


async def test_authenticate_user_not_found(
    auth_service: AuthService, mock_user_repository
):
    """Тест аутентификации с несуществующим email."""
    login_data = UserLogin(email="nouser@example.com", password="password123")
    mock_user_repository.get_by_email.return_value = None

    with pytest.raises(InvalidCredentialsError):
        await auth_service.authenticate_user(login_data)

    mock_user_repository.get_by_email.assert_called_once_with(login_data.email)


async def test_authenticate_user_wrong_password(
    auth_service: AuthService, mock_user_repository
):
    """Тест аутентификации с неверным паролем."""
    login_data = UserLogin(email="test@example.com", password="wrongpassword")

    # мок пользователя
    user = User(
        user_id=uuid7(),
        email=login_data.email,
        is_active=True,
        hashed_password=pwd_context.hash("correctpassword"),
    )
    mock_user_repository.get_by_email.return_value = user

    with pytest.raises(InvalidCredentialsError):
        await auth_service.authenticate_user(login_data)

    mock_user_repository.get_by_email.assert_called_once_with(login_data.email)

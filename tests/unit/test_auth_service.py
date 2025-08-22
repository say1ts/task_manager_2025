import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid_extensions import uuid7

from app.auth.service import (
    AuthService,
    UserAlreadyExistsError,
    InvalidCredentialsError,
)
from app.auth.schemas import UserCreate, UserLogin, UserResponse
from app.auth.models import User

pytestmark = pytest.mark.asyncio


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
    created_user_mock = User(id=uuid7(), email=user_data.email, is_active=True)
    mock_user_repository.create.return_value = created_user_mock

    # Вызываем тестируемый метод
    result = await auth_service.register_user(user_data)

    # Проверяем, что методы мока были вызваны с правильными аргументами
    mock_user_repository.get_by_email.assert_called_once_with(user_data.email)
    mock_user_repository.create.assert_called_once_with(user_data)

    # Проверяем результат
    assert isinstance(result, UserResponse)
    assert result.email == user_data.email


async def test_register_user_already_exists(
    auth_service: AuthService, mock_user_repository
):
    """Тест попытки регистрации пользователя, который уже существует."""
    user_data = UserCreate(email="existing@example.com", password="password123")

    # Настраиваем мок: get_by_email возвращает существующего пользователя
    mock_user_repository.get_by_email.return_value = User(
        id=uuid7(), email=user_data.email
    )

    # Проверяем, что сервис выбрасывает ожидаемое исключение
    with pytest.raises(UserAlreadyExistsError):
        await auth_service.register_user(user_data)

    # Убеждаемся, что метод create не был вызван
    mock_user_repository.create.assert_not_called()


async def test_authenticate_user_success(
    auth_service: AuthService, mock_user_repository
):
    """Тест успешной аутентификации."""
    login_data = UserLogin(email="test@example.com", password="password123")

    # Создаем мок пользователя с методом verify_password и атрибутами для валидации
    user_mock = MagicMock(spec=User)
    user_mock.id = uuid7()  # Реальный UUID для поля id
    user_mock.email = login_data.email  # Реальная строка для email
    user_mock.is_active = True  # Булево для is_active
    user_mock.verify_password.return_value = True  # Пароль верный

    mock_user_repository.get_by_email.return_value = user_mock

    result = await auth_service.authenticate_user(login_data)

    mock_user_repository.get_by_email.assert_called_once_with(login_data.email)
    user_mock.verify_password.assert_called_once_with(login_data.password)
    assert isinstance(result, UserResponse)
    assert result.email == login_data.email
    assert result.id == user_mock.id
    assert result.is_active == user_mock.is_active


async def test_authenticate_user_not_found(
    auth_service: AuthService, mock_user_repository
):
    """Тест аутентификации с несуществующим email."""
    login_data = UserLogin(email="nouser@example.com", password="password123")
    mock_user_repository.get_by_email.return_value = None

    with pytest.raises(InvalidCredentialsError):
        await auth_service.authenticate_user(login_data)


async def test_authenticate_user_wrong_password(
    auth_service: AuthService, mock_user_repository
):
    """Тест аутентификации с неверным паролем."""
    login_data = UserLogin(email="test@example.com", password="wrongpassword")

    user_mock = MagicMock(spec=User)
    user_mock.verify_password.return_value = False  # Пароль неверный

    mock_user_repository.get_by_email.return_value = user_mock

    with pytest.raises(InvalidCredentialsError):
        await auth_service.authenticate_user(login_data)

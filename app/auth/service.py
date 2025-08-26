import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext
from app.config import settings
from .exceptions import UserAlreadyExistsError, InvalidCredentialsError
from .repository import AbstractUserRepository
from .schemas import UserCreate, UserLogin, User, TokenData

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AbstractAuthService:
    """Абстрактный базовый класс для сервиса аутентификации."""

    def __init__(self, repository: AbstractUserRepository):
        self.repository = repository

    async def register_user(self, user_data: UserCreate) -> User:
        """Регистрирует нового пользователя."""
        pass

    async def authenticate_user(self, login_data: UserLogin) -> User:
        """Аутентифицирует пользователя."""
        pass

    def create_access_token(self, data: dict) -> str:
        """Создает JWT access token."""
        pass

    async def get_current_user(self, token: str) -> User:
        """Получает текущего пользователя из токена."""
        pass


class AuthService(AbstractAuthService):
    """Сервис для аутентификации и авторизации."""

    async def register_user(self, user_data: UserCreate) -> User:
        existing_user = await self.repository.get_by_email(user_data.email)
        if existing_user:
            raise UserAlreadyExistsError(user_data.email)
        return await self.repository.create(user_data)

    async def authenticate_user(self, login_data: UserLogin) -> User:
        user = await self.repository.get_by_email(login_data.email)
        if not user or not pwd_context.verify(
            login_data.password, user.hashed_password
        ):
            raise InvalidCredentialsError()
        return user

    def create_access_token(self, data: dict) -> str:
        encoded_jwt = jwt.encode(
            data, settings.AUTH_SECRET_KEY, algorithm=settings.AUTH_ALGORITHM
        )
        return encoded_jwt

    async def get_current_user(self, token: str) -> User:
        try:
            payload = jwt.decode(
                token, settings.AUTH_SECRET_KEY, algorithms=[settings.AUTH_ALGORITHM]
            )
            email: str = payload.get("sub")
            if email is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
                )
            token_data = TokenData(email=email)
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        user = await self.repository.get_by_email(token_data.email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )
        return user

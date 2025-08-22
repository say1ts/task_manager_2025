from datetime import datetime, timedelta, timezone
import jwt
from fastapi import HTTPException, status
from app.config import settings
from .repository import UserRepository
from .schemas import UserCreate, UserLogin, UserResponse, TokenData


class AuthError(Exception):
    pass


class UserAlreadyExistsError(AuthError):
    def __init__(self, email: str):
        super().__init__(f"User with email {email} already exists.")


class InvalidCredentialsError(AuthError):
    def __init__(self):
        super().__init__("Invalid email or password.")


class AuthService:
    """Сервис для аутентификации и авторизации."""

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def register_user(self, user_data: UserCreate) -> UserResponse:
        """Регистрирует нового пользователя."""
        existing_user = await self.repository.get_by_email(user_data.email)
        if existing_user:
            raise UserAlreadyExistsError(user_data.email)
        new_user = await self.repository.create(user_data)
        return UserResponse.model_validate(new_user)

    async def authenticate_user(self, login_data: UserLogin) -> UserResponse:
        """Аутентифицирует пользователя."""
        user = await self.repository.get_by_email(login_data.email)
        if not user or not user.verify_password(login_data.password):
            raise InvalidCredentialsError()
        return UserResponse.model_validate(user)

    def create_access_token(self, data: dict) -> str:
        """Создает JWT access token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode.update({"exp": expire})
        return jwt.encode(
            to_encode, settings.AUTH_SECRET_KEY, algorithm=settings.AUTH_ALGORITHM
        )

    async def get_current_user(self, token: str) -> UserResponse:
        """Получает текущего пользователя из токена."""
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
        return UserResponse.model_validate(user)

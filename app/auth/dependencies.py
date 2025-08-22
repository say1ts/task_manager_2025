from typing import Annotated
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db_session
from .repository import UserRepository
from .service import AuthService
from .schemas import UserResponse

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserRepository:
    """Предоставляет репозиторий пользователей."""
    return UserRepository(session)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_auth_service(repo: UserRepositoryDep) -> AuthService:
    """Предоставляет сервис аутентификации."""
    return AuthService(repo)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], service: AuthServiceDep
) -> UserResponse:
    """Зависимость для получения текущего пользователя."""
    return await service.get_current_user(token)


CurrentUser = Annotated[UserResponse, Depends(get_current_user)]

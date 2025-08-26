from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import UserORM
from .schemas import User, UserCreate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AbstractUserRepository(ABC):
    """Репозиторий для работы с пользователями."""

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Получает пользователя по email."""
        pass

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Получает пользователя по ID."""
        pass

    @abstractmethod
    async def create(self, user_data: UserCreate) -> User:
        """Создает нового пользователя."""
        pass


class UserRepository(AbstractUserRepository):
    """Репозиторий для работы с пользователями, возвращающий DTO."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(UserORM).where(UserORM.email == email)
        )
        user_orm = result.scalar_one_or_none()
        return User.model_validate(user_orm) if user_orm else None

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        user_orm = await self.session.get(UserORM, user_id)
        return User.model_validate(user_orm) if user_orm else None

    async def create(self, user_data: UserCreate) -> User:
        new_user = UserORM(email=user_data.email)
        new_user.set_password(user_data.password)  # Хэшируем пароль
        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)
        return User.model_validate(new_user)

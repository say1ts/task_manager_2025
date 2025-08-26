from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User
from .schemas import UserCreate


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
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        return await self.session.get(User, user_id)

    async def create(self, user_data: UserCreate) -> User:
        new_user = User(email=user_data.email)
        new_user.set_password(user_data.password)
        self.session.add(new_user)
        await self.session.flush()
        await self.session.refresh(new_user)
        return new_user

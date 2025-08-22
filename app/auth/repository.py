from uuid import UUID
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User
from .schemas import UserCreate


class UserRepository:
    """Репозиторий для работы с пользователями."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> Optional[User]:
        """Получает пользователя по email."""
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Получает пользователя по ID."""
        return await self.session.get(User, user_id)

    async def create(self, user_data: UserCreate) -> User:
        """Создает нового пользователя."""
        new_user = User(email=user_data.email)
        new_user.set_password(user_data.password)
        self.session.add(new_user)
        await self.session.flush()
        await self.session.refresh(new_user)
        return new_user

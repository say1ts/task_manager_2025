from abc import ABC, abstractmethod
from uuid import UUID
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import TaskORM
from .schemas import Task, TaskCreate, TaskUpdate
from .exceptions import TaskNotFoundError


class AbstractTaskRepository(ABC):
    """Репозиторий для работы с задачами."""

    @abstractmethod
    async def get_all(self, user_id: UUID) -> List[Task]:
        """Получить все задачи пользователя."""
        pass

    @abstractmethod
    async def get_by_id(self, task_id: UUID, user_id: UUID) -> Optional[Task]:
        """Получить задачу по ID."""
        pass

    @abstractmethod
    async def create(self, task_data: TaskCreate, user_id: UUID) -> Task:
        """Создать новую задачу."""
        pass

    @abstractmethod
    async def update(self, task_id: UUID, user_id: UUID, update_data: TaskUpdate) -> Task:
        """Обновить задачу."""
        pass

    @abstractmethod
    async def delete(self, task_id: UUID, user_id: UUID) -> None:
        """Удалить задачу."""
        pass


class TaskSQLAlchemyRepository(AbstractTaskRepository):
    """Репозиторий для работы с задачами, использующий SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, user_id: UUID) -> List[Task]:
        result = await self.session.execute(
            select(TaskORM).where(TaskORM.user_id == user_id)
        )
        tasks = result.scalars().all()
        return [Task.model_validate(task) for task in tasks]

    async def get_by_id(self, task_id: UUID, user_id: UUID) -> Optional[Task]:
        result = await self.session.execute(
            select(TaskORM).where(
                TaskORM.task_id == task_id,
                TaskORM.user_id == user_id,
            )
        )
        task_orm = result.scalar_one_or_none()
        if task_orm is None:
            raise TaskNotFoundError(task_id)
        return Task.model_validate(task_orm) if task_orm else None

    async def create(self, task_data: TaskCreate, user_id: UUID) -> Task:
        task_orm = TaskORM(**task_data.model_dump(), user_id=user_id)
        self.session.add(task_orm)
        await self.session.commit()
        await self.session.refresh(task_orm)
        return Task.model_validate(task_orm)

    async def update(self, task_id: UUID, user_id: UUID, update_data: TaskUpdate) -> Task:
        task_orm = await self.get_by_id(task_id=task_id, user_id=user_id)
        if not task_orm:
            raise TaskNotFoundError(task_id)

        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(task_orm, key, value)

        await self.session.commit()
        await self.session.refresh(task_orm)
        return Task.model_validate(task_orm)

    async def delete(self, task_id: UUID, user_id: UUID) -> None:
        task_orm = await self.session.get(TaskORM, task_id)
        if not task_orm or task_orm.user_id != user_id:
            raise TaskNotFoundError(task_id)
        await self.session.delete(task_orm)
        await self.session.commit()
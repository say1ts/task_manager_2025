from uuid import UUID
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Task
from .schemas import TaskCreate, TaskUpdate


class TaskSQLAlchemyRepository:
    """
    Слой доступа к данным для задач.
    Работает с сессией SQLAlchemy.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, task_id: UUID, user_id: UUID) -> Optional[Task]:
        stmt = select(Task).where(Task.task_id == task_id, Task.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, user_id: UUID) -> Sequence[Task]:
        result = await self.session.execute(
            select(Task).where(Task.user_id == user_id).order_by(Task.title)
        )
        return result.scalars().all()

    async def create(self, task_data: TaskCreate, user_id: UUID) -> Task:
        new_task = Task(**task_data.model_dump(), user_id=user_id)
        self.session.add(new_task)
        await self.session.flush()
        await self.session.refresh(new_task)
        return new_task

    async def update(self, task: Task, update_data: TaskUpdate) -> Task:
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(task, key, value)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def delete(self, task: Task) -> None:
        await self.session.delete(task)
        await self.session.flush()

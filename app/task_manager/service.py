from abc import ABC, abstractmethod
from uuid import UUID
from typing import List
from .repository import AbstractTaskRepository
from .schemas import TaskCreate, TaskUpdate, Task


class AbstractTaskService(ABC):
    """Абстрактный базовый класс для сервиса задач."""

    def __init__(self, repository: AbstractTaskRepository):
        self.repository = repository

    @abstractmethod
    async def get_all_tasks(self, user_id: UUID) -> List[Task]:
        """Получить все задачи пользователя."""
        pass

    @abstractmethod
    async def get_task_by_id(self, task_id: UUID, user_id: UUID) -> Task:
        """Получить задачу по ID."""
        pass

    @abstractmethod
    async def create_task(self, task_data: TaskCreate, user_id: UUID) -> Task:
        """Создать новую задачу."""
        pass

    @abstractmethod
    async def update_task(
        self, task_id: UUID, update_data: TaskUpdate, user_id: UUID
    ) -> Task:
        """Обновить задачу."""
        pass

    @abstractmethod
    async def delete_task(self, task_id: UUID, user_id: UUID) -> None:
        """Удалить задачу."""
        pass


class TaskService(AbstractTaskService):
    async def get_all_tasks(self, user_id: UUID) -> List[Task]:
        return await self.repository.get_all(user_id=user_id)

    async def get_task_by_id(self, task_id: UUID, user_id: UUID) -> Task:
        return await self.repository.get_by_id(task_id=task_id, user_id=user_id)

    async def create_task(self, task_data: TaskCreate, user_id: UUID) -> Task:
        return await self.repository.create(task_data, user_id=user_id)

    async def update_task(
        self, task_id: UUID, update_data: TaskUpdate, user_id: UUID
    ) -> Task:
        return await self.repository.update(task_id, user_id, update_data)

    async def delete_task(self, task_id: UUID, user_id: UUID) -> None:
        await self.repository.delete(task_id=task_id, user_id=user_id)

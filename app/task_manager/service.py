from uuid import UUID
from typing import List
from .repository import TaskSQLAlchemyRepository
from .schemas import TaskCreate, TaskUpdate, TaskResponse


class TaskServiceError(Exception):
    pass


class TaskNotFoundError(TaskServiceError):
    def __init__(self, task_id: UUID):
        self.task_id = task_id
        super().__init__(f"Task with id {task_id} not found.")


class TaskService:
    def __init__(self, repository: TaskSQLAlchemyRepository):
        self.repository = repository

    async def get_all_tasks(self, user_id: UUID) -> List[TaskResponse]:
        tasks_orm = await self.repository.get_all(user_id=user_id)
        return [TaskResponse.model_validate(task) for task in tasks_orm]

    async def get_task_by_id(self, task_id: UUID, user_id: UUID) -> TaskResponse:
        task_orm = await self.repository.get_by_id(task_id=task_id, user_id=user_id)
        if not task_orm:
            raise TaskNotFoundError(task_id)
        return TaskResponse.model_validate(task_orm)

    async def create_task(self, task_data: TaskCreate, user_id: UUID) -> TaskResponse:
        task_orm = await self.repository.create(task_data, user_id=user_id)
        return TaskResponse.model_validate(task_orm)

    async def update_task(
        self, task_id: UUID, update_data: TaskUpdate, user_id: UUID
    ) -> TaskResponse:
        task_orm = await self.repository.get_by_id(task_id=task_id, user_id=user_id)
        if not task_orm:
            raise TaskNotFoundError(task_id)

        updated_task = await self.repository.update(task_orm, update_data)
        return TaskResponse.model_validate(updated_task)

    async def delete_task(self, task_id: UUID, user_id: UUID) -> None:
        task_orm = await self.repository.get_by_id(task_id=task_id, user_id=user_id)
        if not task_orm:
            raise TaskNotFoundError(task_id)
        await self.repository.delete(task_orm)

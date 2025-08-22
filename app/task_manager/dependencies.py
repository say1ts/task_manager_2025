from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db_session
from .repository import TaskSQLAlchemyRepository
from .service import TaskService


def get_task_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TaskSQLAlchemyRepository:
    """Зависимость, которая создает и предоставляет TaskSQLAlchemyRepository."""
    return TaskSQLAlchemyRepository(session)


DBSession = Annotated[AsyncSession, Depends(get_db_session)]
TaskRepositoryDep = Annotated[TaskSQLAlchemyRepository, Depends(get_task_repository)]


def get_task_service(repo: TaskRepositoryDep) -> TaskService:
    """Зависимость, которая создает и предоставляет TaskService."""
    return TaskService(repo)


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]

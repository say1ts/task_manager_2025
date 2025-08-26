from enum import Enum
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class TaskStatus(str, Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    status: TaskStatus


class TaskCreate(TaskBase):
    status: TaskStatus = TaskStatus.CREATED


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None


class Task(TaskBase):
    task_id: UUID
    user_id: UUID
    model_config = ConfigDict(from_attributes=True)

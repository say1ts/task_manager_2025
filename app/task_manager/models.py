import uuid
from sqlalchemy import UUID, Column, Enum, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.task_manager.schemas import TaskStatus


class TaskORM(Base):
    __tablename__ = "task"

    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.CREATED)

    user_id = Column(UUID(as_uuid=True), ForeignKey("user.user_id"), nullable=False)
    owner = relationship("UserORM", back_populates="tasks")

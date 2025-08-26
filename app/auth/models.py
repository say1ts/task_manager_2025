import uuid
from sqlalchemy import UUID, Column, String, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserORM(Base):
    __tablename__ = "user"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)

    tasks = relationship(
        "TaskORM", back_populates="owner", cascade="all, delete-orphan"
    )

    def set_password(self, plain_password: str) -> None:
        """Хэширует и устанавливает пароль."""
        self.hashed_password = pwd_context.hash(plain_password)

    def verify_password(self, plain_password: str) -> bool:
        """Проверяет пароль на соответствие хэшу."""
        return pwd_context.verify(plain_password, self.hashed_password)

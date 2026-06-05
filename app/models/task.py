import enum
from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Enum, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class TaskStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[Optional[str]] = mapped_column(String(500))
    due_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status_enum"), default=TaskStatus.OPEN
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority, name="task_priority_enum"), default=TaskPriority.MEDIUM
    )
    assignee_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    related_company_id: Mapped[Optional[int]] = mapped_column(ForeignKey("companies.id"))
    related_deal_id: Mapped[Optional[int]] = mapped_column(ForeignKey("deals.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    assignee: Mapped["User"] = relationship(back_populates="tasks")
    related_company: Mapped[Optional["Company"]] = relationship(back_populates="tasks")
    related_deal: Mapped[Optional["Deal"]] = relationship(back_populates="tasks")

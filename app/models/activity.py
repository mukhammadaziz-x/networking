from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100))  # e.g., "create", "update", "delete", "login"
    entity_type: Mapped[str] = mapped_column(String(50))  # e.g., "Company", "Deal", "Contact"
    entity_id: Mapped[Optional[int]] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="activities")

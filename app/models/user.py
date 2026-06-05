import enum
from datetime import datetime
from typing import List
from sqlalchemy import String, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    SALES = "sales"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role_enum"))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    companies: Mapped[List["Company"]] = relationship(back_populates="owner")
    contacts: Mapped[List["Contact"]] = relationship(back_populates="owner")
    deals: Mapped[List["Deal"]] = relationship(back_populates="owner")
    orders: Mapped[List["Order"]] = relationship(back_populates="creator")
    tasks: Mapped[List["Task"]] = relationship(back_populates="assignee")
    activities: Mapped[List["Activity"]] = relationship(back_populates="user")

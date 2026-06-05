import enum
from datetime import datetime
from decimal import Decimal
from typing import List
from sqlalchemy import String, Enum, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class OrderStatus(str, enum.Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    order_number: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status_enum"), default=OrderStatus.DRAFT
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="orders")
    creator: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")

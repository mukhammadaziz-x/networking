from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import String, Numeric, DateTime, Integer, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    category: Mapped[Optional[str]] = mapped_column(String(100))
    size: Mapped[Optional[str]] = mapped_column(String(20))
    color: Mapped[Optional[str]] = mapped_column(String(50))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    stock_qty: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    order_items: Mapped[List["OrderItem"]] = relationship(back_populates="product")

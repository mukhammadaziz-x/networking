from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    position: Mapped[Optional[str]] = mapped_column(String(100))
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="contacts")
    owner: Mapped["User"] = relationship(back_populates="contacts")
    deals: Mapped[List["Deal"]] = relationship(back_populates="contact")

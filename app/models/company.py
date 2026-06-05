import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Enum, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class CompanyStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROSPECT = "prospect"


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    website: Mapped[Optional[str]] = mapped_column(String(255))
    address: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[CompanyStatus] = mapped_column(
        Enum(CompanyStatus, name="company_status_enum"), default=CompanyStatus.PROSPECT
    )
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="companies")
    contacts: Mapped[List["Contact"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    deals: Mapped[List["Deal"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    orders: Mapped[List["Order"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    tasks: Mapped[List["Task"]] = relationship(back_populates="related_company", cascade="all, delete-orphan")

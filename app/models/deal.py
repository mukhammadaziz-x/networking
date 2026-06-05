import enum
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import String, Enum, Numeric, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class DealStage(str, enum.Enum):
    LEAD = "lead"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    WON = "won"
    LOST = "lost"


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    contact_id: Mapped[Optional[int]] = mapped_column(ForeignKey("contacts.id"))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    stage: Mapped[DealStage] = mapped_column(
        Enum(DealStage, name="deal_stage_enum"), default=DealStage.LEAD
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    expected_close_date: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="deals")
    contact: Mapped[Optional["Contact"]] = relationship(back_populates="deals")
    owner: Mapped["User"] = relationship(back_populates="deals")
    tasks: Mapped[List["Task"]] = relationship(back_populates="related_deal", cascade="all, delete-orphan")

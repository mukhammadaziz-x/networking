from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.deal import DealStage


class DealBase(BaseModel):
    title: str
    company_id: int
    contact_id: Optional[int] = None
    stage: DealStage = DealStage.LEAD
    amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    expected_close_date: Optional[date] = None


class DealCreate(DealBase):
    pass


class DealUpdate(BaseModel):
    title: Optional[str] = None
    company_id: Optional[int] = None
    contact_id: Optional[int] = None
    stage: Optional[DealStage] = None
    amount: Optional[Decimal] = None
    expected_close_date: Optional[date] = None


class DealRead(DealBase):
    id: int
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

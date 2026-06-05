from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.order import OrderStatus


class OrderItemBase(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)
    unit_price: Decimal = Field(ge=Decimal("0.00"))


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemRead(OrderItemBase):
    id: int
    order_id: int
    line_total: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    company_id: int
    status: OrderStatus = OrderStatus.DRAFT


class OrderCreate(OrderBase):
    items: List[OrderItemCreate]


class OrderRead(BaseModel):
    id: int
    company_id: int
    order_number: str
    status: OrderStatus
    total_amount: Decimal
    order_date: datetime
    created_by: int
    items: List[OrderItemRead]

    model_config = ConfigDict(from_attributes=True)

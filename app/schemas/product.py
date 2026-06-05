from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    sku: str
    name: str
    category: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    price: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    stock_qty: int = Field(default=0, ge=0)
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    price: Optional[Decimal] = None
    stock_qty: Optional[int] = None
    is_active: Optional[bool] = None


class ProductRead(ProductBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

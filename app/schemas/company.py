from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.company import CompanyStatus


class CompanyBase(BaseModel):
    name: str
    industry: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    status: CompanyStatus = CompanyStatus.PROSPECT


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    status: Optional[CompanyStatus] = None


class CompanyRead(CompanyBase):
    id: int
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    position: Optional[str] = None
    company_id: int


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    company_id: Optional[int] = None


class ContactRead(ContactBase):
    id: int
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

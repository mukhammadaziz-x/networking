from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.task import TaskStatus, TaskPriority


class TaskBase(BaseModel):
    title: str = Field(..., max_length=150)
    description: Optional[str] = Field(None, max_length=500)
    due_date: Optional[date] = None
    status: TaskStatus = TaskStatus.OPEN
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: int
    related_company_id: Optional[int] = None
    related_deal_id: Optional[int] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = Field(None, max_length=500)
    due_date: Optional[date] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[int] = None
    related_company_id: Optional[int] = None
    related_deal_id: Optional[int] = None


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskRead(TaskBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

from datetime import date
from typing import List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.task import Task, TaskStatus, TaskPriority
from app.schemas.task import TaskCreate, TaskUpdate


def get_tasks(
    db: Session,
    assignee_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    overdue_filter: Optional[bool] = None,
    company_id: Optional[int] = None,
    deal_id: Optional[int] = None
) -> List[Task]:
    """Retrieves list of tasks with filters applied"""
    query = db.query(Task)
    
    if assignee_id is not None:
        query = query.filter(Task.assignee_id == assignee_id)
        
    if status_filter:
        try:
            status_enum = TaskStatus(status_filter)
            query = query.filter(Task.status == status_enum)
        except ValueError:
            pass
            
    if priority_filter:
        try:
            priority_enum = TaskPriority(priority_filter)
            query = query.filter(Task.priority == priority_enum)
        except ValueError:
            pass
            
    if overdue_filter:
        # Overdue means due_date is in the past and status is not done
        query = query.filter(
            Task.due_date < date.today(),
            Task.status != TaskStatus.DONE
        )
        
    if company_id is not None:
        query = query.filter(Task.related_company_id == company_id)
        
    if deal_id is not None:
        query = query.filter(Task.related_deal_id == deal_id)
        
    # Sort tasks by due date (NULLs last) then priority (high -> medium -> low)
    return query.order_by(Task.due_date.asc().nullslast(), Task.created_at.desc()).all()


def get_task(db: Session, task_id: int) -> Optional[Task]:
    """Retrieves a single task by ID"""
    return db.query(Task).filter(Task.id == task_id).first()


def create_task(db: Session, task_in: TaskCreate) -> Task:
    """Creates a new task"""
    task = Task(
        title=task_in.title,
        description=task_in.description,
        due_date=task_in.due_date,
        status=task_in.status,
        priority=task_in.priority,
        assignee_id=task_in.assignee_id,
        related_company_id=task_in.related_company_id,
        related_deal_id=task_in.related_deal_id
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task_id: int, task_in: TaskUpdate) -> Optional[Task]:
    """Updates an existing task"""
    task = get_task(db, task_id)
    if not task:
        return None
        
    update_data = task_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
        
    db.commit()
    db.refresh(task)
    return task


def update_task_status(db: Session, task_id: int, status_str: str) -> Optional[Task]:
    """Quickly updates task status"""
    task = get_task(db, task_id)
    if not task:
        return None
        
    try:
        task.status = TaskStatus(status_str)
        db.commit()
        db.refresh(task)
        return task
    except ValueError:
        return None


def delete_task(db: Session, task_id: int) -> bool:
    """Deletes a task by ID"""
    task = get_task(db, task_id)
    if not task:
        return False
        
    db.delete(task)
    db.commit()
    return True

from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Form, Request, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.models.company import Company
from app.models.deal import Deal
from app.models.task import Task, TaskStatus, TaskPriority
from app.auth.dependencies import get_current_user, flash
from app.schemas.task import TaskCreate, TaskUpdate, TaskStatusUpdate, TaskRead
from app.services.task import (
    get_tasks, get_task, create_task, update_task, update_task_status, delete_task
)
from app.services.activity import log_activity

router = APIRouter(tags=["Tasks"])
templates = Jinja2Templates(directory="app/templates")


# ==========================================
# WEB PAGE ROUTES (SSR Forms & Lists)
# ==========================================

@router.get("/tasks", response_class=HTMLResponse)
def view_tasks_list(
    request: Request,
    view: str = "my",  # "my" or "all"
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    overdue: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Enforce role boundaries: sales reps can only see "My Tasks"
    if current_user.role == UserRole.SALES:
        view = "my"
        
    assignee_id = current_user.id if view == "my" else None
    overdue_bool = True if overdue == 1 else None
    
    tasks = get_tasks(
        db,
        assignee_id=assignee_id,
        status_filter=status_filter,
        priority_filter=priority_filter,
        overdue_filter=overdue_bool
    )
    
    return templates.TemplateResponse(
        request=request,
        name="tasks/index.html",
        context={
            "tasks": tasks,
            "view": view,
            "status_filter": status_filter or "",
            "priority_filter": priority_filter or "",
            "overdue": overdue or 0,
            "current_user": current_user,
            "TaskStatus": TaskStatus,
            "TaskPriority": TaskPriority,
            "UserRole": UserRole,
            "today": date.today()
        }
    )


@router.get("/tasks/create", response_class=HTMLResponse)
def render_create_task(
    request: Request,
    company_id: Optional[int] = None,
    deal_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    companies = db.query(Company).order_by(Company.name.asc()).all()
    deals = db.query(Deal).order_by(Deal.title.asc()).all()
    assignees = db.query(User).filter(User.is_active == True).order_by(User.name.asc()).all()
    
    return templates.TemplateResponse(
        request=request,
        name="tasks/form.html",
        context={
            "task": None,
            "companies": companies,
            "deals": deals,
            "assignees": assignees,
            "preselected_company_id": company_id,
            "preselected_deal_id": deal_id,
            "priorities": [p.value for p in TaskPriority],
            "statuses": [s.value for s in TaskStatus],
            "current_user": current_user
        }
    )


@router.post("/tasks/create")
def handle_create_task(
    request: Request,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    due_date: Optional[date] = Form(None),
    priority_val: str = Form("medium", alias="priority"),
    status_val: str = Form("open", alias="status"),
    assignee_id: int = Form(...),
    related_company_id: Optional[int] = Form(None),
    related_deal_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        task_in = TaskCreate(
            title=title,
            description=description,
            due_date=due_date,
            priority=TaskPriority(priority_val),
            status=TaskStatus(status_val),
            assignee_id=assignee_id,
            related_company_id=related_company_id or None,
            related_deal_id=related_deal_id or None
        )
    except ValueError as e:
        flash(request, f"Validation error: {e}", "danger")
        return RedirectResponse(url="/tasks/create", status_code=status.HTTP_303_SEE_OTHER)
        
    # Verify assignee exists
    assignee = db.query(User).filter(User.id == assignee_id).first()
    if not assignee:
        flash(request, "Selected assignee does not exist.", "danger")
        return RedirectResponse(url="/tasks/create", status_code=status.HTTP_303_SEE_OTHER)
        
    new_task = create_task(db, task_in)
    
    log_activity(
        db, current_user.id, "create", "Task", new_task.id,
        f"Created task '{new_task.title}' assigned to {assignee.name} (Due: {new_task.due_date or 'None'})"
    )
    
    flash(request, f"Task '{new_task.title}' created successfully.", "success")
    return RedirectResponse(url="/tasks", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/tasks/{task_id}/edit", response_class=HTMLResponse)
def render_edit_task(
    request: Request,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = get_task(db, task_id)
    if not task:
        flash(request, "Task not found.", "danger")
        return RedirectResponse(url="/tasks", status_code=status.HTTP_303_SEE_OTHER)
        
    companies = db.query(Company).order_by(Company.name.asc()).all()
    deals = db.query(Deal).order_by(Deal.title.asc()).all()
    assignees = db.query(User).filter(User.is_active == True).order_by(User.name.asc()).all()
    
    return templates.TemplateResponse(
        request=request,
        name="tasks/form.html",
        context={
            "task": task,
            "companies": companies,
            "deals": deals,
            "assignees": assignees,
            "priorities": [p.value for p in TaskPriority],
            "statuses": [s.value for s in TaskStatus],
            "current_user": current_user
        }
    )


@router.post("/tasks/{task_id}/edit")
def handle_edit_task(
    request: Request,
    task_id: int,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    due_date: Optional[date] = Form(None),
    priority_val: str = Form(..., alias="priority"),
    status_val: str = Form(..., alias="status"),
    assignee_id: int = Form(...),
    related_company_id: Optional[int] = Form(None),
    related_deal_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = get_task(db, task_id)
    if not task:
        flash(request, "Task not found.", "danger")
        return RedirectResponse(url="/tasks", status_code=status.HTTP_303_SEE_OTHER)
        
    try:
        task_in = TaskUpdate(
            title=title,
            description=description,
            due_date=due_date,
            priority=TaskPriority(priority_val),
            status=TaskStatus(status_val),
            assignee_id=assignee_id,
            related_company_id=related_company_id or None,
            related_deal_id=related_deal_id or None
        )
    except ValueError as e:
        flash(request, f"Validation error: {e}", "danger")
        return RedirectResponse(url=f"/tasks/{task_id}/edit", status_code=status.HTTP_303_SEE_OTHER)
        
    updated = update_task(db, task_id, task_in)
    
    log_activity(
        db, current_user.id, "update", "Task", task_id,
        f"Updated details for task '{updated.title}'"
    )
    
    flash(request, f"Task '{updated.title}' updated.", "success")
    return RedirectResponse(url="/tasks", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/tasks/{task_id}/delete")
def handle_delete_task(
    request: Request,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = get_task(db, task_id)
    if not task:
        flash(request, "Task not found.", "danger")
        return RedirectResponse(url="/tasks", status_code=status.HTTP_303_SEE_OTHER)
        
    title = task.title
    delete_task(db, task_id)
    
    log_activity(db, current_user.id, "delete", "Task", task_id, f"Deleted task '{title}'")
    
    flash(request, f"Task '{title}' has been deleted.", "success")
    return RedirectResponse(url="/tasks", status_code=status.HTTP_303_SEE_OTHER)


# ==========================================
# JSON API ENDPOINTS (/api/tasks)
# ==========================================

@router.patch("/api/tasks/{task_id}/status", response_model=TaskRead)
def api_update_task_status(
    task_id: int,
    body: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """PATCH endpoint called via checklist actions to mark a task as DONE (or other status)"""
    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    old_status = task.status.value
    updated = update_task_status(db, task_id, body.status.value)
    if not updated:
        raise HTTPException(status_code=400, detail="Invalid status transition")
        
    if old_status != updated.status.value:
        log_activity(
            db, current_user.id, "update", "Task", task_id,
            f"Updated task '{updated.title}' status: {old_status} -> {updated.status.value}"
        )
        
    return TaskRead.model_validate(updated)

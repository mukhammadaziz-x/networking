import math
from typing import Optional
from fastapi import APIRouter, Depends, Form, Request, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from datetime import date
from app.models.company import CompanyStatus
from app.models.task import TaskStatus, TaskPriority
from app.auth.dependencies import get_current_user, flash
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyRead
from app.services.company import (
    get_companies, get_company, create_company, update_company, delete_company
)
from app.services.activity import log_activity

router = APIRouter(tags=["Companies"])
templates = Jinja2Templates(directory="app/templates")

# ==========================================
# WEB PAGE ROUTES (Server-Side Rendered)
# ==========================================

@router.get("/companies", response_class=HTMLResponse)
def view_companies(
    request: Request,
    page: int = 1,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    limit = 10
    skip = (page - 1) * limit
    companies, total = get_companies(db, skip=skip, limit=limit, search=search, status=status_filter)
    
    total_pages = math.ceil(total / limit) if total > 0 else 1
    
    return templates.TemplateResponse(
        request=request,
        name="companies/index.html",
        context={
            "companies": companies,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "search": search or "",
            "status_filter": status_filter or "",
            "current_user": current_user,
            "CompanyStatus": CompanyStatus
        }
    )


@router.get("/companies/create", response_class=HTMLResponse)
def render_create_company(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    return templates.TemplateResponse(
        request=request,
        name="companies/form.html",
        context={
            "company": None,
            "current_user": current_user,
            "statuses": [s.value for s in CompanyStatus]
        }
    )


@router.post("/companies/create")
def handle_create_company(
    request: Request,
    name: str = Form(...),
    industry: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    status_val: str = Form("prospect", alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        company_in = CompanyCreate(
            name=name,
            industry=industry or None,
            phone=phone or None,
            email=email or None,
            website=website or None,
            address=address or None,
            city=city or None,
            country=country or None,
            status=CompanyStatus(status_val)
        )
    except ValueError as e:
        flash(request, f"Validation error: {e}", "danger")
        return RedirectResponse(url="/companies/create", status_code=status.HTTP_303_SEE_OTHER)

    new_company = create_company(db, company_in, owner_id=current_user.id)
    
    # Audit log
    log_activity(
        db, current_user.id, "create", "Company", new_company.id,
        f"Created company '{new_company.name}'"
    )
    
    flash(request, f"Company '{new_company.name}' created successfully.", "success")
    return RedirectResponse(url=f"/companies/{new_company.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/companies/{company_id}", response_class=HTMLResponse)
def view_company_details(
    request: Request,
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    company = get_company(db, company_id)
    if not company:
        flash(request, "Company not found.", "danger")
        return RedirectResponse(url="/companies", status_code=status.HTTP_303_SEE_OTHER)
        
    return templates.TemplateResponse(
        request=request,
        name="companies/detail.html",
        context={
            "company": company,
            "contacts": company.contacts,
            "deals": company.deals,
            "orders": company.orders,
            "tasks": company.tasks,
            "current_user": current_user,
            "TaskStatus": TaskStatus,
            "TaskPriority": TaskPriority,
            "CompanyStatus": CompanyStatus,
            "today": date.today()
        }
    )


@router.get("/companies/{company_id}/edit", response_class=HTMLResponse)
def render_edit_company(
    request: Request,
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    company = get_company(db, company_id)
    if not company:
        flash(request, "Company not found.", "danger")
        return RedirectResponse(url="/companies", status_code=status.HTTP_303_SEE_OTHER)
        
    return templates.TemplateResponse(
        request=request,
        name="companies/form.html",
        context={
            "company": company,
            "current_user": current_user,
            "statuses": [s.value for s in CompanyStatus]
        }
    )


@router.post("/companies/{company_id}/edit")
def handle_edit_company(
    request: Request,
    company_id: int,
    name: str = Form(...),
    industry: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    status_val: str = Form(..., alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    company = get_company(db, company_id)
    if not company:
        flash(request, "Company not found.", "danger")
        return RedirectResponse(url="/companies", status_code=status.HTTP_303_SEE_OTHER)

    try:
        company_in = CompanyUpdate(
            name=name,
            industry=industry or None,
            phone=phone or None,
            email=email or None,
            website=website or None,
            address=address or None,
            city=city or None,
            country=country or None,
            status=CompanyStatus(status_val)
        )
    except ValueError as e:
        flash(request, f"Validation error: {e}", "danger")
        return RedirectResponse(url=f"/companies/{company_id}/edit", status_code=status.HTTP_303_SEE_OTHER)

    updated = update_company(db, company_id, company_in)
    
    # Audit log
    log_activity(
        db, current_user.id, "update", "Company", company_id,
        f"Updated company '{updated.name}' details"
    )

    flash(request, f"Company '{updated.name}' updated successfully.", "success")
    return RedirectResponse(url=f"/companies/{company_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/companies/{company_id}/delete")
def handle_delete_company(
    request: Request,
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    company = get_company(db, company_id)
    if not company:
        flash(request, "Company not found.", "danger")
        return RedirectResponse(url="/companies", status_code=status.HTTP_303_SEE_OTHER)

    company_name = company.name
    delete_company(db, company_id)
    
    # Audit log
    log_activity(
        db, current_user.id, "delete", "Company", company_id,
        f"Deleted company '{company_name}'"
    )

    flash(request, f"Company '{company_name}' has been deleted.", "success")
    return RedirectResponse(url="/companies", status_code=status.HTTP_303_SEE_OTHER)


# ==========================================
# JSON API ENDPOINTS (/api/companies)
# ==========================================

@router.get("/api/companies", response_model=dict)
def api_list_companies(
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user)
):
    companies, total = get_companies(db, skip=skip, limit=limit, search=search, status=status_filter)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "companies": [CompanyRead.model_validate(c) for c in companies]
    }


@router.get("/api/companies/{company_id}", response_model=CompanyRead)
def api_get_company(
    company_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user)
):
    company = get_company(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyRead.model_validate(company)


@router.post("/api/companies", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def api_create_company(
    company_in: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_company = create_company(db, company_in, owner_id=current_user.id)
    log_activity(db, current_user.id, "create", "Company", new_company.id, f"API created company '{new_company.name}'")
    return CompanyRead.model_validate(new_company)


@router.put("/api/companies/{company_id}", response_model=CompanyRead)
def api_update_company(
    company_id: int,
    company_in: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    updated = update_company(db, company_id, company_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Company not found")
    log_activity(db, current_user.id, "update", "Company", company_id, f"API updated company '{updated.name}'")
    return CompanyRead.model_validate(updated)


@router.delete("/api/companies/{company_id}", response_model=dict)
def api_delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    company = get_company(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company_name = company.name
    delete_company(db, company_id)
    log_activity(db, current_user.id, "delete", "Company", company_id, f"API deleted company '{company_name}'")
    return {"status": "ok", "message": f"Company '{company_name}' deleted successfully"}

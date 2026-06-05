import math
from typing import Optional
from fastapi import APIRouter, Depends, Form, Request, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.company import Company
from app.auth.dependencies import get_current_user, flash
from app.schemas.contact import ContactCreate, ContactUpdate, ContactRead
from app.services.contact import (
    get_contacts, get_contact, create_contact, update_contact, delete_contact
)
from app.services.activity import log_activity

router = APIRouter(tags=["Contacts"])
templates = Jinja2Templates(directory="app/templates")

# ==========================================
# WEB PAGE ROUTES (Server-Side Rendered)
# ==========================================

@router.get("/contacts", response_class=HTMLResponse)
def view_contacts(
    request: Request,
    page: int = 1,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    limit = 10
    skip = (page - 1) * limit
    contacts, total = get_contacts(db, skip=skip, limit=limit, search=search)
    
    total_pages = math.ceil(total / limit) if total > 0 else 1
    
    return templates.TemplateResponse(
        request=request,
        name="contacts/index.html",
        context={
            "contacts": contacts,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "search": search or "",
            "current_user": current_user
        }
    )


@router.get("/contacts/create", response_class=HTMLResponse)
def render_create_contact(
    request: Request,
    company_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fetch active companies for the drop-down selector
    companies = db.query(Company).order_by(Company.name.asc()).all()
    return templates.TemplateResponse(
        request=request,
        name="contacts/form.html",
        context={
            "contact": None,
            "companies": companies,
            "current_user": current_user,
            "preselected_company_id": company_id
        }
    )


@router.post("/contacts/create")
def handle_create_contact(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone: Optional[str] = Form(None),
    position: Optional[str] = Form(None),
    company_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        contact_in = ContactCreate(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone or None,
            position=position or None,
            company_id=company_id
        )
    except ValueError as e:
        flash(request, f"Validation error: {e}", "danger")
        return RedirectResponse(url="/contacts/create", status_code=status.HTTP_303_SEE_OTHER)

    new_contact = create_contact(db, contact_in, owner_id=current_user.id)
    
    # Audit log
    log_activity(
        db, current_user.id, "create", "Contact", new_contact.id,
        f"Created contact '{new_contact.first_name} {new_contact.last_name}'"
    )
    
    flash(request, f"Contact '{new_contact.first_name} {new_contact.last_name}' created successfully.", "success")
    
    # Redirect to related company detail page
    return RedirectResponse(url=f"/companies/{new_contact.company_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/contacts/{contact_id}/edit", response_class=HTMLResponse)
def render_edit_contact(
    request: Request,
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = get_contact(db, contact_id)
    if not contact:
        flash(request, "Contact not found.", "danger")
        return RedirectResponse(url="/contacts", status_code=status.HTTP_303_SEE_OTHER)
        
    companies = db.query(Company).order_by(Company.name.asc()).all()
    return templates.TemplateResponse(
        request=request,
        name="contacts/form.html",
        context={
            "contact": contact,
            "companies": companies,
            "current_user": current_user
        }
    )


@router.post("/contacts/{contact_id}/edit")
def handle_edit_contact(
    request: Request,
    contact_id: int,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone: Optional[str] = Form(None),
    position: Optional[str] = Form(None),
    company_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = get_contact(db, contact_id)
    if not contact:
        flash(request, "Contact not found.", "danger")
        return RedirectResponse(url="/contacts", status_code=status.HTTP_303_SEE_OTHER)

    try:
        contact_in = ContactUpdate(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone or None,
            position=position or None,
            company_id=company_id
        )
    except ValueError as e:
        flash(request, f"Validation error: {e}", "danger")
        return RedirectResponse(url=f"/contacts/{contact_id}/edit", status_code=status.HTTP_303_SEE_OTHER)

    updated = update_contact(db, contact_id, contact_in)
    
    # Audit log
    log_activity(
        db, current_user.id, "update", "Contact", contact_id,
        f"Updated contact '{updated.first_name} {updated.last_name}' details"
    )

    flash(request, f"Contact '{updated.first_name} {updated.last_name}' updated successfully.", "success")
    return RedirectResponse(url=f"/companies/{updated.company_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/contacts/{contact_id}/delete")
def handle_delete_contact(
    request: Request,
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = get_contact(db, contact_id)
    if not contact:
        flash(request, "Contact not found.", "danger")
        return RedirectResponse(url="/contacts", status_code=status.HTTP_303_SEE_OTHER)

    contact_name = f"{contact.first_name} {contact.last_name}"
    company_id = contact.company_id
    delete_contact(db, contact_id)
    
    # Audit log
    log_activity(
        db, current_user.id, "delete", "Contact", contact_id,
        f"Deleted contact '{contact_name}'"
    )

    flash(request, f"Contact '{contact_name}' has been deleted.", "success")
    return RedirectResponse(url=f"/companies/{company_id}", status_code=status.HTTP_303_SEE_OTHER)


# ==========================================
# JSON API ENDPOINTS (/api/contacts)
# ==========================================

@router.get("/api/contacts", response_model=dict)
def api_list_contacts(
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user)
):
    contacts, total = get_contacts(db, skip=skip, limit=limit, search=search)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "contacts": [ContactRead.model_validate(c) for c in contacts]
    }


@router.get("/api/contacts/{contact_id}", response_model=ContactRead)
def api_get_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user)
):
    contact = get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return ContactRead.model_validate(contact)


@router.post("/api/contacts", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
def api_create_contact(
    contact_in: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_contact = create_contact(db, contact_in, owner_id=current_user.id)
    log_activity(db, current_user.id, "create", "Contact", new_contact.id, f"API created contact '{new_contact.first_name}'")
    return ContactRead.model_validate(new_contact)


@router.put("/api/contacts/{contact_id}", response_model=ContactRead)
def api_update_contact(
    contact_id: int,
    contact_in: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    updated = update_contact(db, contact_id, contact_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Contact not found")
    log_activity(db, current_user.id, "update", "Contact", contact_id, f"API updated contact '{updated.first_name}'")
    return ContactRead.model_validate(updated)


@router.delete("/api/contacts/{contact_id}", response_model=dict)
def api_delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    contact_name = f"{contact.first_name} {contact.last_name}"
    delete_contact(db, contact_id)
    log_activity(db, current_user.id, "delete", "Contact", contact_id, f"API deleted contact '{contact_name}'")
    return {"status": "ok", "message": f"Contact '{contact_name}' deleted successfully"}

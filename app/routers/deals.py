from typing import Optional
from decimal import Decimal
from datetime import date
from fastapi import APIRouter, Depends, Form, Request, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.deal import Deal, DealStage
from app.models.company import Company
from app.models.contact import Contact
from app.auth.dependencies import get_current_user, flash
from app.schemas.deal import DealCreate, DealUpdate, DealRead
from app.services.deal import (
    get_deals, get_deal, create_deal, update_deal, update_deal_stage, delete_deal
)
from app.services.activity import log_activity

router = APIRouter(tags=["Deals"])
templates = Jinja2Templates(directory="app/templates")

# ==========================================
# WEB PAGE ROUTES (Kanban & Forms)
# ==========================================

@router.get("/deals", response_class=HTMLResponse)
def view_kanban_board(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Renders the Kanban Opportunity Pipeline view"""
    deals = db.query(Deal).all()
    
    # Structure columns and calculate aggregate values per stage
    pipeline = {
        "lead": {"title": "Lead", "deals": [], "total": Decimal("0.00")},
        "qualified": {"title": "Qualified", "deals": [], "total": Decimal("0.00")},
        "proposal": {"title": "Proposal", "deals": [], "total": Decimal("0.00")},
        "won": {"title": "Won", "deals": [], "total": Decimal("0.00")},
        "lost": {"title": "Lost", "deals": [], "total": Decimal("0.00")}
    }
    
    for deal in deals:
        stage_val = deal.stage.value
        if stage_val in pipeline:
            pipeline[stage_val]["deals"].append(deal)
            pipeline[stage_val]["total"] += deal.amount
            
    return templates.TemplateResponse(
        request=request,
        name="deals/index.html",
        context={
            "pipeline": pipeline,
            "current_user": current_user,
            "DealStage": DealStage
        }
    )


@router.get("/deals/create", response_class=HTMLResponse)
def render_create_deal(
    request: Request,
    company_id: Optional[int] = None,
    contact_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Renders create opportunity form, pre-populating fields if requested"""
    companies = db.query(Company).order_by(Company.name.asc()).all()
    contacts = db.query(Contact).order_by(Contact.first_name.asc()).all()
    
    return templates.TemplateResponse(
        request=request,
        name="deals/form.html",
        context={
            "deal": None,
            "companies": companies,
            "contacts": contacts,
            "preselected_company_id": company_id,
            "preselected_contact_id": contact_id,
            "stages": [s.value for s in DealStage],
            "current_user": current_user
        }
    )


@router.post("/deals/create")
def handle_create_deal(
    request: Request,
    title: str = Form(...),
    company_id: int = Form(...),
    contact_id: Optional[int] = Form(None),
    stage_val: str = Form("lead", alias="stage"),
    amount: Decimal = Form(...),
    expected_close_date: Optional[date] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        deal_in = DealCreate(
            title=title,
            company_id=company_id,
            contact_id=contact_id,
            stage=DealStage(stage_val),
            amount=amount,
            expected_close_date=expected_close_date
        )
    except ValueError as e:
        flash(request, f"Validation error: {e}", "danger")
        return RedirectResponse(url="/deals/create", status_code=status.HTTP_303_SEE_OTHER)

    new_deal = create_deal(db, deal_in, owner_id=current_user.id)
    
    log_activity(
        db, current_user.id, "create", "Deal", new_deal.id,
        f"Created deal opportunity '{new_deal.title}' for ${new_deal.amount:,.2f} (Stage: {new_deal.stage.value})"
    )
    
    flash(request, f"Opportunity '{new_deal.title}' logged in pipeline.", "success")
    return RedirectResponse(url="/deals", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/deals/{deal_id}/edit", response_class=HTMLResponse)
def render_edit_deal(
    request: Request,
    deal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deal = get_deal(db, deal_id)
    if not deal:
        flash(request, "Deal not found.", "danger")
        return RedirectResponse(url="/deals", status_code=status.HTTP_303_SEE_OTHER)
        
    companies = db.query(Company).order_by(Company.name.asc()).all()
    contacts = db.query(Contact).order_by(Contact.first_name.asc()).all()
    
    return templates.TemplateResponse(
        request=request,
        name="deals/form.html",
        context={
            "deal": deal,
            "companies": companies,
            "contacts": contacts,
            "stages": [s.value for s in DealStage],
            "current_user": current_user
        }
    )


@router.post("/deals/{deal_id}/edit")
def handle_edit_deal(
    request: Request,
    deal_id: int,
    title: str = Form(...),
    company_id: int = Form(...),
    contact_id: Optional[int] = Form(None),
    stage_val: str = Form(..., alias="stage"),
    amount: Decimal = Form(...),
    expected_close_date: Optional[date] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deal = get_deal(db, deal_id)
    if not deal:
        flash(request, "Deal not found.", "danger")
        return RedirectResponse(url="/deals", status_code=status.HTTP_303_SEE_OTHER)

    old_stage = deal.stage.value
    try:
        deal_in = DealUpdate(
            title=title,
            company_id=company_id,
            contact_id=contact_id,
            stage=DealStage(stage_val),
            amount=amount,
            expected_close_date=expected_close_date
        )
    except ValueError as e:
        flash(request, f"Validation error: {e}", "danger")
        return RedirectResponse(url=f"/deals/{deal_id}/edit", status_code=status.HTTP_303_SEE_OTHER)

    updated = update_deal(db, deal_id, deal_in)
    
    description = f"Updated deal '{updated.title}' details"
    if old_stage != updated.stage.value:
        description += f" (Stage changed from {old_stage} to {updated.stage.value})"
        
    log_activity(db, current_user.id, "update", "Deal", deal_id, description)

    flash(request, f"Opportunity '{updated.title}' saved.", "success")
    return RedirectResponse(url="/deals", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/deals/{deal_id}/delete")
def handle_delete_deal(
    request: Request,
    deal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deal = get_deal(db, deal_id)
    if not deal:
        flash(request, "Deal not found.", "danger")
        return RedirectResponse(url="/deals", status_code=status.HTTP_303_SEE_OTHER)

    deal_title = deal.title
    delete_deal(db, deal_id)
    
    log_activity(db, current_user.id, "delete", "Deal", deal_id, f"Deleted opportunity '{deal_title}'")
    flash(request, f"Opportunity '{deal_title}' deleted.", "success")
    return RedirectResponse(url="/deals", status_code=status.HTTP_303_SEE_OTHER)


# ==========================================
# JSON API ENDPOINTS (/api/deals)
# ==========================================

class StageUpdateBody(Jinja2Templates):
    # Simply mapping a temporary Pydantic model for request parsing
    pass

from pydantic import BaseModel
class StageUpdateSchema(BaseModel):
    stage: str


@router.patch("/api/deals/{deal_id}/stage", response_model=DealRead)
def api_update_deal_stage(
    deal_id: int,
    body: StageUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """PATCH endpoint called via Drag & Drop Kanban to persist stage updates"""
    deal = get_deal(db, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
        
    old_stage = deal.stage.value
    try:
        updated = update_deal_stage(db, deal_id, body.stage)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid stage value: {e}")
        
    if old_stage != updated.stage.value:
        log_activity(
            db, current_user.id, "update", "Deal", deal_id,
            f"Kanban drag-drop updated deal '{updated.title}' stage: {old_stage} -> {updated.stage.value}"
        )
        
    return DealRead.model_validate(updated)

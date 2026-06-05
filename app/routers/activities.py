from typing import Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.activity import Activity
from app.auth.dependencies import get_current_user

router = APIRouter(tags=["Activities"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/activities", response_class=HTMLResponse)
def view_activities_feed(
    request: Request,
    user_filter: Optional[int] = None,
    entity_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Activity)
    
    if user_filter:
        query = query.filter(Activity.user_id == user_filter)
        
    if entity_filter:
        query = query.filter(Activity.entity_type == entity_filter)
        
    # Get latest 100 entries
    activities = query.order_by(Activity.created_at.desc()).limit(100).all()
    
    # Get distinct entity types from DB for filters
    db_entity_types = db.query(Activity.entity_type).distinct().all()
    entity_types = sorted([et[0] for et in db_entity_types if et[0]])
    
    # Get all users for filters dropdown
    users = db.query(User).order_by(User.name.asc()).all()
    
    return templates.TemplateResponse(
        request=request,
        name="activities/index.html",
        context={
            "activities": activities,
            "users": users,
            "entity_types": entity_types,
            "selected_user_id": user_filter or 0,
            "selected_entity": entity_filter or "",
            "current_user": current_user
        }
    )

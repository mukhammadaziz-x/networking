from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.services.dashboard import (
    get_dashboard_kpis, get_chart_data, get_sales_report_data, get_pipeline_report_data
)

router = APIRouter(tags=["Dashboard & Reports"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/reports", response_class=HTMLResponse)
def view_reports(
    request: Request,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Default date range: last 30 days
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
        
    sales_data = get_sales_report_data(db, start_date, end_date)
    pipeline_data = get_pipeline_report_data(db)
    
    return templates.TemplateResponse(
        request=request,
        name="reports/index.html",
        context={
            "sales": sales_data,
            "pipeline": pipeline_data,
            "current_user": current_user,
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d')
        }
    )


@router.get("/api/dashboard/data", response_class=JSONResponse)
def get_api_dashboard_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """API endpoint providing KPIs and Chart.js datasets to the frontend"""
    kpis = get_dashboard_kpis(db)
    charts = get_chart_data(db)
    return {
        "kpis": kpis,
        "charts": charts
    }

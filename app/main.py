from fastapi import FastAPI, Request, Depends, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.auth.dependencies import (
    NeedLoginException,
    RoleDeniedException,
    get_flashes,
    get_current_user
)
from app.models.user import User
from app.models.activity import Activity
from app.services.dashboard import get_dashboard_kpis
from app.routers import auth, users, companies, contacts, products, deals, orders, tasks, activities, dashboard

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Wholesale Clothing Distribution CRM Back-Office",
    version="0.1.0"
)

# Add session middleware for session-based auth (uses secure signed cookies via itsdangerous)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="clothcrm_session",
    same_site="lax",
    https_only=False,  # Set to True in production with SSL
)

# Mount static directories
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["get_flashes"] = get_flashes


# Register Exception Handlers
@app.exception_handler(NeedLoginException)
async def need_login_exception_handler(request: Request, exc: NeedLoginException):
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@app.exception_handler(RoleDeniedException)
async def role_denied_exception_handler(request: Request, exc: RoleDeniedException):
    from app.auth.dependencies import flash
    flash(request, exc.message, "danger")
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(companies.router)
app.include_router(contacts.router)
app.include_router(products.router)
app.include_router(deals.router)
app.include_router(orders.router)
app.include_router(tasks.router)
app.include_router(activities.router)
app.include_router(dashboard.router)


@app.get("/health", response_class=JSONResponse)
def health_check():
    """Health check endpoint for container orchestrators and load balancers"""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Renders the dashboard / landing page"""
    kpis = get_dashboard_kpis(db)
    activities = db.query(Activity).order_by(Activity.created_at.desc()).limit(5).all()
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "current_user": current_user,
            "kpis": kpis,
            "activities": activities
        }
    )

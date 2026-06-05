from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from app.config import settings

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


@app.get("/health", response_class=JSONResponse)
def health_check():
    """Health check endpoint for container orchestrators and load balancers"""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Renders the dashboard / landing page"""
    return templates.TemplateResponse(request=request, name="home.html")

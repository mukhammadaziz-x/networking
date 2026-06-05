from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.auth.security import verify_password
from app.auth.dependencies import flash

router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Renders the login page if not logged in; otherwise redirects to homepage"""
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="login.html")


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Authenticates the user and sets session details"""
    user = db.query(User).filter(User.email == email).first()
    
    if not user or not verify_password(password, user.password_hash):
        flash(request, "Invalid email or password.", "danger")
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        
    if not user.is_active:
        flash(request, "Your account is inactive. Please contact an administrator.", "danger")
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        
    # Store credentials in session cookie
    request.session["user_id"] = user.id
    flash(request, f"Welcome back, {user.name}!", "success")
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/logout")
def logout(request: Request):
    """Clears the session cookie and signs out user"""
    request.session.clear()
    flash(request, "You have been successfully logged out.", "success")
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

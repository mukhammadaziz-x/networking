from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.auth.security import get_password_hash
from app.auth.dependencies import require_role, flash, get_current_user

router = APIRouter(prefix="/users", tags=["Users Management"])
templates = Jinja2Templates(directory="app/templates")

# Restrict the entire router to admin role
admin_protection = Depends(require_role("admin"))


@router.get("", response_class=HTMLResponse)
def list_users(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _auth=admin_protection
):
    """Lists all users in the system"""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return templates.TemplateResponse(
        request=request,
        name="users.html",
        context={"users": users, "current_user": current_user, "UserRole": UserRole}
    )


@router.post("")
def create_user(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
    _auth=admin_protection
):
    """Creates a new user account"""
    # Check if email is already taken
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        flash(request, "Email address is already in use.", "danger")
        return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)

    try:
        # Validate role
        role_enum = UserRole(role)
    except ValueError:
        flash(request, "Invalid user role specified.", "danger")
        return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)

    new_user = User(
        name=name,
        email=email,
        password_hash=get_password_hash(password),
        role=role_enum,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    
    flash(request, f"User '{name}' has been created successfully.", "success")
    return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{user_id}/toggle")
def toggle_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _auth=admin_protection
):
    """Toggles a user's active status. Admins cannot deactivate themselves."""
    if user_id == current_user.id:
        flash(request, "You cannot deactivate your own account.", "danger")
        return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        flash(request, "User not found.", "danger")
        return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)

    user.is_active = not user.is_active
    db.commit()

    status_str = "activated" if user.is_active else "deactivated"
    flash(request, f"User '{user.name}' status has been {status_str}.", "success")
    return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{user_id}/role")
def change_role(
    request: Request,
    user_id: int,
    role: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _auth=admin_protection
):
    """Changes a user's role. Admins cannot change their own role."""
    if user_id == current_user.id:
        flash(request, "You cannot change your own role.", "danger")
        return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)

    try:
        role_enum = UserRole(role)
    except ValueError:
        flash(request, "Invalid user role specified.", "danger")
        return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        flash(request, "User not found.", "danger")
        return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)

    user.role = role_enum
    db.commit()

    flash(request, f"User '{user.name}' role has been changed to '{role_enum.value}'.", "success")
    return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)

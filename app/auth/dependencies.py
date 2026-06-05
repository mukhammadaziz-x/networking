from typing import List, Generator
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User


class NeedLoginException(Exception):
    """Custom exception raised when authentication is required but missing"""
    pass


class RoleDeniedException(Exception):
    """Custom exception raised when a user does not have permission for an action"""
    def __init__(self, message: str = "Access denied: unauthorized role"):
        self.message = message
        super().__init__(message)


def flash(request: Request, message: str, category: str = "success") -> None:
    """Stores a flash message in the user session"""
    if "_flashes" not in request.session:
        request.session["_flashes"] = []
    request.session["_flashes"].append({"message": message, "category": category})


def get_flashes(request: Request) -> List[dict]:
    """Retrieves and clears all flash messages from the session"""
    return request.session.pop("_flashes", [])


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """FastAPI dependency to retrieve the currently logged-in user"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise NeedLoginException()
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        request.session.clear()
        raise NeedLoginException()
        
    if not user.is_active:
        flash(request, "Your account has been deactivated.", "danger")
        request.session.clear()
        raise NeedLoginException()
        
    return user


class require_role:
    """FastAPI dependency to restrict routes to specified roles"""
    def __init__(self, *allowed_roles: str):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise RoleDeniedException("You do not have permission to access this page.")
        return current_user

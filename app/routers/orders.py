import json
import math
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, Form, Request, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.company import Company
from app.models.product import Product
from app.models.order import Order, OrderStatus
from app.auth.dependencies import get_current_user, flash
from app.schemas.order import OrderCreate, OrderItemCreate, OrderRead
from app.services.order import (
    get_orders, get_order, create_order, update_order_status
)
from app.services.activity import log_activity

router = APIRouter(tags=["Orders"])
templates = Jinja2Templates(directory="app/templates")


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to convert Decimal to float for frontend consumption"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


# ==========================================
# WEB PAGE ROUTES (SSR Invoice & Forms)
# ==========================================

@router.get("/orders", response_class=HTMLResponse)
def view_orders(
    request: Request,
    page: int = 1,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    limit = 10
    skip = (page - 1) * limit
    orders, total = get_orders(db, skip=skip, limit=limit, search=search, status_filter=status_filter)
    
    total_pages = math.ceil(total / limit) if total > 0 else 1
    
    return templates.TemplateResponse(
        request=request,
        name="orders/index.html",
        context={
            "orders": orders,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "search": search or "",
            "status_filter": status_filter or "",
            "current_user": current_user,
            "OrderStatus": OrderStatus
        }
    )


@router.get("/orders/create", response_class=HTMLResponse)
def render_create_order(
    request: Request,
    company_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    companies = db.query(Company).order_by(Company.name.asc()).all()
    products = db.query(Product).filter(Product.is_active == True).order_by(Product.name.asc()).all()
    
    # Map products to a JSON string for real-time frontend calculations
    prod_map = {
        p.id: {
            "name": p.name,
            "sku": p.sku,
            "price": p.price,
            "stock_qty": p.stock_qty
        } for p in products
    }
    products_json = json.dumps(prod_map, cls=DecimalEncoder)
    
    return templates.TemplateResponse(
        request=request,
        name="orders/create.html",
        context={
            "companies": companies,
            "products": products,
            "products_json": products_json,
            "preselected_company_id": company_id,
            "current_user": current_user
        }
    )


@router.post("/orders/create")
def handle_create_order(
    request: Request,
    company_id: int = Form(...),
    product_ids: List[int] = Form(..., alias="product_id"),
    quantities: List[int] = Form(..., alias="quantity"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items_in = []
    
    # Process zip parameters
    for pid, qty in zip(product_ids, quantities):
        if not pid or qty <= 0:
            continue
            
        product = db.query(Product).filter(Product.id == pid).first()
        if not product:
            flash(request, f"Product ID {pid} not found.", "danger")
            return RedirectResponse(url="/orders/create", status_code=status.HTTP_303_SEE_OTHER)
            
        items_in.append(
            OrderItemCreate(
                product_id=pid,
                quantity=qty,
                unit_price=product.price
            )
        )
        
    if not items_in:
        flash(request, "An order must contain at least one valid line item.", "danger")
        return RedirectResponse(url="/orders/create", status_code=status.HTTP_303_SEE_OTHER)
        
    try:
        order_in = OrderCreate(
            company_id=company_id,
            status=OrderStatus.DRAFT,
            items=items_in
        )
        new_order = create_order(db, order_in, creator_id=current_user.id)
    except Exception as e:
        flash(request, f"Error creating order: {e}", "danger")
        return RedirectResponse(url="/orders/create", status_code=status.HTTP_303_SEE_OTHER)
        
    log_activity(
        db, current_user.id, "create", "Order", new_order.id,
        f"Created wholesale order '{new_order.order_number}' (Total: ${new_order.total_amount:,.2f})"
    )
    
    flash(request, f"Order {new_order.order_number} created successfully.", "success")
    return RedirectResponse(url=f"/orders/{new_order.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/orders/{order_id}", response_class=HTMLResponse)
def view_order_details(
    request: Request,
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = get_order(db, order_id)
    if not order:
        flash(request, "Order not found.", "danger")
        return RedirectResponse(url="/orders", status_code=status.HTTP_303_SEE_OTHER)
        
    return templates.TemplateResponse(
        request=request,
        name="orders/detail.html",
        context={
            "order": order,
            "current_user": current_user,
            "OrderStatus": OrderStatus
        }
    )


@router.post("/orders/{order_id}/status")
def handle_change_order_status(
    request: Request,
    order_id: int,
    status_val: str = Form(..., alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = get_order(db, order_id)
    if not order:
        flash(request, "Order not found.", "danger")
        return RedirectResponse(url="/orders", status_code=status.HTTP_303_SEE_OTHER)
        
    old_status = order.status.value
    try:
        updated = update_order_status(db, order_id, status_val, current_user.id)
    except ValueError as e:
        # Catch insufficient stock validation errors
        flash(request, str(e), "danger")
        return RedirectResponse(url=f"/orders/{order_id}", status_code=status.HTTP_303_SEE_OTHER)
        
    log_activity(
        db, current_user.id, "update", "Order", order_id,
        f"Updated order '{updated.order_number}' status: {old_status} -> {updated.status.value}"
    )
    
    flash(request, f"Order status updated to '{updated.status.value}'.", "success")
    return RedirectResponse(url=f"/orders/{order_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/orders/{order_id}/delete")
def handle_delete_order(
    request: Request,
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = get_order(db, order_id)
    if not order:
        flash(request, "Order not found.", "danger")
        return RedirectResponse(url="/orders", status_code=status.HTTP_303_SEE_OTHER)
        
    order_number = order.order_number
    # Order deletion (usually restricted to drafts or cancelled, but we will allow it for simplicity)
    db.delete(order)
    db.commit()
    
    log_activity(db, current_user.id, "delete", "Order", order_id, f"Deleted order '{order_number}'")
    flash(request, f"Order '{order_number}' has been deleted.", "success")
    return RedirectResponse(url="/orders", status_code=status.HTTP_303_SEE_OTHER)

import math
from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, Form, Request, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.product import Product
from app.auth.dependencies import get_current_user, flash
from app.schemas.product import ProductCreate, ProductUpdate, ProductRead
from app.services.product import (
    get_products, get_product, create_product, update_product, delete_product
)
from app.services.activity import log_activity

router = APIRouter(tags=["Products"])
templates = Jinja2Templates(directory="app/templates")

# ==========================================
# WEB PAGE ROUTES (Server-Side Rendered)
# ==========================================

@router.get("/products", response_class=HTMLResponse)
def view_products(
    request: Request,
    page: int = 1,
    search: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    limit = 10
    skip = (page - 1) * limit
    products, total = get_products(db, skip=skip, limit=limit, search=search, category=category)
    
    # Get distinct categories for the filter sidebar / header dropdown
    categories_raw = db.query(Product.category).distinct().filter(Product.category.isnot(None)).all()
    categories = [c[0] for c in categories_raw if c[0]]
    
    total_pages = math.ceil(total / limit) if total > 0 else 1
    
    return templates.TemplateResponse(
        request=request,
        name="products/index.html",
        context={
            "products": products,
            "categories": categories,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "search": search or "",
            "category_filter": category or "",
            "current_user": current_user
        }
    )


@router.get("/products/create", response_class=HTMLResponse)
def render_create_product(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    return templates.TemplateResponse(
        request=request,
        name="products/form.html",
        context={
            "product": None,
            "current_user": current_user
        }
    )


@router.post("/products/create")
def handle_create_product(
    request: Request,
    sku: str = Form(...),
    name: str = Form(...),
    category: Optional[str] = Form(None),
    size: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    price: Decimal = Form(...),
    stock_qty: int = Form(...),
    is_active: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if SKU is taken
    existing_product = db.query(Product).filter(Product.sku == sku).first()
    if existing_product:
        flash(request, "Product SKU is already in use.", "danger")
        return RedirectResponse(url="/products/create", status_code=status.HTTP_303_SEE_OTHER)

    try:
        product_in = ProductCreate(
            sku=sku,
            name=name,
            category=category or None,
            size=size or None,
            color=color or None,
            price=price,
            stock_qty=stock_qty,
            is_active=is_active
        )
    except ValueError as e:
        flash(request, f"Validation error: {e}", "danger")
        return RedirectResponse(url="/products/create", status_code=status.HTTP_303_SEE_OTHER)

    new_product = create_product(db, product_in)
    
    # Audit log
    log_activity(
        db, current_user.id, "create", "Product", new_product.id,
        f"Created product '{new_product.name}' (SKU: {new_product.sku})"
    )
    
    flash(request, f"Product '{new_product.name}' created successfully.", "success")
    return RedirectResponse(url="/products", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/products/{product_id}/edit", response_class=HTMLResponse)
def render_edit_product(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = get_product(db, product_id)
    if not product:
        flash(request, "Product not found.", "danger")
        return RedirectResponse(url="/products", status_code=status.HTTP_303_SEE_OTHER)
        
    return templates.TemplateResponse(
        request=request,
        name="products/form.html",
        context={
            "product": product,
            "current_user": current_user
        }
    )


@router.post("/products/{product_id}/edit")
def handle_edit_product(
    request: Request,
    product_id: int,
    sku: str = Form(...),
    name: str = Form(...),
    category: Optional[str] = Form(None),
    size: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    price: Decimal = Form(...),
    stock_qty: int = Form(...),
    is_active: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = get_product(db, product_id)
    if not product:
        flash(request, "Product not found.", "danger")
        return RedirectResponse(url="/products", status_code=status.HTTP_303_SEE_OTHER)

    # Check if SKU is taken by another product
    existing = db.query(Product).filter(Product.sku == sku, Product.id != product_id).first()
    if existing:
        flash(request, "Product SKU is already in use.", "danger")
        return RedirectResponse(url=f"/products/{product_id}/edit", status_code=status.HTTP_303_SEE_OTHER)

    try:
        product_in = ProductUpdate(
            sku=sku,
            name=name,
            category=category or None,
            size=size or None,
            color=color or None,
            price=price,
            stock_qty=stock_qty,
            is_active=is_active
        )
    except ValueError as e:
        flash(request, f"Validation error: {e}", "danger")
        return RedirectResponse(url=f"/products/{product_id}/edit", status_code=status.HTTP_303_SEE_OTHER)

    updated = update_product(db, product_id, product_in)
    
    # Audit log
    log_activity(
        db, current_user.id, "update", "Product", product_id,
        f"Updated product '{updated.name}' details"
    )

    flash(request, f"Product '{updated.name}' updated successfully.", "success")
    return RedirectResponse(url="/products", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/products/{product_id}/delete")
def handle_delete_product(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = get_product(db, product_id)
    if not product:
        flash(request, "Product not found.", "danger")
        return RedirectResponse(url="/products", status_code=status.HTTP_303_SEE_OTHER)

    product_name = product.name
    delete_product(db, product_id)
    
    # Audit log
    log_activity(
        db, current_user.id, "delete", "Product", product_id,
        f"Deleted product '{product_name}'"
    )

    flash(request, f"Product '{product_name}' has been deleted.", "success")
    return RedirectResponse(url="/products", status_code=status.HTTP_303_SEE_OTHER)


# ==========================================
# JSON API ENDPOINTS (/api/products)
# ==========================================

@router.get("/api/products", response_model=dict)
def api_list_products(
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user)
):
    products, total = get_products(db, skip=skip, limit=limit, search=search, category=category)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "products": [ProductRead.model_validate(p) for p in products]
    }


@router.get("/api/products/{product_id}", response_model=ProductRead)
def api_get_product(
    product_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user)
):
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductRead.model_validate(product)


@router.post("/api/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def api_create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if SKU is taken
    existing_product = db.query(Product).filter(Product.sku == product_in.sku).first()
    if existing_product:
        raise HTTPException(status_code=400, detail="Product SKU is already in use.")

    new_product = create_product(db, product_in)
    log_activity(db, current_user.id, "create", "Product", new_product.id, f"API created product '{new_product.name}'")
    return ProductRead.model_validate(new_product)


@router.put("/api/products/{product_id}", response_model=ProductRead)
def api_update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if product_in.sku:
        existing = db.query(Product).filter(Product.sku == product_in.sku, Product.id != product_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Product SKU is already in use.")

    updated = update_product(db, product_id, product_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Product not found")
    log_activity(db, current_user.id, "update", "Product", product_id, f"API updated product '{updated.name}'")
    return ProductRead.model_validate(updated)


@router.delete("/api/products/{product_id}", response_model=dict)
def api_delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product_name = product.name
    delete_product(db, product_id)
    log_activity(db, current_user.id, "delete", "Product", product_id, f"API deleted product '{product_name}'")
    return {"status": "ok", "message": f"Product '{product_name}' deleted successfully"}

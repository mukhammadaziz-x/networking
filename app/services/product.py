from typing import List, Tuple, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    category: Optional[str] = None
) -> Tuple[List[Product], int]:
    """Retrieves list of products with optional search, category filtering, and pagination"""
    query = db.query(Product)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_filter),
                Product.sku.ilike(search_filter),
                Product.color.ilike(search_filter),
                Product.category.ilike(search_filter)
            )
        )
        
    if category:
        query = query.filter(Product.category == category)
        
    total = query.count()
    products = query.order_by(Product.name.asc()).offset(skip).limit(limit).all()
    
    return products, total


def get_product(db: Session, product_id: int) -> Optional[Product]:
    """Retrieves a single product by ID"""
    return db.query(Product).filter(Product.id == product_id).first()


def create_product(db: Session, product_in: ProductCreate) -> Product:
    """Creates a new product record"""
    product = Product(
        sku=product_in.sku,
        name=product_in.name,
        category=product_in.category,
        size=product_in.size,
        color=product_in.color,
        price=product_in.price,
        stock_qty=product_in.stock_qty,
        is_active=product_in.is_active
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(
    db: Session,
    product_id: int,
    product_in: ProductUpdate
) -> Optional[Product]:
    """Updates an existing product record"""
    product = get_product(db, product_id)
    if not product:
        return None
        
    update_data = product_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
        
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> bool:
    """Deletes an existing product record"""
    product = get_product(db, product_id)
    if not product:
        return False
        
    db.delete(product)
    db.commit()
    return True

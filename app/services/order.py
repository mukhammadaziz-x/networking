from typing import List, Tuple, Optional
from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.company import Company
from app.models.product import Product
from app.schemas.order import OrderCreate


def get_orders(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    status_filter: Optional[str] = None
) -> Tuple[List[Order], int]:
    """Retrieves a list of orders with pagination and filtering"""
    query = db.query(Order)
    
    if search:
        search_filter = f"%{search}%"
        # Join company to allow searching by company name
        query = query.join(Company).filter(
            or_(
                Order.order_number.ilike(search_filter),
                Company.name.ilike(search_filter)
            )
        )
        
    if status_filter:
        try:
            status_enum = OrderStatus(status_filter)
            query = query.filter(Order.status == status_enum)
        except ValueError:
            pass
            
    total = query.count()
    orders = query.order_by(Order.order_date.desc()).offset(skip).limit(limit).all()
    
    return orders, total


def get_order(db: Session, order_id: int) -> Optional[Order]:
    """Retrieves a single order by ID"""
    return db.query(Order).filter(Order.id == order_id).first()


def create_order(db: Session, order_in: OrderCreate, creator_id: int) -> Order:
    """Creates a new order along with its line items, calculating totals"""
    # Generate sequential unique order number
    count = db.query(Order).count()
    year = datetime.now().year
    order_number = f"ORD-{year}-{(count + 1):04d}"
    
    order = Order(
        company_id=order_in.company_id,
        order_number=order_number,
        status=order_in.status,
        total_amount=0.00,  # Will calculate below
        created_by=creator_id
    )
    db.add(order)
    db.flush()  # Populate order.id
    
    total_amount = 0.00
    for item_in in order_in.items:
        # Verify product existence
        product = db.query(Product).filter(Product.id == item_in.product_id).first()
        if not product:
            raise ValueError(f"Product with ID {item_in.product_id} does not exist.")
            
        line_total = item_in.quantity * item_in.unit_price
        total_amount += line_total
        
        item = OrderItem(
            order_id=order.id,
            product_id=item_in.product_id,
            quantity=item_in.quantity,
            unit_price=item_in.unit_price,
            line_total=line_total
        )
        db.add(item)
        
    order.total_amount = total_amount
    db.commit()
    db.refresh(order)
    return order


def update_order_status(db: Session, order_id: int, status_str: str, user_id: int) -> Order:
    """Updates an order status, enforcing inventory stock adjustments on confirmation/cancellation"""
    order = get_order(db, order_id)
    if not order:
        raise ValueError("Order not found.")
        
    new_status = OrderStatus(status_str)
    old_status = order.status
    
    if old_status == new_status:
        return order
        
    # Transitioning to Confirmed -> Decrement stock
    if new_status == OrderStatus.CONFIRMED:
        # Check stock first
        for item in order.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product.is_active:
                raise ValueError(f"Product '{product.name}' is inactive and cannot be ordered.")
            if product.stock_qty < item.quantity:
                raise ValueError(
                    f"Insufficient stock for '{product.name}' (SKU: {product.sku}). "
                    f"Available: {product.stock_qty}, Requested: {item.quantity}"
                )
                
        # Commit decrement
        for item in order.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            product.stock_qty -= item.quantity
            
    # Transitioning FROM Confirmed (or later) TO Cancelled -> Return stock
    elif new_status == OrderStatus.CANCELLED and old_status in [OrderStatus.CONFIRMED, OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
        for item in order.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            product.stock_qty += item.quantity
            
    order.status = new_status
    db.commit()
    db.refresh(order)
    return order

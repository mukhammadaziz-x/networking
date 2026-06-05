from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.activity import Activity
from app.models.deal import Deal, DealStage
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.company import Company

client = TestClient(app)


def get_auth_client():
    """Helper to log in as admin and return an authenticated TestClient instance"""
    auth_client = TestClient(app)
    auth_client.post(
        "/login",
        data={"email": "admin@clothcrm.local", "password": "Admin123!"},
        follow_redirects=True
    )
    return auth_client


def test_deal_stage_patch_and_activity():
    """Verify that PATCHing a deal stage updates it and logs an activity"""
    auth_client = get_auth_client()
    db = SessionLocal()
    
    try:
        # Fetch the first deal (seeded Globex Initial Order)
        deal = db.query(Deal).filter(Deal.title.like("%Globex%")).first()
        assert deal is not None
        old_stage = deal.stage
        
        # Patch to another stage (e.g. lost)
        response = auth_client.patch(
            f"/api/deals/{deal.id}/stage",
            json={"stage": "lost"}
        )
        assert response.status_code == 200
        assert response.json()["stage"] == "lost"
        
        # Verify DB updated
        db.refresh(deal)
        assert deal.stage == DealStage.LOST
        
        # Verify Activity Logged
        activity = db.query(Activity).filter(
            Activity.entity_type == "Deal",
            Activity.entity_id == deal.id,
            Activity.action == "update"
        ).order_by(Activity.created_at.desc()).first()
        assert activity is not None
        assert "kanban drag-drop" in activity.description.lower()

    finally:
        db.close()


def test_order_creation_and_stock_workflow():
    """Verify order creation unit calculations and stock decrement/increment workflow"""
    auth_client = get_auth_client()
    db = SessionLocal()
    
    try:
        # Robust cleanup of any leftovers from previous failed runs
        db.query(OrderItem).filter(OrderItem.product_id.in_(
            db.query(Product.id).filter(Product.sku == "SHIRT-TEST-INV")
        )).delete(synchronize_session=False)
        db.query(Order).filter(Order.company_id.in_(
            db.query(Company.id).filter(Company.name == "Order Test Corp")
        )).delete(synchronize_session=False)
        db.query(Product).filter(Product.sku == "SHIRT-TEST-INV").delete(synchronize_session=False)
        db.query(Company).filter(Company.name == "Order Test Corp").delete(synchronize_session=False)
        db.commit()

        # Create a company and product for test isolation
        company = Company(name="Order Test Corp", status="active", owner_id=1)
        product = Product(
            sku="SHIRT-TEST-INV",
            name="Inventory Test Shirt",
            category="T-Shirts",
            price=Decimal("20.00"),
            stock_qty=20,
            is_active=True
        )
        db.add_all([company, product])
        db.commit()
        db.refresh(company)
        db.refresh(product)
        
        # 1. Create order as Draft (quantity=5)
        # Form post parameters are product_id (list) and quantity (list)
        order_data = {
            "company_id": company.id,
            "product_id": [product.id],
            "quantity": [5]
        }
        create_response = auth_client.post("/orders/create", data=order_data, follow_redirects=False)
        assert create_response.status_code == 303
        
        # Retrieve the created order from DB
        order = db.query(Order).filter(Order.company_id == company.id).order_by(Order.order_date.desc()).first()
        assert order is not None
        assert order.status == OrderStatus.DRAFT
        assert order.total_amount == Decimal("100.00")  # 5 * 20.00
        
        # Verify stock has not changed yet (still 20)
        db.refresh(product)
        assert product.stock_qty == 20

        # 2. Confirm Order (stock should decrease by 5 -> 15)
        confirm_response = auth_client.post(
            f"/orders/{order.id}/status",
            data={"status": "confirmed"},
            follow_redirects=False
        )
        assert confirm_response.status_code == 303
        
        db.refresh(order)
        db.refresh(product)
        assert order.status == OrderStatus.CONFIRMED
        assert product.stock_qty == 15

        # 3. Create a second order (quantity=25) to test insufficient stock rejection
        insufficient_order_data = {
            "company_id": company.id,
            "product_id": [product.id],
            "quantity": [25]
        }
        auth_client.post("/orders/create", data=insufficient_order_data)
        large_order = db.query(Order).filter(Order.company_id == company.id).order_by(Order.order_date.desc()).first()
        assert large_order.id != order.id
        
        # Try to confirm large order -> should fail (ValueError returned as flash redirect)
        fail_confirm = auth_client.post(
            f"/orders/{large_order.id}/status",
            data={"status": "confirmed"},
            follow_redirects=False
        )
        assert fail_confirm.status_code == 303
        
        # Verify large order status remains DRAFT and product stock is still 15
        db.refresh(large_order)
        db.refresh(product)
        assert large_order.status == OrderStatus.DRAFT
        assert product.stock_qty == 15

        # 4. Cancel the first confirmed order -> stock should return to inventory (15 + 5 -> 20)
        cancel_response = auth_client.post(
            f"/orders/{order.id}/status",
            data={"status": "cancelled"},
            follow_redirects=False
        )
        assert cancel_response.status_code == 303
        
        db.refresh(order)
        db.refresh(product)
        assert order.status == OrderStatus.CANCELLED
        assert product.stock_qty == 20

        # Clean up
        db.delete(large_order)
        db.delete(order)
        db.delete(product)
        db.delete(company)
        db.commit()

    finally:
        db.close()

from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.activity import Activity
from app.models.company import Company
from app.models.contact import Contact
from app.models.product import Product

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


def test_company_crud_and_activity_logging():
    """Verify that creating, updating, and deleting companies works and registers activities"""
    auth_client = get_auth_client()
    db = SessionLocal()
    
    try:
        # 1. Create Company via API
        company_data = {
            "name": "Test Wholesale Corp",
            "industry": "Textiles",
            "phone": "555-987-6543",
            "email": "test@testcorp.com",
            "website": "https://testcorp.com",
            "address": "777 Fabric Lane",
            "city": "Boston",
            "country": "USA",
            "status": "active"
        }
        create_response = auth_client.post("/api/companies", json=company_data)
        assert create_response.status_code == 201
        created_company = create_response.json()
        company_id = created_company["id"]
        assert created_company["name"] == "Test Wholesale Corp"
        assert created_company["status"] == "active"
        
        # Verify Activity Log for Creation
        activity = db.query(Activity).filter(
            Activity.entity_type == "Company",
            Activity.entity_id == company_id,
            Activity.action == "create"
        ).first()
        assert activity is not None
        assert "created company" in activity.description.lower()

        # 2. Read Company
        read_response = auth_client.get(f"/api/companies/{company_id}")
        assert read_response.status_code == 200
        assert read_response.json()["industry"] == "Textiles"

        # 3. Update Company
        update_data = {"name": "Test Wholesale Corp Updated", "status": "inactive"}
        update_response = auth_client.put(f"/api/companies/{company_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Test Wholesale Corp Updated"
        assert update_response.json()["status"] == "inactive"

        # Verify Activity Log for Update
        activity_upd = db.query(Activity).filter(
            Activity.entity_type == "Company",
            Activity.entity_id == company_id,
            Activity.action == "update"
        ).first()
        assert activity_upd is not None

        # 4. Delete Company
        delete_response = auth_client.delete(f"/api/companies/{company_id}")
        assert delete_response.status_code == 200
        assert "deleted successfully" in delete_response.json()["message"]

        # Verify Activity Log for Deletion
        activity_del = db.query(Activity).filter(
            Activity.entity_type == "Company",
            Activity.entity_id == company_id,
            Activity.action == "delete"
        ).first()
        assert activity_del is not None

    finally:
        db.close()


def test_contact_crud():
    """Verify contact creation, read, update, and deletion via API"""
    auth_client = get_auth_client()
    db = SessionLocal()
    
    try:
        # Create a company to link the contact to
        company = Company(name="Contact Parent Corp", status="active", owner_id=1)
        db.add(company)
        db.commit()
        db.refresh(company)
        
        # 1. Create Contact
        contact_data = {
            "first_name": "Sarah",
            "last_name": "Connor",
            "email": "sarah.connor@parent.com",
            "phone": "555-888-9999",
            "position": "Procurement Lead",
            "company_id": company.id
        }
        create_response = auth_client.post("/api/contacts", json=contact_data)
        assert create_response.status_code == 201
        created_contact = create_response.json()
        contact_id = created_contact["id"]
        assert created_contact["first_name"] == "Sarah"
        
        # 2. Update Contact
        update_data = {"position": "Chief Buyer"}
        update_response = auth_client.put(f"/api/contacts/{contact_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["position"] == "Chief Buyer"

        # 3. Delete Contact
        delete_response = auth_client.delete(f"/api/contacts/{contact_id}")
        assert delete_response.status_code == 200
        
        # Clean up company
        db.delete(company)
        db.commit()
        
    finally:
        db.close()


def test_product_crud():
    """Verify product catalog CRUD operations and low stock verification details"""
    auth_client = get_auth_client()
    
    # 1. Create Product
    product_data = {
        "sku": "TSHIRT-TEST-S",
        "name": "Test Small T-Shirt",
        "category": "T-Shirts",
        "size": "S",
        "color": "Red",
        "price": 12.50,
        "stock_qty": 5,  # Low stock
        "is_active": True
    }
    create_response = auth_client.post("/api/products", json=product_data)
    assert create_response.status_code == 201
    created_product = create_response.json()
    product_id = created_product["id"]
    assert created_product["sku"] == "TSHIRT-TEST-S"
    assert created_product["stock_qty"] == 5

    # 2. Read Product and verify low stock highlight on index web page
    web_list_response = auth_client.get("/products")
    assert web_list_response.status_code == 200
    assert "LOW" in web_list_response.text  # Verify HTML warning marker exists

    # 3. Update Product
    update_data = {"stock_qty": 50}  # No longer low stock
    update_response = auth_client.put(f"/api/products/{product_id}", json=update_data)
    assert update_response.status_code == 200
    assert update_response.json()["stock_qty"] == 50

    # 4. Delete Product
    delete_response = auth_client.delete(f"/api/products/{product_id}")
    assert delete_response.status_code == 200

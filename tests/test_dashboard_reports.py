from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.company import Company
from app.models.deal import Deal, DealStage
from app.models.order import Order, OrderStatus


def get_auth_client():
    """Helper to return an authenticated TestClient instance"""
    client = TestClient(app)
    client.post(
        "/login",
        data={"email": "admin@clothcrm.local", "password": "Admin123!"},
        follow_redirects=True
    )
    return client


def test_dashboard_unauthenticated_redirect():
    """Verify that unauthenticated GET / redirects to login"""
    client = TestClient(app)
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_dashboard_authenticated_success():
    """Verify that authenticated GET / renders dashboard with metrics"""
    client = get_auth_client()
    response = client.get("/")
    assert response.status_code == 200
    assert "Dashboard" in response.text
    assert "Total Accounts" in response.text
    assert "Recent Activity" in response.text


def test_api_dashboard_data():
    """Verify that GET /api/dashboard/data returns correct JSON structure"""
    client = get_auth_client()
    response = client.get("/api/dashboard/data")
    assert response.status_code == 200
    
    data = response.json()
    assert "kpis" in data
    assert "charts" in data
    
    # Check KPI fields
    kpis = data["kpis"]
    assert "total_companies" in kpis
    assert "open_deals_value" in kpis
    assert "revenue_month_value" in kpis
    assert "open_tasks_count" in kpis
    
    # Check Chart fields
    charts = data["charts"]
    assert "sales_revenue" in charts
    assert "deals_by_stage" in charts
    assert "orders_by_status" in charts
    assert "top_products" in charts


def test_reports_page_and_filtering():
    """Verify that GET /reports is accessible and respects date-range filtering"""
    client = get_auth_client()
    db = SessionLocal()
    
    try:
        # Create a company and order within range
        company = Company(name="Report Test Corp", status="active", owner_id=1)
        db.add(company)
        db.commit()
        db.refresh(company)
        
        order = Order(
            company_id=company.id,
            order_number="ORD-REP-TEST-99",
            status=OrderStatus.CONFIRMED,
            total_amount=500.00,
            created_by=1
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        
        # 1. Fetch reports with date range covering the order
        start_str = (date.today() - timedelta(days=2)).strftime('%Y-%m-%d')
        end_str = (date.today() + timedelta(days=2)).strftime('%Y-%m-%d')
        response = client.get(f"/reports?start_date={start_str}&end_date={end_str}")
        assert response.status_code == 200
        assert "Sales Performance and Pipeline Reporting" in response.text
        assert "ORD-REP-TEST-99" in response.text
        assert "Report Test Corp" in response.text
        
        # 2. Fetch reports with date range excluding the order (e.g. far future)
        start_future = (date.today() + timedelta(days=10)).strftime('%Y-%m-%d')
        end_future = (date.today() + timedelta(days=15)).strftime('%Y-%m-%d')
        exclude_response = client.get(f"/reports?start_date={start_future}&end_date={end_future}")
        assert exclude_response.status_code == 200
        assert "ORD-REP-TEST-99" not in exclude_response.text
        
        # Clean up
        db.delete(order)
        db.delete(company)
        db.commit()
        
    finally:
        db.close()

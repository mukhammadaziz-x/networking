from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.company import Company
from app.models.contact import Contact
from app.models.product import Product
from app.models.deal import Deal
from app.models.order import Order


def test_db_seeding_integrity():
    """Verify that seeded data has correct relationships and counts"""
    db: Session = SessionLocal()
    try:
        # Check users count
        users = db.query(User).all()
        assert len(users) >= 3
        admin = db.query(User).filter(User.email == "admin@clothcrm.local").first()
        assert admin is not None
        assert admin.role == UserRole.ADMIN

        # Check companies count and relationship
        companies = db.query(Company).all()
        assert len(companies) >= 3
        acme = db.query(Company).filter(Company.name == "Acme Corp").first()
        assert acme is not None
        assert acme.owner.name == "Bob Sales"

        # Check contacts and backpopulates
        contacts = db.query(Contact).all()
        assert len(contacts) >= 3
        john = db.query(Contact).filter(Contact.first_name == "John").first()
        assert john is not None
        assert john.company.name == "Acme Corp"
        assert john.owner.name == "Bob Sales"

        # Check products
        products = db.query(Product).all()
        assert len(products) >= 3
        tshirt = db.query(Product).filter(Product.sku == "TSHIRT-ORG-M").first()
        assert tshirt is not None
        assert tshirt.price == 15.00

        # Check deals
        deals = db.query(Deal).all()
        assert len(deals) >= 3
        acme_deal = db.query(Deal).filter(Deal.title.like("%Acme%")).first()
        assert acme_deal is not None
        assert acme_deal.company.name == "Acme Corp"
        assert acme_deal.contact.first_name == "John"

        # Check order and items
        orders = db.query(Order).all()
        assert len(orders) >= 1
        order = orders[0]
        assert order.order_number == "ORD-2026-0001"
        assert len(order.items) == 1
        assert order.items[0].product.sku == "HOODIE-BLK-L"
        assert order.items[0].quantity == 100
        assert order.total_amount == 4500.00

    finally:
        db.close()

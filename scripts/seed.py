import sys
import os
from datetime import datetime, date, timedelta
from decimal import Decimal

# Add root folder to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.company import Company, CompanyStatus
from app.models.contact import Contact
from app.models.product import Product
from app.models.deal import Deal, DealStage
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.activity import Activity
import bcrypt


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def main():
    print("Starting database seeding...")
    db = SessionLocal()
    try:
        # Clear existing data in reverse order of foreign keys
        print("Clearing existing data...")
        db.query(OrderItem).delete()
        db.query(Order).delete()
        db.query(Task).delete()
        db.query(Deal).delete()
        db.query(Contact).delete()
        db.query(Company).delete()
        db.query(Activity).delete()
        db.query(User).delete()
        db.query(Product).delete()
        db.commit()

        # 1. Create Users
        print("Creating users...")
        admin = User(
            name="Administrator",
            email="admin@clothcrm.local",
            password_hash=get_password_hash("Admin123!"),
            role=UserRole.ADMIN,
            is_active=True
        )
        manager = User(
            name="Alice Manager",
            email="manager@clothcrm.local",
            password_hash=get_password_hash("Manager123!"),
            role=UserRole.MANAGER,
            is_active=True
        )
        sales_rep = User(
            name="Bob Sales",
            email="sales@clothcrm.local",
            password_hash=get_password_hash("Sales123!"),
            role=UserRole.SALES,
            is_active=True
        )
        
        db.add_all([admin, manager, sales_rep])
        db.flush()  # to populate IDs

        # 2. Create Products
        print("Creating products...")
        p1 = Product(
            sku="TSHIRT-ORG-M",
            name="Organic Cotton T-Shirt",
            category="T-Shirts",
            size="M",
            color="Green",
            price=Decimal("15.00"),
            stock_qty=150,
            is_active=True
        )
        p2 = Product(
            sku="HOODIE-BLK-L",
            name="Classic Black Hoodie",
            category="Hoodies",
            size="L",
            color="Black",
            price=Decimal("45.00"),
            stock_qty=80,
            is_active=True
        )
        p3 = Product(
            sku="JEANS-BLU-32",
            name="Slim Fit Blue Jeans",
            category="Pants",
            size="32",
            color="Blue",
            price=Decimal("55.00"),
            stock_qty=100,
            is_active=True
        )
        db.add_all([p1, p2, p3])
        db.flush()

        # 3. Create Companies
        print("Creating companies...")
        c1 = Company(
            name="Acme Corp",
            industry="Retail",
            phone="123-456-7890",
            email="info@acme.com",
            website="https://acme.com",
            address="123 Industrial Way",
            city="Metropolis",
            country="USA",
            status=CompanyStatus.PROSPECT,
            owner_id=sales_rep.id
        )
        c2 = Company(
            name="Globex Corporation",
            industry="E-commerce",
            phone="555-0199",
            email="contact@globex.com",
            website="https://globex.com",
            address="456 Power Blvd",
            city="Cypress Creek",
            country="USA",
            status=CompanyStatus.ACTIVE,
            owner_id=sales_rep.id
        )
        c3 = Company(
            name="Initech",
            industry="Apparel",
            phone="888-234-5678",
            email="purchasing@initech.com",
            website="https://initech.com",
            address="4120 Freemont Ave",
            city="Austin",
            country="USA",
            status=CompanyStatus.ACTIVE,
            owner_id=manager.id
        )
        db.add_all([c1, c2, c3])
        db.flush()

        # 4. Create Contacts
        print("Creating contacts...")
        contact1 = Contact(
            first_name="John",
            last_name="Doe",
            email="john.doe@acme.com",
            phone="123-456-0001",
            position="Purchasing Manager",
            company_id=c1.id,
            owner_id=sales_rep.id
        )
        contact2 = Contact(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@globex.com",
            phone="555-0199",
            position="VP of Procurement",
            company_id=c2.id,
            owner_id=sales_rep.id
        )
        contact3 = Contact(
            first_name="Peter",
            last_name="Gibbons",
            email="peter@initech.com",
            phone="888-234-1111",
            position="Lead Buyer",
            company_id=c3.id,
            owner_id=manager.id
        )
        db.add_all([contact1, contact2, contact3])
        db.flush()

        # 5. Create Deals
        print("Creating deals...")
        deal1 = Deal(
            title="Acme Corp Bulk T-Shirts Opportunity",
            company_id=c1.id,
            contact_id=contact1.id,
            owner_id=sales_rep.id,
            stage=DealStage.PROPOSAL,
            amount=Decimal("1500.00"),
            expected_close_date=date.today() + timedelta(days=30)
        )
        deal2 = Deal(
            title="Globex Initial Order",
            company_id=c2.id,
            contact_id=contact2.id,
            owner_id=sales_rep.id,
            stage=DealStage.WON,
            amount=Decimal("4500.00"),
            expected_close_date=date.today() - timedelta(days=2)
        )
        deal3 = Deal(
            title="Initech Fall Denim Collection",
            company_id=c3.id,
            contact_id=contact3.id,
            owner_id=manager.id,
            stage=DealStage.QUALIFIED,
            amount=Decimal("5500.00"),
            expected_close_date=date.today() + timedelta(days=60)
        )
        db.add_all([deal1, deal2, deal3])
        db.flush()

        # 6. Create Orders and Items
        print("Creating orders...")
        order = Order(
            company_id=c2.id,
            order_number="ORD-2026-0001",
            status=OrderStatus.CONFIRMED,
            total_amount=Decimal("4500.00"),
            order_date=datetime.now() - timedelta(days=2),
            created_by=sales_rep.id
        )
        db.add(order)
        db.flush()

        item = OrderItem(
            order_id=order.id,
            product_id=p2.id,
            quantity=100,
            unit_price=Decimal("45.00"),
            line_total=Decimal("4500.00")
        )
        db.add(item)

        # 7. Create Tasks
        print("Creating tasks...")
        t1 = Task(
            title="Follow up on Acme Proposal",
            description="Send email checking on status of bulk T-shirt quote.",
            due_date=date.today() + timedelta(days=3),
            status=TaskStatus.OPEN,
            priority=TaskPriority.HIGH,
            assignee_id=sales_rep.id,
            related_company_id=c1.id,
            related_deal_id=deal1.id
        )
        t2 = Task(
            title="Coordinate Globex Delivery",
            description="Check inventory for 100 hoodies and notify shipping manager.",
            due_date=date.today() + timedelta(days=1),
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.MEDIUM,
            assignee_id=sales_rep.id,
            related_company_id=c2.id
        )
        db.add_all([t1, t2])

        # 8. Create Activity Logs
        print("Creating activity log entries...")
        act1 = Activity(
            user_id=sales_rep.id,
            action="create",
            entity_type="Company",
            entity_id=c1.id,
            description="Created Acme Corp as a prospect customer.",
            created_at=datetime.now() - timedelta(days=5)
        )
        act2 = Activity(
            user_id=sales_rep.id,
            action="update",
            entity_type="Deal",
            entity_id=deal2.id,
            description="Updated Deal stage to WON.",
            created_at=datetime.now() - timedelta(days=2)
        )
        db.add_all([act1, act2])

        db.commit()
        print("Database seeding completed successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

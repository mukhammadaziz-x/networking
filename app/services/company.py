from typing import List, Tuple, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.company import Company, CompanyStatus
from app.schemas.company import CompanyCreate, CompanyUpdate


def get_companies(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    status: Optional[str] = None
) -> Tuple[List[Company], int]:
    """Retrieves list of companies with optional search, filtering, and pagination"""
    query = db.query(Company)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Company.name.ilike(search_filter),
                Company.industry.ilike(search_filter),
                Company.city.ilike(search_filter),
                Company.country.ilike(search_filter)
            )
        )
        
    if status:
        try:
            status_enum = CompanyStatus(status)
            query = query.filter(Company.status == status_enum)
        except ValueError:
            pass  # Ignore invalid statuses
            
    total = query.count()
    companies = query.order_by(Company.name.asc()).offset(skip).limit(limit).all()
    
    return companies, total


def get_company(db: Session, company_id: int) -> Optional[Company]:
    """Retrieves a single company by ID"""
    return db.query(Company).filter(Company.id == company_id).first()


def create_company(db: Session, company_in: CompanyCreate, owner_id: int) -> Company:
    """Creates a new company record"""
    company = Company(
        name=company_in.name,
        industry=company_in.industry,
        phone=company_in.phone,
        email=company_in.email,
        website=company_in.website,
        address=company_in.address,
        city=company_in.city,
        country=company_in.country,
        status=company_in.status,
        owner_id=owner_id
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def update_company(
    db: Session,
    company_id: int,
    company_in: CompanyUpdate
) -> Optional[Company]:
    """Updates an existing company record"""
    company = get_company(db, company_id)
    if not company:
        return None
        
    update_data = company_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
        
    db.commit()
    db.refresh(company)
    return company


def delete_company(db: Session, company_id: int) -> bool:
    """Deletes an existing company record"""
    company = get_company(db, company_id)
    if not company:
        return False
        
    db.delete(company)
    db.commit()
    return True

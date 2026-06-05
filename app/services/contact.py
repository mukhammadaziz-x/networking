from typing import List, Tuple, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.contact import Contact
from app.models.company import Company
from app.schemas.contact import ContactCreate, ContactUpdate


def get_contacts(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None
) -> Tuple[List[Contact], int]:
    """Retrieves list of contacts with search and pagination"""
    query = db.query(Contact)
    
    if search:
        search_filter = f"%{search}%"
        # Join company to allow searching by company name as well
        query = query.join(Company).filter(
            or_(
                Contact.first_name.ilike(search_filter),
                Contact.last_name.ilike(search_filter),
                Contact.email.ilike(search_filter),
                Contact.position.ilike(search_filter),
                Company.name.ilike(search_filter)
            )
        )
        
    total = query.count()
    contacts = query.order_by(Contact.first_name.asc(), Contact.last_name.asc()).offset(skip).limit(limit).all()
    
    return contacts, total


def get_contact(db: Session, contact_id: int) -> Optional[Contact]:
    """Retrieves a single contact by ID"""
    return db.query(Contact).filter(Contact.id == contact_id).first()


def create_contact(db: Session, contact_in: ContactCreate, owner_id: int) -> Contact:
    """Creates a new contact record"""
    contact = Contact(
        first_name=contact_in.first_name,
        last_name=contact_in.last_name,
        email=contact_in.email,
        phone=contact_in.phone,
        position=contact_in.position,
        company_id=contact_in.company_id,
        owner_id=owner_id
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def update_contact(
    db: Session,
    contact_id: int,
    contact_in: ContactUpdate
) -> Optional[Contact]:
    """Updates an existing contact record"""
    contact = get_contact(db, contact_id)
    if not contact:
        return None
        
    update_data = contact_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)
        
    db.commit()
    db.refresh(contact)
    return contact


def delete_contact(db: Session, contact_id: int) -> bool:
    """Deletes an existing contact record"""
    contact = get_contact(db, contact_id)
    if not contact:
        return False
        
    db.delete(contact)
    db.commit()
    return True

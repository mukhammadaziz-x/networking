from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.deal import Deal, DealStage
from app.schemas.deal import DealCreate, DealUpdate


def get_deals(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    stage: Optional[str] = None
) -> List[Deal]:
    """Retrieves list of deals, optionally filtered by stage"""
    query = db.query(Deal)
    if stage:
        try:
            stage_enum = DealStage(stage)
            query = query.filter(Deal.stage == stage_enum)
        except ValueError:
            pass
    return query.order_by(Deal.created_at.desc()).offset(skip).limit(limit).all()


def get_deal(db: Session, deal_id: int) -> Optional[Deal]:
    """Retrieves a single deal by ID"""
    return db.query(Deal).filter(Deal.id == deal_id).first()


def create_deal(db: Session, deal_in: DealCreate, owner_id: int) -> Deal:
    """Creates a new deal record"""
    deal = Deal(
        title=deal_in.title,
        company_id=deal_in.company_id,
        contact_id=deal_in.contact_id,
        owner_id=owner_id,
        stage=deal_in.stage,
        amount=deal_in.amount,
        expected_close_date=deal_in.expected_close_date
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return deal


def update_deal(db: Session, deal_id: int, deal_in: DealUpdate) -> Optional[Deal]:
    """Updates an existing deal record"""
    deal = get_deal(db, deal_id)
    if not deal:
        return None
        
    update_data = deal_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(deal, field, value)
        
    db.commit()
    db.refresh(deal)
    return deal


def update_deal_stage(db: Session, deal_id: int, stage_str: str) -> Optional[Deal]:
    """Updates only the stage of a deal (helper for Kanban drops)"""
    deal = get_deal(db, deal_id)
    if not deal:
        return None
    
    stage_enum = DealStage(stage_str)
    deal.stage = stage_enum
    db.commit()
    db.refresh(deal)
    return deal


def delete_deal(db: Session, deal_id: int) -> bool:
    """Deletes a deal record"""
    deal = get_deal(db, deal_id)
    if not deal:
        return False
        
    db.delete(deal)
    db.commit()
    return True

from fastapi import APIRouter, HTTPException, Depends, Query
from utils.util import get_db
from config.database import Session
from datetime import datetime
from utils.pydantic_model import GuardCreate,GuardStatus,GuardResponse,GuardUpdate
from models.guard import Guard
from typing import List, Optional

guard= APIRouter()

@guard.post("/guards/", response_model=GuardResponse)
async def create_guard(guard: GuardCreate, db: Session = Depends(get_db)):
    # Check if contact number already exists
    existing_guard = db.query(Guard).filter(Guard.contact_number == guard.contact_number).first()
    if existing_guard:
        raise HTTPException(status_code=400, detail="Contact number already registered")
    
    db_guard = Guard(**guard.dict())
    db.add(db_guard)
    db.commit()
    db.refresh(db_guard)
    return db_guard

@guard.get("/guards/", response_model=List[GuardResponse])
async def get_guards(
    skip: int = 0,
    limit: int = 100,
    status: Optional[GuardStatus] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Guard)
    
    if status:
        query = query.filter(Guard.status == status)
    
    if search:
        query = query.filter(
            (Guard.name.ilike(f"%{search}%")) |
            (Guard.contact_number.ilike(f"%{search}%"))
        )
    
    guards = query.offset(skip).limit(limit).all()
    return guards

@guard.get("/guards/{guard_id}", response_model=GuardResponse)
async def get_guard(guard_id: int, db: Session = Depends(get_db)):
    guard = db.query(Guard).filter(Guard.id == guard_id).first()
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    return guard

@guard.get("/guards/by-contact/{contact_number}", response_model=GuardResponse)
async def get_guard_by_contact(contact_number: str, db: Session = Depends(get_db)):
    guard = db.query(Guard).filter(Guard.contact_number == contact_number).first()
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    return guard

@guard.put("/guards/{guard_id}", response_model=GuardResponse)
async def update_guard(guard_id: int, guard_update: GuardUpdate, db: Session = Depends(get_db)):
    guard = db.query(Guard).filter(Guard.id == guard_id).first()
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    
    # Check contact number uniqueness if being updated
    if guard_update.contact_number and guard_update.contact_number != guard.contact_number:
        existing = db.query(Guard).filter(Guard.contact_number == guard_update.contact_number).first()
        if existing:
            raise HTTPException(status_code=400, detail="Contact number already exists")
    
    for field, value in guard_update.dict(exclude_unset=True).items():
        setattr(guard, field, value)
    
    guard.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(guard)
    return guard

@guard.delete("/guards/{guard_id}")
async def delete_guard(guard_id: int, db: Session = Depends(get_db)):
    guard = db.query(Guard).filter(Guard.id == guard_id).first()
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    
    db.delete(guard)
    db.commit()
    return {"message": "Guard deleted successfully"}

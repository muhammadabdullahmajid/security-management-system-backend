from fastapi import APIRouter, HTTPException, Depends, Query
from utils.util import get_db
from sqlalchemy.orm import  Session 
from datetime import datetime
from utils.pydantic_model import GuardCreate,GuardStatus,GuardResponse,GuardUpdate
from models.guard import Guard
from models.dutyassignment import DutyAssignment
from typing import List, Optional

guard= APIRouter()

@guard.post("/", response_model=GuardResponse)
async def create_guard(guard: GuardCreate, db: Session = Depends(get_db)):
    try:
    # Check if contact number already exists
        existing_guard = db.query(Guard).filter(Guard.contact_number == guard.contact_number).first()
        if existing_guard:
            raise HTTPException(status_code=400, detail="Contact number already registered")
        
        db_guard = Guard(**guard.dict())
        db.add(db_guard)
        db.commit()
        db.refresh(db_guard)
        return db_guard
    except Exception as e:
        print(f"Error creating guard: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@guard.get("/", response_model=List[GuardResponse])
async def get_guards(
    skip: int = 0,
    limit: int = 100,
    status: Optional[GuardStatus] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
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
    except Exception as e:
        print(f"Error fetching guards: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@guard.get("/{guard_id}", response_model=GuardResponse)
async def get_guard(guard_id: int, db: Session = Depends(get_db)):
    try:
        guard = db.query(Guard).filter(Guard.id == guard_id).first()
        if not guard:
            raise HTTPException(status_code=404, detail="Guard not found")
        return guard
    except Exception as e:
        print(f"Error fetching guards by id: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@guard.get("/by-contact/{contact_number}", response_model=GuardResponse)
async def get_guard_by_contact(contact_number: str, db: Session = Depends(get_db)):
    try:
        guard = db.query(Guard).filter(Guard.contact_number == contact_number).first()
        if not guard:
            raise HTTPException(status_code=404, detail="Guard not found")
        return guard
    except Exception as e:
        print(f"Error fetching guards by contact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@guard.put("/{guard_id}", response_model=GuardResponse)
async def update_guard(guard_id: int, guard_update: GuardUpdate, db: Session = Depends(get_db)):
    try:
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
    except Exception as e:
        print(f"Error updating guards by id: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@guard.delete("/{guard_id}")
async def delete_guard(guard_id: int, db: Session = Depends(get_db)):
    try:
        # Check if guard exists
        guard_obj = db.query(Guard).filter(Guard.id == guard_id).first()
        if not guard_obj:
            raise HTTPException(status_code=404, detail="Guard not found")
        
        guard_contact = guard_obj.contact_number

        # Check if guard has active assignments
        assignments = db.query(DutyAssignment).filter(
            DutyAssignment.guard_contact_number == guard_contact
        ).first()
        if assignments:
            # Don't catch this in the except, let FastAPI handle it
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete guard with active duty assignments"
            )

        # Delete guard
        db.delete(guard_obj)
        db.commit()
        return {"message": "Guard deleted successfully"}
    
    except HTTPException:
        # Re-raise HTTPException so FastAPI sends correct status code
        raise
    except Exception as e:
        print(f"Error deleting guard by id: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

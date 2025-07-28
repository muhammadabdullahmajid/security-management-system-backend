from fastapi import APIRouter, HTTPException, Depends, Query
from utils.util import get_db
from config.database import Session
from datetime import datetime
from utils.pydantic_model import DutyAssignmentCreate,DutyAssignmentResponse,DutyAssignmentUpdate,DutyStatus
from models.guard import Guard
from models.client import Client
from typing import List, Optional
from models.dutyassignment import DutyAssignment

duty_assignment= APIRouter()

@duty_assignment.post("/", response_model=DutyAssignmentResponse)
async def create_duty_assignment(assignment: DutyAssignmentCreate, db: Session = Depends(get_db)):
    # Check if guard exists
    guard = db.query(Guard).filter(Guard.id == assignment.guard_id).first()
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    
    # Check if client exists
    client = db.query(Client).filter(Client.id == assignment.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # End any existing active assignments for this guard
    existing_assignments = db.query(DutyAssignment).filter(
        DutyAssignment.guard_id == assignment.guard_id,
        DutyAssignment.is_active == True
    ).all()
    
    for existing in existing_assignments:
        existing.is_active = False
        existing.end_date = datetime.utcnow()
    
    db_assignment = DutyAssignment(**assignment.dict())
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment

@duty_assignment.get("/", response_model=List[DutyAssignmentResponse])
async def get_duty_assignments(
    skip: int = 0,
    limit: int = 100,
    guard_id: Optional[int] = None,
    client_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    duty_status: Optional[DutyStatus] = None,
    db: Session = Depends(get_db)
):
    query = db.query(DutyAssignment)
    
    if guard_id:
        query = query.filter(DutyAssignment.guard_id == guard_id)
    if client_id:
        query = query.filter(DutyAssignment.client_id == client_id)
    if is_active is not None:
        query = query.filter(DutyAssignment.is_active == is_active)
    if duty_status:
        query = query.filter(DutyAssignment.duty_status == duty_status)
    
    assignments = query.offset(skip).limit(limit).all()
    return assignments

@duty_assignment.get("/{assignment_id}", response_model=DutyAssignmentResponse)
async def get_duty_assignment(assignment_id: int, db: Session = Depends(get_db)):
    assignment = db.query(DutyAssignment).filter(DutyAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment

@duty_assignment.put("/{assignment_id}", response_model=DutyAssignmentResponse)
async def update_duty_assignment(
    assignment_id: int,
    assignment_update: DutyAssignmentUpdate,
    db: Session = Depends(get_db)
):
    assignment = db.query(DutyAssignment).filter(DutyAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # If reassigning to a different client, verify client exists
    if assignment_update.client_id and assignment_update.client_id != assignment.client_id:
        client = db.query(Client).filter(Client.id == assignment_update.client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="New client not found")
    
    for field, value in assignment_update.dict(exclude_unset=True).items():
        setattr(assignment, field, value)
    
    assignment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(assignment)
    return assignment

@duty_assignment.post("/reassign/{guard_id}")
async def reassign_guard(
    guard_id: int,
    new_client_id: int,
    db: Session = Depends(get_db)
):
    # Verify guard exists
    guard = db.query(Guard).filter(Guard.id == guard_id).first()
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    
    # Verify client exists
    client = db.query(Client).filter(Client.id == new_client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # End current assignment
    current_assignment = db.query(DutyAssignment).filter(
        DutyAssignment.guard_id == guard_id,
        DutyAssignment.is_active == True
    ).first()
    
    if current_assignment:
        current_assignment.is_active = False
        current_assignment.end_date = datetime.utcnow()
    
    # Create new assignment
    new_assignment = DutyAssignment(
        guard_id=guard_id,
        client_id=new_client_id,
        start_date=datetime.utcnow(),
        duty_status=DutyStatus.ON_DUTY,
        is_active=True
    )
    
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)
    
    return {"message": "Guard reassigned successfully", "assignment": new_assignment}
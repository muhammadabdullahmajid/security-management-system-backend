from fastapi import APIRouter, HTTPException, Depends, Query
from utils.util import get_db
from sqlalchemy.orm import  Session 
from datetime import datetime
from utils.pydantic_model import DutyAssignmentCreate,DutyAssignmentResponse,DutyAssignmentUpdate,DutyStatus,DutyAssignmentReassign
from models.guard import Guard
from models.client import Client
from typing import List, Optional
from models.dutyassignment import DutyAssignment

dutyassignment= APIRouter()

@dutyassignment.post("/", response_model=DutyAssignmentResponse)
async def create_duty_assignment(assignment: DutyAssignmentCreate, db: Session = Depends(get_db)):
    try:
        guard = db.query(Guard).filter(Guard.contact_number == assignment.guard_contact_number).first()
        if not guard:
            raise HTTPException(status_code=404, detail="Guard not found")

        client = db.query(Client).filter(Client.contact_number == assignment.client_contact_number).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        # End any existing active assignments for this guard
        existing_assignments = db.query(DutyAssignment).filter(
            DutyAssignment.guard_contact_number == assignment.guard_contact_number,
            DutyAssignment.is_active == True
        ).all()

        for existing in existing_assignments:
            existing.is_active = False
            existing.end_date = datetime.utcnow()

        # Inject guard name into the assignment
        assignment_data = assignment.dict()
        assignment_data["name"] = guard.name  # 👈 Inject name from Guard table

        db_assignment = DutyAssignment(**assignment_data)
        db.add(db_assignment)
        db.commit()
        db.refresh(db_assignment)
        return db_assignment

    except Exception as e:
        print(f"Error in duty Assignment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@dutyassignment.get("/", response_model=List[DutyAssignmentResponse])
async def get_duty_assignments(
    skip: int = 0,
    limit: int = 100,
    guard_contact_number: Optional[int] = None,
    client_contact_number: Optional[int] = None,
    is_active: Optional[bool] = None,
    duty_status: Optional[DutyStatus] = None,
    db: Session = Depends(get_db)
):
    try:
        query = db.query(DutyAssignment)
        
        if guard_contact_number:
            query = query.filter(DutyAssignment.guard_contact_number == guard_contact_number)
        if client_contact_number:
            query = query.filter(DutyAssignment.client_contact_number == client_contact_number)
        if is_active is not None:
            query = query.filter(DutyAssignment.is_active == is_active)
        if duty_status:
            query = query.filter(DutyAssignment.duty_status == duty_status)
        
        assignments = query.offset(skip).limit(limit).all()
        return assignments
    except Exception as e:
        print(f"Error feaching duty Assignment: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 

@dutyassignment.get("/{assignment_id}", response_model=DutyAssignmentResponse)
async def get_duty_assignment(assignment_id: int, db: Session = Depends(get_db)):
    try:
        assignment = db.query(DutyAssignment).filter(DutyAssignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        return assignment
    except Exception as e:
        print(f"Error fetching duty assignment by ID: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@dutyassignment.put("/{assignment_id}", response_model=DutyAssignmentResponse)
async def update_duty_assignment(
    assignment_id: int,
    assignment_update: DutyAssignmentUpdate,
    db: Session = Depends(get_db)
):
    try:
        assignment = db.query(DutyAssignment).filter(DutyAssignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # If reassigning to a different client, verify client exists
        if assignment_update.client_contact_number and assignment_update.client_contact_number != assignment.client_contact_number:
            client = db.query(Client).filter(Client.contact_number == assignment_update.client_contact_number).first()
            if not client:
                raise HTTPException(status_code=404, detail="New client not found")
        
        for field, value in assignment_update.dict(exclude_unset=True).items():
            setattr(assignment, field, value)
        
        assignment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(assignment)
        return assignment
    except Exception as e:
        print(f"Error updating duty assignment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@dutyassignment.post("/reassign/{guard_contact_number}")
async def reassign_guard(
    duty_assignment: DutyAssignmentReassign,
    db: Session = Depends(get_db)
):
    try:
    # Verify guard exists
        guard = db.query(Guard).filter(Guard.contact_number == duty_assignment.guard_contact_number).first()
        if not guard:
            raise HTTPException(status_code=404, detail="Guard not found")
        
        # Verify client exists
        client = db.query(Client).filter(Client.contact_number == duty_assignment.new_client_contact_number).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # End current assignment
        current_assignment = db.query(DutyAssignment).filter(
            DutyAssignment.guard_contact_number == duty_assignment.guard_contact_number,
            DutyAssignment.is_active == True
        ).first()
        
        if current_assignment:
            current_assignment.is_active = False
            current_assignment.end_date = datetime.utcnow()
        
        # Create new assignment
        new_assignment = DutyAssignment(
            guard_contact_number=duty_assignment.guard_contact_number,
            client_contact_number=duty_assignment.new_client_contact_number,
            company_name=duty_assignment.company_name,
            start_date=datetime.utcnow(),
            duty_status=DutyStatus.ON_DUTY,
            is_active=True
        )
        
        db.add(new_assignment)
        db.commit()
        db.refresh(new_assignment)
        
        return {"message": "Guard reassigned successfully", "assignment": new_assignment}
    except Exception as e:
        print(f"Error reassigning guard: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

@dutyassignment.delete("/{assignment_id}", status_code=204)
async def delete_duty_assignment(assignment_id: int, db: Session = Depends(get_db)):
    """
    Delete a duty assignment by its ID.
    """
    try:
        assignment = db.query(DutyAssignment).filter(DutyAssignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        db.delete(assignment)
        db.commit()
        return None  # 204 No Content
    except Exception as e:
        print(f"Error deleting duty assignment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

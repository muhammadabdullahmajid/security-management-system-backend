from fastapi import APIRouter, HTTPException, Depends, Query
from utils.util import get_db
from sqlalchemy.orm import  Session 
from datetime import datetime
from utils.pydantic_model import SalaryRecordCreate,SalaryRecordResponse,SalaryRecordUpdate
from models.dutyassignment import DutyAssignment
from models.client import Client
from models.guard import Guard, GuardStatus
from typing import Optional

search = APIRouter()

@search.get("/guards")
async def search_guards_advanced(
    name: Optional[str] = None,
    contact: Optional[str] = None,
    status: Optional[GuardStatus] = None,
    client_name: Optional[str] = None,
    available_only: Optional[bool] = False,
    db: Session = Depends(get_db)
):
    query = db.query(Guard)
    
    if name:
        query = query.filter(Guard.name.ilike(f"%{name}%"))
    if contact:
        query = query.filter(Guard.contact_number.ilike(f"%{contact}%"))
    if status:
        query = query.filter(Guard.status == status)
    
    if client_name:
        query = query.join(DutyAssignment).join(Client).filter(
            Client.name.ilike(f"%{client_name}%"),
            DutyAssignment.is_active == True
        )
    
    if available_only:
        # Guards without active assignments
        query = query.filter(
            ~Guard.duty_assignments.any(DutyAssignment.is_active == True)
        )
    
    guards = query.all()
    
    # Enhance with current assignment info
    result = []
    for guard in guards:
        current_assignment = db.query(DutyAssignment).filter(
            DutyAssignment.guard_id == guard.id,
            DutyAssignment.is_active == True
        ).first()
        
        guard_info = {
            "id": guard.id,
            "name": guard.name,
            "contact_number": guard.contact_number,
            "status": guard.status,
            "current_assignment": None
        }
        
        if current_assignment:
            guard_info["current_assignment"] = {
                "client_name": current_assignment.client.name,
                "duty_status": current_assignment.duty_status,
                "start_date": current_assignment.start_date
            }
        
        result.append(guard_info)
    
    return result
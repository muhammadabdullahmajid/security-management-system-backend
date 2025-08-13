from fastapi import APIRouter, HTTPException, Depends, Query
from utils.util import get_db
from sqlalchemy.orm import  Session 
from datetime import datetime
from utils.pydantic_model import SalaryRecordCreate,SalaryRecordResponse,SalaryRecordUpdate
from models.dutyassignment import DutyAssignment, DutyStatus
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
            DutyAssignment.guard_contact_number == guard.contact_number,
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

@search.get("/clients")
async def search_clients_advanced(
    name: Optional[str] = None,
    contact: Optional[str] = None,
    with_active_guards: Optional[bool] = False,
    db: Session = Depends(get_db)
):
    query = db.query(Client)
    
    if name:
        query = query.filter(Client.name.ilike(f"%{name}%"))
    if contact:
        query = query.filter(Client.contact_number.ilike(f"%{contact}%"))
    
    if with_active_guards:
        query = query.join(DutyAssignment).filter(DutyAssignment.is_active == True).distinct()
    
    clients = query.all()
    
    result = []
    for client in clients:
        active_guards = db.query(DutyAssignment).filter(
            DutyAssignment.client_contact_number == client.contact_number,
            DutyAssignment.is_active == True
        ).count()
        
        result.append({
            "id": client.id,
            "name": client.name,
            "contact_number": client.contact_number,
            "contact_person"
            "active_guards_count": active_guards
        })
    
    return result

@search.get("/assignments")
async def search_assignments_advanced(
    client_name: Optional[str] = None,
    guard_name: Optional[str] = None,
    duty_status: Optional[DutyStatus] = None,
    active_only: Optional[bool] = False,
    db: Session = Depends(get_db)
):
    query = db.query(DutyAssignment).join(Client).join(Guard)
    
    if client_name:
        query = query.filter(Client.name.ilike(f"%{client_name}%"))
    if guard_name:
        query = query.filter(Guard.name.ilike(f"%{guard_name}%"))
    if duty_status:
        query = query.filter(DutyAssignment.duty_status == duty_status)
    if active_only:
        query = query.filter(DutyAssignment.is_active == True)
    
    assignments = query.all()
    
    result = []
    for a in assignments:
        result.append({
            "id": a.id,
            "client_name": a.client.name,
            "guard_name": a.guard.name,
            "duty_status": a.duty_status,
            "is_active": a.is_active,
            "start_date": a.start_date,
            "end_date": a.end_date
        })
    
    return result
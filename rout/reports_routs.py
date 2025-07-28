from fastapi import APIRouter, HTTPException, Depends, Query
from utils.util import get_db
from config.database import Session
from datetime import datetime
from models.guard import Guard, GuardStatus
from models.salaryrecord import SalaryRecord
from models.inventoryrecord import InventoryRecord,InventoryStatus
from models.client import Client
from models.dutyassignment import DutyAssignment

report = APIRouter()


@report.get("/monthly-summary")
async def get_monthly_summary(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    db: Session = Depends(get_db)
):
    # Total guards active in the month
    total_guards = db.query(Guard).filter(Guard.status == GuardStatus.ACTIVE).count()
    
    # Salary summary for the month
    salary_records = db.query(SalaryRecord).filter(
        SalaryRecord.month == month,
        SalaryRecord.year == year
    ).all()
    
    total_salary_paid = sum(record.final_salary for record in salary_records if record.is_paid)
    total_salary_pending = sum(record.final_salary for record in salary_records if not record.is_paid)
    
    # Active assignments in the month
    active_assignments = db.query(DutyAssignment).filter(
        DutyAssignment.is_active == True
    ).count()
    
    # Inventory issued in the month
    inventory_issued = db.query(InventoryRecord).filter(
        InventoryRecord.issue_date >= datetime(year, month, 1),
        InventoryRecord.issue_date < datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
    ).count()
    
    return {
        "month": month,
        "year": year,
        "total_guards": total_guards,
        "active_assignments": active_assignments,
        "salary_summary": {
            "total_paid": total_salary_paid,
            "total_pending": total_salary_pending,
            "records_processed": len(salary_records)
        },
        "inventory_issued": inventory_issued
    }

@report.get("/client-summary/{client_id}")
async def get_client_summary(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Current guards assigned
    current_assignments = db.query(DutyAssignment).filter(
        DutyAssignment.client_id == client_id,
        DutyAssignment.is_active == True
    ).all()
    
    # Historical assignments
    total_assignments = db.query(DutyAssignment).filter(
        DutyAssignment.client_id == client_id
    ).count()
    
    # Guard details
    guards_info = []
    for assignment in current_assignments:
        guard_info = {
            "guard_id": assignment.guard.id,
            "name": assignment.guard.name,
            "contact_number": assignment.guard.contact_number,
            "duty_status": assignment.duty_status,
            "shift_type": assignment.shift_type,
            "start_date": assignment.start_date,
            "duration_days": (datetime.utcnow() - assignment.start_date).days
        }
        guards_info.append(guard_info)
    
    return {
        "client": client,
        "current_guards_count": len(current_assignments),
        "total_historical_assignments": total_assignments,
        "current_guards": guards_info,
        "monthly_cost": client.contract_rate * len(current_assignments)
    }

@report.get("/guard-history/{guard_id}")
async def get_guard_history(guard_id: int, db: Session = Depends(get_db)):
    guard = db.query(Guard).filter(Guard.id == guard_id).first()
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    
    # Assignment history
    assignments = db.query(DutyAssignment).filter(
        DutyAssignment.guard_id == guard_id
    ).order_by(DutyAssignment.start_date.desc()).all()
    
    # Salary history
    salary_records = db.query(SalaryRecord).filter(
        SalaryRecord.guard_id == guard_id
    ).order_by(SalaryRecord.year.desc(), SalaryRecord.month.desc()).all()
    
    # Inventory history
    inventory_records = db.query(InventoryRecord).filter(
        InventoryRecord.guard_id == guard_id
    ).order_by(InventoryRecord.issue_date.desc()).all()
    
    # Calculate total earnings
    total_earnings = sum(record.final_salary for record in salary_records if record.is_paid)
    pending_earnings = sum(record.final_salary for record in salary_records if not record.is_paid)
    
    return {
        "guard": guard,
        "assignment_history": [
            {
                "client_name": assignment.client.name,
                "start_date": assignment.start_date,
                "end_date": assignment.end_date,
                "duty_status": assignment.duty_status,
                "is_active": assignment.is_active
            }
            for assignment in assignments
        ],
        "salary_summary": {
            "total_paid": total_earnings,
            "total_pending": pending_earnings,
            "records_count": len(salary_records)
        },
        "inventory_summary": {
            "total_items_issued": len(inventory_records),
            "currently_issued": len([r for r in inventory_records if r.status == InventoryStatus.ISSUED])
        }
    }
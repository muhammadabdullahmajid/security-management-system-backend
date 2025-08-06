from fastapi import APIRouter, HTTPException, Depends, Query
from utils.util import get_db
from sqlalchemy.orm import  Session 
from models.client import Client
from datetime import datetime
from models.dutyassignment import DutyAssignment, DutyStatus
from models.guard import Guard, GuardStatus
from models.salaryrecord import SalaryRecord
from models.inventoryrecord import InventoryRecord,InventoryStatus


stat=APIRouter()



@stat.get("/overview")
async def get_system_overview(db: Session = Depends(get_db)):
    try:
    # Guard statistics
        guard_stats = {
            "total": db.query(Guard).count(),
            "active": db.query(Guard).filter(Guard.status == GuardStatus.ACTIVE).count(),
            "inactive": db.query(Guard).filter(Guard.status == GuardStatus.INACTIVE).count(),
            "on_leave": db.query(Guard).filter(Guard.status == GuardStatus.ON_LEAVE).count()
        }
        
        # Assignment statistics
        assignment_stats = {
            "total_active": db.query(DutyAssignment).filter(DutyAssignment.is_active == True).count(),
            "on_duty": db.query(DutyAssignment).filter(
                DutyAssignment.is_active == True,
                DutyAssignment.duty_status == DutyStatus.ON_DUTY
            ).count(),
            "off_duty": db.query(DutyAssignment).filter(
                DutyAssignment.is_active == True,
                DutyAssignment.duty_status == DutyStatus.OFF_DUTY
            ).count()
        }
        
        # Client statistics
        client_stats = {
            "total": db.query(Client).count(),
            "with_guards": db.query(Client).join(DutyAssignment).filter(
                DutyAssignment.is_active == True
            ).distinct().count()
        }
        
        # Financial statistics
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year
        
        monthly_salaries = db.query(SalaryRecord).filter(
            SalaryRecord.month == current_month,
            SalaryRecord.year == current_year
        ).all()
        
        financial_stats = {
            "monthly_salary_paid": sum(r.final_salary for r in monthly_salaries if r.is_paid),
            "monthly_salary_pending": sum(r.final_salary for r in monthly_salaries if not r.is_paid),
            "total_salary_records": len(monthly_salaries)
        }
        
        # Inventory statistics
        inventory_stats = {
            "total_items": db.query(InventoryRecord).count(),
            "currently_issued": db.query(InventoryRecord).filter(
                InventoryRecord.status == InventoryStatus.ISSUED
            ).count(),
            "returned": db.query(InventoryRecord).filter(
                InventoryRecord.status == InventoryStatus.RETURNED
            ).count()
        }
        
        return {
            "guards": guard_stats,
            "assignments": assignment_stats,
            "clients": client_stats,
            "financial": financial_stats,
            "inventory": inventory_stats,
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        print(f"Error fetching system overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch system overview")
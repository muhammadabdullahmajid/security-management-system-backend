from fastapi import APIRouter, HTTPException, Depends, Query
from utils.util import get_db
from config.database import Session
from datetime import datetime
from utils.pydantic_model import SalaryRecordCreate,SalaryRecordResponse,SalaryRecordUpdate
from models.salaryrecord import SalaryRecord
from models.guard import Guard
from typing import List, Optional

salary_record = APIRouter()


@salary_record.post("/", response_model=SalaryRecordResponse)
async def create_salary_record(salary: SalaryRecordCreate, db: Session = Depends(get_db)):
    # Check if guard exists
    guard = db.query(Guard).filter(Guard.id == salary.guard_id).first()
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    
    # Check if salary record already exists for this month/year
    existing = db.query(SalaryRecord).filter(
        SalaryRecord.guard_id == salary.guard_id,
        SalaryRecord.month == salary.month,
        SalaryRecord.year == salary.year
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Salary record already exists for this month")
    
    # Calculate final salary
    final_salary = (
        salary.base_salary - 
        (salary.deductions or 0) - 
        (salary.uniform_deduction or 500) + 
        (salary.bonus or 0)
    )
    
    db_salary = SalaryRecord(**salary.dict(), final_salary=final_salary)
    db.add(db_salary)
    db.commit()
    db.refresh(db_salary)
    return db_salary

@salary_record.get("/", response_model=List[SalaryRecordResponse])
async def get_salary_records(
    skip: int = 0,
    limit: int = 100,
    guard_id: Optional[int] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    is_paid: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(SalaryRecord)
    
    if guard_id:
        query = query.filter(SalaryRecord.guard_id == guard_id)
    if month:
        query = query.filter(SalaryRecord.month == month)
    if year:
        query = query.filter(SalaryRecord.year == year)
    if is_paid is not None:
        query = query.filter(SalaryRecord.is_paid == is_paid)
    
    records = query.offset(skip).limit(limit).all()
    return records

@salary_record.get("/{record_id}", response_model=SalaryRecordResponse)
async def get_salary_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(SalaryRecord).filter(SalaryRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Salary record not found")
    return record

@salary_record.put("/{record_id}", response_model=SalaryRecordResponse)
async def update_salary_record(
    record_id: int,
    salary_update: SalaryRecordUpdate,
    db: Session = Depends(get_db)
):
    record = db.query(SalaryRecord).filter(SalaryRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Salary record not found")
    
    for field, value in salary_update.dict(exclude_unset=True).items():
        setattr(record, field, value)
    
    # Recalculate final salary
    record.final_salary = (
        record.base_salary - 
        record.deductions - 
        record.uniform_deduction + 
        record.bonus
    )
    
    record.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(record)
    return record

@salary_record.post("/calculate/{guard_id}")
async def calculate_salary(
    guard_id: int,
    month: int,
    year: int,
    base_salary: float,
    db: Session = Depends(get_db)
):
    # Auto-calculate salary with standard deductions
    guard = db.query(Guard).filter(Guard.id == guard_id).first()
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    
    # Check if record already exists
    existing = db.query(SalaryRecord).filter(
        SalaryRecord.guard_id == guard_id,
        SalaryRecord.month == month,
        SalaryRecord.year == year
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Salary record already exists")
    
    # Standard calculations
    uniform_deduction = 500.0
    final_salary = base_salary - uniform_deduction
    
    salary_record = SalaryRecord(
        guard_id=guard_id,
        month=month,
        year=year,
        base_salary=base_salary,
        uniform_deduction=uniform_deduction,
        final_salary=final_salary
    )
    
    db.add(salary_record)
    db.commit()
    db.refresh(salary_record)
    
    return salary_record
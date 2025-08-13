from fastapi import APIRouter, HTTPException, Depends, Query
from utils.util import get_db
from sqlalchemy.orm import  Session 
from datetime import datetime
from utils.pydantic_model import SalaryRecordCreate,SalaryRecordResponse,SalaryRecordUpdate
from models.salaryrecord import SalaryRecord
from models.guard import Guard
from typing import List, Optional

salaryrecord = APIRouter()


@salaryrecord.post("/", response_model=SalaryRecordResponse)
async def create_salary_record(salary: SalaryRecordCreate, db: Session = Depends(get_db)):
    # 1. Get guard
    guard = db.query(Guard).filter(Guard.contact_number == salary.guard_contact_number).first()
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")

    # 2. Check duplicate salary record
    existing = db.query(SalaryRecord).filter(
        SalaryRecord.guard_contact_number == salary.guard_contact_number,
        SalaryRecord.month == salary.month,
        SalaryRecord.year == salary.year
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Salary record already exists for this month")

    # 3. Determine uniform deduction amount
    monthly_deduction = guard.monthly_deduction or 500.0
    base_salary = guard.current_salary
    remaining_uniform_amount = guard.uniform_cost - guard.uniform_deducted_amount
    uniform_deduction = 0.0
    if remaining_uniform_amount > 0:
        uniform_deduction = min(monthly_deduction, remaining_uniform_amount)
        guard.uniform_deducted_amount += uniform_deduction  # Update progress

    # 4. Final salary calculation
    final_salary = (
        base_salary -
        (salary.deductions or 0.0) -
        uniform_deduction +
        (salary.bonus or 0.0)
    )

    # 5. Create salary record
    db_salary = SalaryRecord(
        **salary.dict(exclude={"uniform_deduction"}),
        uniform_deduction=uniform_deduction,
        final_salary=final_salary
    )
    db.add(db_salary)
    db.commit()
    db.refresh(db_salary)

    return db_salary

@salaryrecord.get("/", response_model=List[SalaryRecordResponse])
async def get_salary_records(
    skip: int = 0,
    limit: int = 100,
    guard_contact_number: Optional[int] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    is_paid: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(SalaryRecord)

    if guard_contact_number:
        query = query.filter(SalaryRecord.guard_contact_number == guard_contact_number)
    if month:
        query = query.filter(SalaryRecord.month == month)
    if year:
        query = query.filter(SalaryRecord.year == year)
    if is_paid is not None:
        query = query.filter(SalaryRecord.is_paid == is_paid)
    
    records = query.offset(skip).limit(limit).all()
    return records

@salaryrecord.get("/{contact_number}", response_model=SalaryRecordResponse)
async def get_salary_record(contact_number: str, db: Session = Depends(get_db)):
    record = db.query(SalaryRecord).filter(SalaryRecord.guard_contact_number == contact_number).first()
    if not record:
        raise HTTPException(status_code=404, detail="Salary record not found")
    return record

@salaryrecord.get("/{record_id}", response_model=SalaryRecordResponse)
async def get_guard_by_salary_record(record_id: int, db: Session = Depends(get_db)):
    try:
        record = db.query(SalaryRecord).filter(SalaryRecord.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="Salary record not found")
        
        guard = db.query(Guard).filter(Guard.contact_number == record.guard_contact_number).first()
        if not guard:
            raise HTTPException(status_code=404, detail="Guard not found")
        
        return guard
    except Exception as e:
        print(f"Error fetching guard by salary record: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@salaryrecord.put("/{contact_number}", response_model=SalaryRecordResponse)
async def update_salary_record(
    contact_number: str,
    salary_update: SalaryRecordUpdate,
    db: Session = Depends(get_db)
):
    guard = db.query(Guard).filter(Guard.contact_number == contact_number).first()
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    record = db.query(SalaryRecord).filter(SalaryRecord.guard_contact_number == contact_number).first()
    if not record:
        raise HTTPException(status_code=404, detail="Salary record not found")
    
    for field, value in salary_update.dict(exclude_unset=True).items():
        setattr(record, field, value)
    
    # Recalculate final salary
    record.final_salary = (
    (guard.current_salary or 0.0) -
    (record.deductions or 0.0) -
    (record.uniform_deduction or 0.0) +
    (record.bonus or 0.0)
)
    
    record.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(record)
    return record

@salaryrecord.put("/by-id/{record_id}", response_model=SalaryRecordResponse)
async def update_salary_record_by_id(
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
    guard = db.query(Guard).filter(Guard.contact_number == record.guard_contact_number).first()
    if guard:
        record.final_salary = (
            (guard.current_salary or 0.0)
            - (record.deductions or 0.0)
            - (record.uniform_deduction or 0.0)
            + (record.bonus or 0.0)
        )

    record.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(record)
    return record

@salaryrecord.delete("/{record_id}")
async def delete_salary_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(SalaryRecord).filter(SalaryRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Salary record not found")
    db.delete(record)
    db.commit()
    return {"message": "Salary record deleted successfully"}

# @salaryrecord.get("/stat")
# async def get_salary_stats(db: Session = Depends(get_db)):
#     paid_count = db.query(SalaryRecord).filter(SalaryRecord.is_paid == True).count()
#     unpaid_count = db.query(SalaryRecord).filter(SalaryRecord.is_paid == False).count()
#     total_paid = db.query(SalaryRecord.final_salary).filter(SalaryRecord.is_paid == True).all()
#     total_pending = db.query(SalaryRecord.final_salary).filter(SalaryRecord.is_paid == False).all()

#     return {
#         "paid_count": paid_count,
#         "unpaid_count": unpaid_count,
#         "total_paid": sum(x[0] for x in total_paid),
#         "total_pending": sum(x[0] for x in total_pending)
#     }
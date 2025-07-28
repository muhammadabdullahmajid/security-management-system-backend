# Security Management System - FastAPI Backend
# requirements.txt dependencies:
# fastapi==0.104.1
# uvicorn==0.24.0
# sqlalchemy==2.0.23
# psycopg2-binary==2.9.9
# pydantic==2.5.0
# python-multipart==0.0.6

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List
import enum

# Database Configuration
DATABASE_URL = "postgresql://username:password@localhost/security_management_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# FastAPI App
app = FastAPI(title="Security Management System", version="1.0.0")

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enums
class GuardStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"

class DutyStatus(str, enum.Enum):
    ON_DUTY = "on_duty"
    OFF_DUTY = "off_duty"
    AVAILABLE = "available"

class InventoryStatus(str, enum.Enum):
    ISSUED = "issued"
    RETURNED = "returned"
    LOST = "lost"

# Database Models
class Guard(Base):
    __tablename__ = "guards"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    contact_number = Column(String, unique=True, nullable=False, index=True)
    address = Column(Text)
    join_date = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(GuardStatus), default=GuardStatus.ACTIVE)
    current_salary = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    duty_assignments = relationship("DutyAssignment", back_populates="guard")
    salary_records = relationship("SalaryRecord", back_populates="guard")
    inventory_items = relationship("InventoryRecord", back_populates="guard")

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    contact_person = Column(String)
    contact_number = Column(String)
    address = Column(Text)
    contract_rate = Column(Float, default=0.0)  # Rate per guard per month
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    duty_assignments = relationship("DutyAssignment", back_populates="client")

class DutyAssignment(Base):
    __tablename__ = "duty_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    guard_id = Column(Integer, ForeignKey("guards.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    duty_status = Column(Enum(DutyStatus), default=DutyStatus.ON_DUTY)
    shift_type = Column(String, default="day")  # day, night, 24hour
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    guard = relationship("Guard", back_populates="duty_assignments")
    client = relationship("Client", back_populates="duty_assignments")

class SalaryRecord(Base):
    __tablename__ = "salary_records"
    
    id = Column(Integer, primary_key=True, index=True)
    guard_id = Column(Integer, ForeignKey("guards.id"), nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)
    base_salary = Column(Float, nullable=False)
    deductions = Column(Float, default=0.0)
    uniform_deduction = Column(Float, default=500.0)
    bonus = Column(Float, default=0.0)
    final_salary = Column(Float, nullable=False)
    is_paid = Column(Boolean, default=False)
    payment_date = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    guard = relationship("Guard", back_populates="salary_records")

class InventoryRecord(Base):
    __tablename__ = "inventory_records"
    
    id = Column(Integer, primary_key=True, index=True)
    guard_id = Column(Integer, ForeignKey("guards.id"), nullable=False)
    item_name = Column(String, nullable=False)
    item_type = Column(String, nullable=False)  # uniform, shoes, gun, equipment
    quantity = Column(Integer, default=1)
    issue_date = Column(DateTime, nullable=False)
    return_date = Column(DateTime)
    status = Column(Enum(InventoryStatus), default=InventoryStatus.ISSUED)
    condition_on_issue = Column(String, default="good")
    condition_on_return = Column(String)
    cost = Column(Float, default=0.0)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    guard = relationship("Guard", back_populates="inventory_items")

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Models for API
class GuardCreate(BaseModel):
    name: str
    contact_number: str
    address: Optional[str] = None
    current_salary: Optional[float] = 0.0

class GuardUpdate(BaseModel):
    name: Optional[str] = None
    contact_number: Optional[str] = None
    address: Optional[str] = None
    status: Optional[GuardStatus] = None
    current_salary: Optional[float] = None

class GuardResponse(BaseModel):
    id: int
    name: str
    contact_number: str
    address: Optional[str]
    join_date: datetime
    status: GuardStatus
    current_salary: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ClientCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    contact_number: Optional[str] = None
    address: Optional[str] = None
    contract_rate: Optional[float] = 0.0

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    contact_number: Optional[str] = None
    address: Optional[str] = None
    contract_rate: Optional[float] = None

class ClientResponse(BaseModel):
    id: int
    name: str
    contact_person: Optional[str]
    contact_number: Optional[str]
    address: Optional[str]
    contract_rate: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DutyAssignmentCreate(BaseModel):
    guard_id: int
    client_id: int
    start_date: datetime
    end_date: Optional[datetime] = None
    duty_status: Optional[DutyStatus] = DutyStatus.ON_DUTY
    shift_type: Optional[str] = "day"

class DutyAssignmentUpdate(BaseModel):
    client_id: Optional[int] = None
    end_date: Optional[datetime] = None
    duty_status: Optional[DutyStatus] = None
    shift_type: Optional[str] = None
    is_active: Optional[bool] = None

class DutyAssignmentResponse(BaseModel):
    id: int
    guard_id: int
    client_id: int
    start_date: datetime
    end_date: Optional[datetime]
    duty_status: DutyStatus
    shift_type: str
    is_active: bool
    guard: GuardResponse
    client: ClientResponse
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SalaryRecordCreate(BaseModel):
    guard_id: int
    month: int
    year: int
    base_salary: float
    deductions: Optional[float] = 0.0
    uniform_deduction: Optional[float] = 500.0
    bonus: Optional[float] = 0.0
    notes: Optional[str] = None

class SalaryRecordUpdate(BaseModel):
    base_salary: Optional[float] = None
    deductions: Optional[float] = None
    uniform_deduction: Optional[float] = None
    bonus: Optional[float] = None
    is_paid: Optional[bool] = None
    payment_date: Optional[datetime] = None
    notes: Optional[str] = None

class SalaryRecordResponse(BaseModel):
    id: int
    guard_id: int
    month: int
    year: int
    base_salary: float
    deductions: float
    uniform_deduction: float
    bonus: float
    final_salary: float
    is_paid: bool
    payment_date: Optional[datetime]
    notes: Optional[str]
    guard: GuardResponse
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class InventoryRecordCreate(BaseModel):
    guard_id: int
    item_name: str
    item_type: str
    quantity: Optional[int] = 1
    issue_date: datetime
    condition_on_issue: Optional[str] = "good"
    cost: Optional[float] = 0.0
    notes: Optional[str] = None

class InventoryRecordUpdate(BaseModel):
    return_date: Optional[datetime] = None
    status: Optional[InventoryStatus] = None
    condition_on_return: Optional[str] = None
    notes: Optional[str] = None

class InventoryRecordResponse(BaseModel):
    id: int
    guard_id: int
    item_name: str
    item_type: str
    quantity: int
    issue_date: datetime
    return_date: Optional[datetime]
    status: InventoryStatus
    condition_on_issue: str
    condition_on_return: Optional[str]
    cost: float
    notes: Optional[str]
    guard: GuardResponse
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# API Routes

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Security Management System API", "version": "1.0.0"}

# Dashboard endpoint
@app.get("/dashboard")
async def get_dashboard(db: Session = Depends(get_db)):
    total_guards = db.query(Guard).count()
    active_guards = db.query(Guard).filter(Guard.status == GuardStatus.ACTIVE).count()
    total_clients = db.query(Client).count()
    active_assignments = db.query(DutyAssignment).filter(DutyAssignment.is_active == True).count()
    guards_on_duty = db.query(DutyAssignment).filter(
        DutyAssignment.is_active == True,
        DutyAssignment.duty_status == DutyStatus.ON_DUTY
    ).count()
    guards_available = db.query(Guard).filter(
        Guard.status == GuardStatus.ACTIVE,
        ~Guard.duty_assignments.any(DutyAssignment.is_active == True)
    ).count()
    
    return {
        "total_guards": total_guards,
        "active_guards": active_guards,
        "total_clients": total_clients,
        "active_assignments": active_assignments,
        "guards_on_duty": guards_on_duty,
        "guards_available": guards_available
    }

# Guard Management APIs
@app.post("/guards/", response_model=GuardResponse)
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

@app.get("/guards/", response_model=List[GuardResponse])
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

@app.get("/guards/{guard_id}", response_model=GuardResponse)
async def get_guard(guard_id: int, db: Session = Depends(get_db)):
    guard = db.query(Guard).filter(Guard.id == guard_id).first()
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    return guard

@app.get("/guards/by-contact/{contact_number}", response_model=GuardResponse)
async def get_guard_by_contact(contact_number: str, db: Session = Depends(get_db)):
    guard = db.query(Guard).filter(Guard.contact_number == contact_number).first()
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    return guard

@app.put("/guards/{guard_id}", response_model=GuardResponse)
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

@app.delete("/guards/{guard_id}")
async def delete_guard(guard_id: int, db: Session = Depends(get_db)):
    guard = db.query(Guard).filter(Guard.id == guard_id).first()
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    
    db.delete(guard)
    db.commit()
    return {"message": "Guard deleted successfully"}

# Client Management APIs
@app.post("/clients/", response_model=ClientResponse)
async def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    db_client = Client(**client.dict())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

@app.get("/clients/", response_model=List[ClientResponse])
async def get_clients(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Client)
    
    if search:
        query = query.filter(Client.name.ilike(f"%{search}%"))
    
    clients = query.offset(skip).limit(limit).all()
    return clients

@app.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@app.get("/clients/{client_id}/guards")
async def get_client_guards(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    assignments = db.query(DutyAssignment).filter(
        DutyAssignment.client_id == client_id,
        DutyAssignment.is_active == True
    ).all()
    
    guards_info = []
    for assignment in assignments:
        guard_info = {
            "guard_id": assignment.guard.id,
            "name": assignment.guard.name,
            "contact_number": assignment.guard.contact_number,
            "duty_status": assignment.duty_status,
            "shift_type": assignment.shift_type,
            "start_date": assignment.start_date
        }
        guards_info.append(guard_info)
    
    return {
        "client": client,
        "total_guards": len(guards_info),
        "guards": guards_info
    }

@app.put("/clients/{client_id}", response_model=ClientResponse)
async def update_client(client_id: int, client_update: ClientUpdate, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    for field, value in client_update.dict(exclude_unset=True).items():
        setattr(client, field, value)
    
    client.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(client)
    return client

@app.delete("/clients/{client_id}")
async def delete_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    db.delete(client)
    db.commit()
    return {"message": "Client deleted successfully"}

# Duty Assignment APIs
@app.post("/duty-assignments/", response_model=DutyAssignmentResponse)
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

@app.get("/duty-assignments/", response_model=List[DutyAssignmentResponse])
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

@app.get("/duty-assignments/{assignment_id}", response_model=DutyAssignmentResponse)
async def get_duty_assignment(assignment_id: int, db: Session = Depends(get_db)):
    assignment = db.query(DutyAssignment).filter(DutyAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment

@app.put("/duty-assignments/{assignment_id}", response_model=DutyAssignmentResponse)
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

@app.post("/duty-assignments/reassign/{guard_id}")
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

# Salary Management APIs
@app.post("/salary-records/", response_model=SalaryRecordResponse)
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

@app.get("/salary-records/", response_model=List[SalaryRecordResponse])
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

@app.get("/salary-records/{record_id}", response_model=SalaryRecordResponse)
async def get_salary_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(SalaryRecord).filter(SalaryRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Salary record not found")
    return record

@app.put("/salary-records/{record_id}", response_model=SalaryRecordResponse)
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

@app.post("/salary-records/calculate/{guard_id}")
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

# Inventory Management APIs
@app.post("/inventory-records/", response_model=InventoryRecordResponse)
async def create_inventory_record(inventory: InventoryRecordCreate, db: Session = Depends(get_db)):
    # Check if guard exists
    guard = db.query(Guard).filter(Guard.id == inventory.guard_id).first()
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    
    db_inventory = InventoryRecord(**inventory.dict())
    db.add(db_inventory)
    db.commit()
    db.refresh(db_inventory)
    return db_inventory

@app.get("/inventory-records/", response_model=List[InventoryRecordResponse])
async def get_inventory_records(
    skip: int = 0,
    limit: int = 100,
    guard_id: Optional[int] = None,
    item_type: Optional[str] = None,
    status: Optional[InventoryStatus] = None,
    db: Session = Depends(get_db)
):
    query = db.query(InventoryRecord)
    
    if guard_id:
        query = query.filter(InventoryRecord.guard_id == guard_id)
    if item_type:
        query = query.filter(InventoryRecord.item_type == item_type)
    if status:
        query = query.filter(InventoryRecord.status == status)
    
    records = query.offset(skip).limit(limit).all()
    return records

@app.get("/inventory-records/{record_id}", response_model=InventoryRecordResponse)
async def get_inventory_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(InventoryRecord).filter(InventoryRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Inventory record not found")
    return record

@app.put("/inventory-records/{record_id}", response_model=InventoryRecordResponse)
async def update_inventory_record(
    record_id: int,
    inventory_update: InventoryRecordUpdate,
    db: Session = Depends(get_db)
):
    record = db.query(InventoryRecord).filter(InventoryRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Inventory record not found")
    
    for field, value in inventory_update.dict(exclude_unset=True).items():
        setattr(record, field, value)
    
    record.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(record)
    return record

@app.post("/inventory-records/return/{record_id}")
async def return_inventory_item(
    record_id: int,
    condition: Optional[str] = "good",
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    record = db.query(InventoryRecord).filter(InventoryRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Inventory record not found")
    
    if record.status != InventoryStatus.ISSUED:
        raise HTTPException(status_code=400, detail="Item is not currently issued")
    
    record.return_date = datetime.utcnow()
    record.status = InventoryStatus.RETURNED
    record.condition_on_return = condition
    if notes:
        record.notes = notes
    record.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(record)
    
    return {"message": "Item returned successfully", "record": record}

@app.get("/inventory-records/guard/{guard_id}")
async def get_guard_inventory(guard_id: int, db: Session = Depends(get_db)):
    guard = db.query(Guard).filter(Guard.id == guard_id).first()
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    
    # Get all inventory items for this guard
    issued_items = db.query(InventoryRecord).filter(
        InventoryRecord.guard_id == guard_id,
        InventoryRecord.status == InventoryStatus.ISSUED
    ).all()
    
    returned_items = db.query(InventoryRecord).filter(
        InventoryRecord.guard_id == guard_id,
        InventoryRecord.status == InventoryStatus.RETURNED
    ).all()
    
    return {
        "guard": guard,
        "issued_items": issued_items,
        "returned_items": returned_items,
        "total_issued": len(issued_items),
        "total_returned": len(returned_items)
    }

# Advanced Search and Reporting APIs
@app.get("/search/guards")
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

@app.get("/reports/monthly-summary")
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

@app.get("/reports/client-summary/{client_id}")
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

@app.get("/reports/guard-history/{guard_id}")
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

# Utility endpoints
@app.get("/stats/overview")
async def get_system_overview(db: Session = Depends(get_db)):
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

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
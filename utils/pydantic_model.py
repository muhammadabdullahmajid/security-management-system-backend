from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from models.guard import GuardStatus
from models.dutyassignment import DutyStatus
from models.inventoryrecord import InventoryStatus




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
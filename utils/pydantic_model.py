from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from models.guard import GuardStatus
from models.dutyassignment import DutyStatus
from models.inventoryrecord import InventoryStatus




class GuardCreate(BaseModel):
    name: str
    contact_number: str
    address: Optional[str] = None
    cnic: Optional[str] = None
    current_salary: Optional[float] = 0.0
    uniform_cost: Optional[float] = None
    monthly_deduction: Optional[float] = 0.0
    image_url: str
    cnic_front_url: Optional[str] = None
    cnic_back_url: Optional[str] = None

    

class GuardUpdate(BaseModel):
    name: Optional[str] = None
    contact_number: Optional[str] = None
    address: Optional[str] = None
    cnic: Optional[str] = None
    current_salary: Optional[float] = None
    status: Optional[GuardStatus] = None
    image_url: Optional[str] = None
    cnic_front_url: Optional[str] = None
    cnic_back_url: Optional[str] = None

class GuardResponse(BaseModel):
    id: int
    name: str
    contact_number: str
    address: Optional[str]
    cnic: Optional[str] = None
    join_date: datetime
    status: GuardStatus
    current_salary: float
    image_url: Optional[str]
    cnic_front_url: Optional[str]
    cnic_back_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ClientCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    contact_number: Optional[str] = None
    address: Optional[str] = None
    company_name: Optional[str] = None
    contract_rate: Optional[float] = 0.0

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    contact_number: Optional[str] = None
    company_name: Optional[str] = None
    address: Optional[str] = None
    contract_rate: Optional[float] = None

class ClientResponse(BaseModel):
    id: int
    name: str
    contact_person: Optional[str]
    contact_number: Optional[str]
    address: Optional[str]
    company_name: Optional[str] = None
    contract_rate: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DutyAssignmentCreate(BaseModel):
    guard_contact_number: str
    client_contact_number: str
    company_name: Optional[str] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    duty_status: Optional[DutyStatus] = DutyStatus.ON_DUTY
    shift_type: Optional[str] = "day"

class DutyAssignmentUpdate(BaseModel):
    client_contact_number: str
    company_name: Optional[str] = None
    end_date: Optional[datetime] = None
    duty_status: Optional[DutyStatus] = None
    shift_type: Optional[str] = None
    is_active: Optional[bool] = None

class DutyAssignmentResponse(BaseModel):
    id: int
    guard_contact_number: str
    client_contact_number: str
    name: Optional[str] = None
    company_name: Optional[str] = None
    start_date: datetime
    end_date: Optional[datetime]
    duty_status: DutyStatus
    shift_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SalaryRecordCreate(BaseModel):
    guard_contact_number: str
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2000)
    deductions: Optional[float] = 0.0
    bonus: Optional[float] = 0.0
    notes: Optional[str] = None

class SalaryRecordUpdate(BaseModel):
    deductions: Optional[float] = None
    bonus: Optional[float] = None
    is_paid: Optional[bool] = None
    payment_date: Optional[datetime] = None
    notes: Optional[str] = None

class SalaryRecordResponse(BaseModel):
    id: int
    guard_contact_number: str
    month: int
    year: int
    deductions: Optional[float]
    uniform_deduction: Optional[float]
    bonus: Optional[float]
    final_salary: float
    is_paid: bool
    payment_date: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class InventoryRecordCreate(BaseModel):
    guard_contact_number: str
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
    guard_contact_number: str
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

class DutyAssignmentReassign(BaseModel):
    guard_contact_number: str
    new_client_contact_number: str
    company_name: Optional[str]

class GuardAssignmentInfo(BaseModel):
    guard_id: int
    name: str
    contact_number: str
    duty_status: str
    shift_type: str
    start_date: datetime

class ClientGuardResponse(BaseModel):
    client_contact_number: str
    total_guards: int
    guards: List[GuardAssignmentInfo]

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    created_at: datetime

class LoginRequest(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str    

    
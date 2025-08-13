from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum
from sqlalchemy.orm import relationship, foreign
from datetime import datetime
from models.base import Base
import enum

class GuardStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"



class Guard(Base):
    __tablename__ = "guards"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    contact_number = Column(String, unique=True, nullable=False, index=True)
    address = Column(Text)
    cnic = Column (String, nullable= True)
    uniform_cost = Column(Float, default=4000.0)
    uniform_deducted_amount = Column(Float, default=0.0)
    monthly_deduction = Column(Float, default=0.0)
    image_url = Column( String, nullable=True)
    cnic_front_url= Column( String, nullable=True)
    cnic_back_url= Column( String, nullable=True)
    join_date = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(GuardStatus), default=GuardStatus.ACTIVE)
    current_salary = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    duty_assignments = relationship("DutyAssignment", back_populates="guard", primaryjoin="foreign(DutyAssignment.guard_contact_number) == Guard.contact_number")
    salary_records = relationship("SalaryRecord", back_populates="guard", primaryjoin="foreign(SalaryRecord.guard_contact_number) == Guard.contact_number")
    inventory_items = relationship("InventoryRecord", back_populates="guard", primaryjoin="foreign(InventoryRecord.guard_contact_number) == Guard.contact_number")

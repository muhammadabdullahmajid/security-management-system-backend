from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship, foreign
from datetime import datetime
from models.base import Base
import enum

class DutyStatus(str, enum.Enum):
    ON_DUTY = "on_duty"
    OFF_DUTY = "off_duty"
    AVAILABLE = "available"

class DutyAssignment(Base):
    __tablename__ = "duty_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    guard_contact_number = Column(String, ForeignKey("guards.contact_number"), nullable=False)
    client_contact_number = Column(String, ForeignKey("clients.contact_number"), nullable=False)
    name = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    duty_status = Column(Enum(DutyStatus), default=DutyStatus.ON_DUTY)
    shift_type = Column(String, default="day")  # day, night, 24hour
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    guard = relationship("Guard", back_populates="duty_assignments", primaryjoin="Guard.contact_number==DutyAssignment.guard_contact_number")
    client = relationship("Client", back_populates="duty_assignments", primaryjoin="Client.contact_number==DutyAssignment.client_contact_number")


from sqlalchemy import Column, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from base import Base


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
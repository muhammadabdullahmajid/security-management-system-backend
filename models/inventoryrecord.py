from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship, foreign
from datetime import datetime
from models.base import Base
import enum


class InventoryStatus(str, enum.Enum):
    ISSUED = "issued"
    RETURNED = "returned"
    LOST = "lost"


class InventoryRecord(Base):
    __tablename__ = "inventory_records"
    
    id = Column(Integer, primary_key=True, index=True)
    guard_contact_number = Column(String, ForeignKey("guards.contact_number"), nullable=False)
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
    guard = relationship("Guard", back_populates="inventory_items", primaryjoin="Guard.contact_number == foreign(InventoryRecord.guard_contact_number)")
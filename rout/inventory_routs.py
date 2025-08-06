from fastapi import APIRouter, HTTPException, Depends, Query
from utils.util import get_db
from sqlalchemy.orm import  Session 
from datetime import datetime
from utils.pydantic_model import InventoryStatus, InventoryRecordCreate,InventoryRecordResponse, InventoryRecordUpdate
from models.inventoryrecord import InventoryRecord,InventoryStatus
from models.guard import Guard
from typing import List, Optional

inventory_record=APIRouter()

@inventory_record.post("/", response_model=InventoryRecordResponse)
async def create_inventory_record(inventory: InventoryRecordCreate, db: Session = Depends(get_db)):
    # Check if guard exists
    guard = db.query(Guard).filter(Guard.contact_number == inventory.guard_contact_number).first()
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    
    db_inventory = InventoryRecord(**inventory.dict())
    db.add(db_inventory)
    db.commit()
    db.refresh(db_inventory)
    return db_inventory

@inventory_record.get("/inventory-records/", response_model=List[InventoryRecordResponse])
async def get_inventory_records(
    skip: int = 0,
    limit: int = 100,
    guard_contact_number: Optional[int] = None,
    item_type: Optional[str] = None,
    status: Optional[InventoryStatus] = None,
    db: Session = Depends(get_db)
):
    query = db.query(InventoryRecord)
    
    if guard_contact_number:
        query = query.filter(InventoryRecord.guard_contact_number == guard_contact_number)
    if item_type:
        query = query.filter(InventoryRecord.item_type == item_type)
    if status:
        query = query.filter(InventoryRecord.status == status)
    
    records = query.offset(skip).limit(limit).all()
    return records

@inventory_record.get("/inventory-records/{record_id}", response_model=InventoryRecordResponse)
async def get_inventory_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(InventoryRecord).filter(InventoryRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Inventory record not found")
    return record

@inventory_record.put("/inventory-records/{record_id}", response_model=InventoryRecordResponse)
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

@inventory_record.post("/inventory-records/return/{record_id}")
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

@inventory_record.get("/inventory-records/guard/{guard_id}")
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
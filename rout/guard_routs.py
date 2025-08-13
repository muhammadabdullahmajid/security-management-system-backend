from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from utils.util import get_db
from sqlalchemy.orm import  Session 
import uuid
import cloudinary
import cloudinary.uploader
from datetime import datetime
from dotenv import load_dotenv
from utils.pydantic_model import GuardCreate,GuardStatus,GuardResponse,GuardUpdate
from models.guard import Guard
from models.dutyassignment import DutyAssignment
from typing import List, Optional
import os

load_dotenv()
cloudinary.config()

guard= APIRouter()


@guard.post("/", response_model=GuardResponse)
async def create_guard(
    name: str = Form(...),
    contact_number: str = Form(...),
    address: Optional[str] = Form(None),
    cnic: Optional[str] = Form (None),
    current_salary: Optional[float] = Form(0.0),
    uniform_cost: Optional[float] = Form(None),
    monthly_deduction: Optional[float] = Form(0.0),
    db: Session = Depends(get_db),
    image: UploadFile = File(...),
    cnic_front_image: UploadFile = File(...),
    cnic_back_image: UploadFile = File(...)
):
    try:
        # Check if contact number already exists
        existing_guard = db.query(Guard).filter(Guard.contact_number == contact_number).first()
        if existing_guard:
            raise HTTPException(status_code=400, detail="Contact number already registered")

        # Helper to upload to Cloudinary
        def upload_to_cloudinary(file: UploadFile, folder: str):
            result = cloudinary.uploader.upload(
                file.file,
                folder=folder,
                public_id=str(uuid.uuid4()),
                resource_type="image"
            )
            return result.get("secure_url")

        # Upload all images
        image_url = upload_to_cloudinary(image, "guards")
        cnic_front_url = upload_to_cloudinary(cnic_front_image, "guards/cnic_front")
        cnic_back_url = upload_to_cloudinary(cnic_back_image, "guards/cnic_back")

        if not all([image_url, cnic_front_url, cnic_back_url]):
            raise HTTPException(status_code=500, detail="One or more image uploads failed")

        # Save guard data with all URLs
        db_guard = Guard(
            name=name,
            contact_number=contact_number,
            address=address,
            cnic = cnic,
            current_salary=current_salary,
            uniform_cost=uniform_cost,
            monthly_deduction=monthly_deduction,
            image_url=image_url,
            cnic_front_url=cnic_front_url,
            cnic_back_url=cnic_back_url
        )
        db.add(db_guard)
        db.commit()
        db.refresh(db_guard)

        return db_guard

    except Exception as e:
        print(f"Error creating guard: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


    
@guard.get("/", response_model=List[GuardResponse])
async def get_guards(
    skip: int = 0,
    limit: int = 100,
    status: Optional[GuardStatus] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
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
    except Exception as e:
        print(f"Error fetching guards: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@guard.get("/{guard_id}", response_model=GuardResponse)
async def get_guard(guard_id: int, db: Session = Depends(get_db)):
    try:
        guard = db.query(Guard).filter(Guard.id == guard_id).first()
        if not guard:
            raise HTTPException(status_code=404, detail="Guard not found")
        return guard
    except Exception as e:
        print(f"Error fetching guards by id: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@guard.get("/by-contact/{contact_number}", response_model=GuardResponse)
async def get_guard_by_contact(contact_number: str, db: Session = Depends(get_db)):
    try:
        guard = db.query(Guard).filter(Guard.contact_number == contact_number).first()
        if not guard:
            raise HTTPException(status_code=404, detail="Guard not found")
        return guard
    except Exception as e:
        print(f"Error fetching guards by contact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@guard.put("/{guard_id}", response_model=GuardResponse)
async def update_guard(
    guard_id: int,
    name: Optional[str] = Form(None),
    contact_number: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    cnic: Optional[str] = Form(None),
    current_salary: Optional[float] = Form(None),
    status: Optional[GuardStatus] = Form(None),
    image: Optional[UploadFile] = File(None),
    cnic_front_image: Optional[UploadFile] = File(None),
    cnic_back_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    guard = db.query(Guard).filter(Guard.id == guard_id).first()
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")

    if contact_number and contact_number != guard.contact_number:
        existing = db.query(Guard).filter(Guard.contact_number == contact_number).first()
        if existing:
            raise HTTPException(status_code=400, detail="Contact number already exists")

    if name: guard.name = name
    if contact_number: guard.contact_number = contact_number
    if address: guard.address = address
    if cnic: guard.cnic = cnic
    if current_salary: guard.current_salary = current_salary
    if status: guard.status = status

    def upload_to_cloudinary(file: UploadFile, folder: str):
            result = cloudinary.uploader.upload(
                file.file,
                folder=folder,
                public_id=str(uuid.uuid4()),
                resource_type="image"
            )
            return result.get("secure_url")
    
    # Upload files if provided
    if image:
        guard.image_url = await upload_to_cloudinary(image)
    if cnic_front_image:
        guard.cnic_front_url = await upload_to_cloudinary(cnic_front_image)
    if cnic_back_image:
        guard.cnic_back_url = await upload_to_cloudinary(cnic_back_image)

    guard.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(guard)
    return guard


@guard.delete("/{guard_id}")
async def delete_guard(guard_id: int, db: Session = Depends(get_db)):
    try:
        # Check if guard exists
        guard_obj = db.query(Guard).filter(Guard.id == guard_id).first()
        if not guard_obj:
            raise HTTPException(status_code=404, detail="Guard not found")
        
        guard_contact = guard_obj.contact_number

        # Check if guard has active assignments
        assignments = db.query(DutyAssignment).filter(
            DutyAssignment.guard_contact_number == guard_contact
        ).first()
        if assignments:
            # Don't catch this in the except, let FastAPI handle it
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete guard with active duty assignments"
            )

        # Delete guard
        db.delete(guard_obj)
        db.commit()
        return {"message": "Guard deleted successfully"}
    
    except HTTPException:
        # Re-raise HTTPException so FastAPI sends correct status code
        raise
    except Exception as e:
        print(f"Error deleting guard by id: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@guard.get("/all")
def total_guard(
    guard_id = Optional[int],
    db: Session = Depends(get_db)):
    try:
        total = db.query(Guard).count()  
        return {"total_guards": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
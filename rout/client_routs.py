from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from utils.util import get_db
from utils.pydantic_model import ClientCreate, ClientUpdate, ClientResponse, GuardAssignmentInfo, ClientGuardResponse
from sqlalchemy.orm import  Session 
from models.client import Client
from datetime import datetime
from models.dutyassignment import DutyAssignment

client= APIRouter()

@client.post("/", response_model=ClientResponse)
async def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    try:
        existing_client = db.query(Client).filter(Client.contact_number == client.contact_number).first()
        if existing_client:
            raise HTTPException(status_code=400, detail="Client with this contact number already exists")
        db_client = Client(**client.dict())
        db.add(db_client)
        db.commit()
        db.refresh(db_client)
        return db_client
    except Exception as e:
        print(f"Error creating clients: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@client.get("/", response_model=List[ClientResponse])
async def get_clients(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Client)
        
        if search:
            query = query.filter(Client.name.ilike(f"%{search}%"))
        
        clients = query.offset(skip).limit(limit).all()
        return clients
    except Exception as e:
        print(f"Error fetching clients: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@client.get("/{contact_number}", response_model=ClientResponse)
async def get_client(contact_number: str, db: Session = Depends(get_db)):
    try:
        client = db.query(Client).filter(Client.contact_number == contact_number).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        return client
    except Exception as e:
        print(f"Error fetching client by number: {e}")
        raise HTTPException(status_code=500, detail=str(e))  
     
@client.get("/{contact_number}/guards", response_model=ClientGuardResponse)
async def get_client_guards(contact_number: str, db: Session = Depends(get_db)):
    try:
        client = db.query(Client).filter(Client.contact_number == contact_number).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        assignments = db.query(DutyAssignment).filter(
            DutyAssignment.client_contact_number == contact_number,
            DutyAssignment.is_active == True
        ).all()

        guards_info = []
        for assignment in assignments:
            guards_info.append(GuardAssignmentInfo(
                guard_id=assignment.guard.id,
                name=assignment.guard.name,
                contact_number=assignment.guard.contact_number,
                duty_status=assignment.duty_status,
                shift_type=assignment.shift_type,
                start_date=assignment.start_date,
            ))

        return ClientGuardResponse(
            client_contact_number=contact_number,
            total_guards=len(guards_info),
            guards=guards_info
        )
    except Exception as e:
        print(f"Error fetching guards of client by number: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 


@client.put("/{client_id}", response_model=ClientResponse)
async def update_client(client_id: int, client_update: ClientUpdate, db: Session = Depends(get_db)):
    try:
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        for field, value in client_update.dict(exclude_unset=True).items():
            setattr(client, field, value)
        
        client.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(client)
        return client
    except Exception as e:
        print(f"Error update client by id: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 


@client.delete("/{client_id}")
async def delete_client(client_id: int, db: Session = Depends(get_db)):
    try:
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        db.delete(client)
        db.commit()
        return {"message": "Client deleted successfully"}
    except Exception as e:
        print(f"Error delete client by id: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
    
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from utils.util import get_db
from utils.pydantic_model import ClientCreate, ClientUpdate, ClientResponse
from config.database import Session
from models.client import Client
from datetime import datetime
from models.dutyassignment import DutyAssignment

client= APIRouter()

@client.post("/", response_model=ClientResponse)
async def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    db_client = Client(**client.dict())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

@client.get("/", response_model=List[ClientResponse])
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

@client.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@client.get("/{client_id}/guards")
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

@client.put("/{client_id}", response_model=ClientResponse)
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

@client.delete("/{client_id}")
async def delete_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    db.delete(client)
    db.commit()
    return {"message": "Client deleted successfully"}
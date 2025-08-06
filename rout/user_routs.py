from fastapi import  APIRouter, HTTPException,Depends 
from models.auth import User
from utils.pydantic_model import UserResponse,UserCreate,Token,LoginRequest
from utils.util import hash_password, verify_password,create_access_token,get_db
from datetime import timedelta
from dotenv import load_dotenv
from sqlalchemy.orm import  Session 
import os

load_dotenv()

ACCESS_TOKEN_EXPIRE_MINUTES= int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES",120))




auth= APIRouter()



@auth.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if user already exists
        if db.query(User).filter(User.username == user.username).first():
            raise HTTPException(status_code=400, detail="Username already registered")
        if db.query(User).filter(User.email == user.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user
        hashed_password = hash_password(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return UserResponse(
            id=str(db_user.id),
            username=db_user.username,
            email=db_user.email,
            is_active=db_user.is_active,
            created_at=db_user.created_at
        )
    except Exception as e:
        print("error in register user",e)
        raise HTTPException(status_code=500, detail="Failed to register user")

@auth.post("/login", response_model=Token)
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == data.email).first()
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Incorrect email or password")

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer", "data": {"user_id": str(user.id)}}
    except Exception as e:
        print("error in login user", e)
        raise HTTPException(status_code=500, detail="user login failed")
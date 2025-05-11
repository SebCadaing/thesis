from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from passlib.context import CryptContext
from database import SessionLocal
import models

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Schemas
class SignupData(BaseModel):
    username: str
    email: str
    password: str
    role: str  # "student" or "teacher"

class LoginData(BaseModel):
    username: str
    password: str
    role: str

# /signup route
@router.post("/signup")
def signup(data: SignupData, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = pwd_context.hash(data.password)
    new_user = models.User(
        username=data.username,
        email=data.email,
        role=data.role,
        password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"access_token": new_user.id, "message": "Signup successful"}

# /login route
@router.post("/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == data.username, models.User.role == data.role).first()
    if not user or not pwd_context.verify(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {"access_token": user.id, "message": "Login successful"}

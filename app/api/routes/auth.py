from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import timedelta
from app.core.auth import verify_password, hash_password, create_access_token

router = APIRouter()

# 示例用户数据库（仅供演示）
fake_users_db = {
    "test@example.com": {
        "username": "test",
        "email": "test@example.com",
        "hashed_password": hash_password("testpassword"),
    }
}

class UserLogin(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

@router.post("/login")
async def login(user: UserLogin):
    user_data = fake_users_db.get(user.email)
    if not user_data or not verify_password(user.password, user_data["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register")
async def register(user: UserCreate):
    if user.email in fake_users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = hash_password(user.password)
    fake_users_db[user.email] = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_password,
    }
    return {"message": "User registered successfully"}

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import jwt
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database.database import get_db
from database.models import User, Memory, MatchLog, SharedMemory
from auth.jwt import create_access_token, get_current_user
from schemas.memory import MemoryCreate, MemoryResponse
from schemas.user import UserCreate, UserResponse
from database.supabase import supabase

load_dotenv()

app = FastAPI(title="Cloud LLM API")

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT ayarları
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class Memory(BaseModel):
    prompt: str
    response: str
    intent: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: Optional[int] = 1
    usage_count: Optional[int] = 0
    context_message: Optional[str] = None
    category: Optional[str] = None

# Kullanıcı işlemleri
@app.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=user.password  # Gerçek uygulamada hash'lenecek
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token")
async def login_for_access_token(email: str, password: str):
    """Kullanıcı girişi ve token oluşturma"""
    try:
        result = await supabase.sign_in(email, password)
        if not result["success"]:
            raise HTTPException(status_code=401, detail="Geçersiz kimlik bilgileri")
        
        # Token oluştur
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = jwt.encode(
            {
                "sub": result["session"].user.id,
                "exp": datetime.utcnow() + access_token_expires
            },
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Memory işlemleri
@app.post("/memories/")
async def create_memory(memory: Memory, token: str = Depends(oauth2_scheme)):
    """Yeni hafıza kaydı oluştur"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload["sub"]
        
        result = await supabase.create_memory(memory.dict(), user_id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result["data"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memories/")
async def get_memories(token: str = Depends(oauth2_scheme)):
    """Kullanıcının hafıza kayıtlarını getir"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload["sub"]
        
        result = await supabase.get_memories(user_id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result["data"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/memories/{memory_id}")
async def update_memory(memory_id: int, memory: Memory, token: str = Depends(oauth2_scheme)):
    """Hafıza kaydını güncelle"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload["sub"]
        
        result = await supabase.update_memory(memory_id, memory.dict(), user_id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result["data"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memories/{memory_id}")
async def delete_memory(memory_id: int, token: str = Depends(oauth2_scheme)):
    """Hafıza kaydını sil"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload["sub"]
        
        result = await supabase.delete_memory(memory_id, user_id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {"message": "Kayıt başarıyla silindi"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Paylaşım işlemleri
@app.post("/memories/{memory_id}/share/{user_id}")
async def share_memory(
    memory_id: int,
    user_id: int,
    can_edit: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    memory = db.query(Memory).filter(
        Memory.id == memory_id,
        Memory.owner_id == current_user.id
    ).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    shared_user = db.query(User).filter(User.id == user_id).first()
    if not shared_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    shared_memory = SharedMemory(
        memory_id=memory_id,
        shared_with_id=user_id,
        can_edit=1 if can_edit else 0
    )
    db.add(shared_memory)
    db.commit()
    
    return {"message": "Memory shared successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
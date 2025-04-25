from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    memories = relationship("Memory", back_populates="owner")

class Memory(Base):
    __tablename__ = "memories"
    
    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(String)
    response = Column(String)
    intent = Column(String, index=True)
    tags = Column(JSON)
    priority = Column(Integer, default=1)
    usage_count = Column(Integer, default=0)
    context_message = Column(String, nullable=True)
    category = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="memories")
    embedding = Column(JSON, nullable=True)  # Vektör gömme için
    similarity_score = Column(Float, nullable=True)  # Benzerlik skoru için

class MatchLog(Base):
    __tablename__ = "match_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, ForeignKey("memories.id"))
    matched_input = Column(String)
    similarity_score = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    
class SharedMemory(Base):
    __tablename__ = "shared_memories"
    
    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, ForeignKey("memories.id"))
    shared_with_id = Column(Integer, ForeignKey("users.id"))
    can_edit = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow) 
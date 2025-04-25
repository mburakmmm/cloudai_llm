from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MemoryBase(BaseModel):
    prompt: str
    response: str
    intent: str
    tags: List[str] = []
    priority: int = 1
    context_message: Optional[str] = None
    category: Optional[str] = None

class MemoryCreate(MemoryBase):
    pass

class MemoryResponse(MemoryBase):
    id: int
    owner_id: int
    created_at: datetime
    usage_count: int = 0
    similarity_score: Optional[float] = None

    class Config:
        from_attributes = True 
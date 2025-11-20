from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    is_admin: bool = False
    rate_limit: int = 100

class UserResponse(BaseModel):
    username: str
    is_admin: bool
    created_at: Optional[float] = None
    last_used: Optional[float] = None
    rate_limit: int
    is_active: bool

class APIKeyResponse(BaseModel):
    username: str
    api_key: str
    message: str

class UserUpdate(BaseModel):
    is_admin: Optional[bool] = None
    rate_limit: Optional[int] = None
    is_active: Optional[bool] = None
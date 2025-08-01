from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import uuid4

class User(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex, alias="_id")
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: Optional[str] = Field(None, description="Password")
    is_deleted: Optional[bool] = Field(default=False, description="Whether the user is soft-deleted")
    is_2fa_enabled: Optional[bool] = Field(default=False, description="Whether 2FA is enabled for the user")
    
    class Config:
        populate_by_name = True  # Allows populating by alias, e.g., both '_id' and 'id'
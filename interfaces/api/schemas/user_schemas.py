from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserBase(BaseModel):
    """Base user schema with common fields"""
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="Email address")

class UserCreate(UserBase):
    """Schema for user creation"""
    password: str = Field(..., description="Password")

class UserResponse(UserBase):
    """Schema for user response data"""
    id: str = Field(..., alias="_id", description="User ID")
    is_deleted: bool = Field(default=False, description="Whether the user is soft-deleted")
    is_2fa_enabled: bool = Field(default=False, description="Whether 2FA is enabled for the user")
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    """Schema for user updates"""
    username: Optional[str] = Field(None, description="Username")
    email: Optional[EmailStr] = Field(None, description="Email address")
    password: Optional[str] = Field(None, description="Password")
    is_deleted: Optional[bool] = Field(None, description="Whether the user is soft-deleted")
    is_2fa_enabled: Optional[bool] = Field(None, description="Whether 2FA is enabled for the user")

class UserPreferences(BaseModel):
    """Schema for user preferences"""
    id: Optional[str] = Field(None, description="Preferences ID")
    user_id: Optional[str] = Field(None, description="User ID")
    username: Optional[str] = Field(None, description="Username")
    units: Optional[str] = Field('metric', description="Temperature units: metric, imperial, or standard")
    theme: Optional[str] = Field('auto', description="UI theme: auto, light, or dark")
    defaultLocation: Optional[str] = Field('', description="Default location for weather forecasts")
    
    class Config:
        from_attributes = True

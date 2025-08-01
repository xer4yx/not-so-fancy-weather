from pydantic import BaseModel, Field
from typing import Optional
from uuid import uuid4

class Preferences(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex, alias="_id")
    user_id: str = Field(..., description="The ID of the user these preferences belong to")
    username: str = Field(..., description="The username of the user these preferences belong to")
    units: str = Field(default="metric", description="Temperature units: metric, imperial, or standard")
    theme: str = Field(default="auto", description="UI theme: auto, light, or dark")
    defaultLocation: str = Field(default="", description="Default location for weather forecasts")
    
    class Config:
        populate_by_name = True  # Allows populating by alias, e.g., both '_id' and 'id' 
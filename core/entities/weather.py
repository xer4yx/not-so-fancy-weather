from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class Weather(BaseModel):
    id: Optional[str] = None
    city_id: int
    city_name: str
    coordinates: Dict[str, float]  # {"lat": float, "lon": float}
    weather_data: Dict[str, Any]  # Store the relevant weather forecast data
    date_from: Optional[datetime] = None  # Start date for the forecast period
    date_to: Optional[datetime] = None  # End date for the forecast period
    user_id: Optional[str] = None  # ID of the user who requested this weather data
    temperature_data: Optional[Dict[str, Any]] = None  # Extracted temperature data for the specific date range
    created_at: datetime = Field(default=datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    } 
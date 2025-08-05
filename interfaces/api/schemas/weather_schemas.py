from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime, date


class DateRangeFilter(BaseModel):
    date_from: datetime
    date_to: datetime
    
    @validator('date_to')
    def validate_date_range(cls, v, values):
        if 'date_from' in values and v < values['date_from']:
            raise ValueError("End date must be after start date")
        return v


class LocationIdentifier(BaseModel):
    city_name: Optional[str] = None
    city_id: Optional[int] = None
    coordinates: Optional[Dict[str, float]] = None
    fuzzy_search: Optional[bool] = Field(default=False, description="Enable fuzzy matching for city names")
    
    @validator('coordinates')
    def validate_coordinates(cls, v):
        if v is None:
            return v
            
        if not all(key in v for key in ['lat', 'lon']):
            raise ValueError("Coordinates must contain 'lat' and 'lon' keys")
        
        if not (-90 <= v['lat'] <= 90) or not (-180 <= v['lon'] <= 180):
            raise ValueError("Invalid latitude or longitude values")
        
        return v
        
    @validator('*')
    def validate_at_least_one_field(cls, v, values, **kwargs):
        field = kwargs.get('field')
        if field == 'city_name' and v is None and values.get('city_id') is None and values.get('coordinates') is None:
            raise ValueError("At least one location identifier (city_name, city_id, or coordinates) must be provided")
        return v


class WeatherDataCreate(BaseModel):
    city_id: int
    city_name: str
    coordinates: Dict[str, float]  # {"lat": float, "lon": float}
    weather_data: Dict[str, Any]
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    user_id: Optional[str] = None
    temperature_data: Optional[Dict[str, Any]] = None
    
    @validator('coordinates')
    def validate_coordinates(cls, v):
        if not all(key in v for key in ['lat', 'lon']):
            raise ValueError("Coordinates must contain 'lat' and 'lon' keys")
        
        if not (-90 <= v['lat'] <= 90) or not (-180 <= v['lon'] <= 180):
            raise ValueError("Invalid latitude or longitude values")
        
        return v
    
    @validator('date_to')
    def validate_date_range(cls, v, values):
        if v is None:
            return v
        if 'date_from' in values and values['date_from'] is not None and v < values['date_from']:
            raise ValueError("End date must be after start date")
        return v
    
    @validator('weather_data')
    def validate_weather_data(cls, v):
        # Ensure we have at least the essential weather data fields
        required_keys = ['main', 'description', 'temp', 'humidity', 'wind_speed']
        
        # Check if we have top-level keys or nested under specific structure
        if 'main' in v and isinstance(v['main'], dict):
            # OpenWeatherMap format
            if not all(key in v['main'] for key in ['temp', 'humidity']):
                raise ValueError("Missing required weather data fields in 'main' object")
            
            if 'wind' not in v or not isinstance(v['wind'], dict) or 'speed' not in v['wind']:
                raise ValueError("Missing wind speed data")
                
            if 'weather' not in v or not isinstance(v['weather'], list) or not v['weather']:
                raise ValueError("Missing weather description data")
        else:
            # Simplified format
            missing_keys = [key for key in required_keys if key not in v]
            if missing_keys:
                raise ValueError(f"Missing required weather data fields: {', '.join(missing_keys)}")
        
        return v


class WeatherDataUpdate(BaseModel):
    city_name: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None  # {"lat": float, "lon": float}
    weather_data: Optional[Dict[str, Any]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    temperature_data: Optional[Dict[str, Any]] = None
    
    @validator('coordinates')
    def validate_coordinates(cls, v):
        if v is None:
            return v
            
        if not all(key in v for key in ['lat', 'lon']):
            raise ValueError("Coordinates must contain 'lat' and 'lon' keys")
        
        if not (-90 <= v['lat'] <= 90) or not (-180 <= v['lon'] <= 180):
            raise ValueError("Invalid latitude or longitude values")
        
        return v
    
    @validator('date_to')
    def validate_date_range(cls, v, values):
        if v is None:
            return v
        if 'date_from' in values and values['date_from'] is not None and v < values['date_from']:
            raise ValueError("End date must be after start date")
        return v
    
    @validator('weather_data')
    def validate_weather_data(cls, v):
        if v is None:
            return v
            
        # Same validation as in WeatherDataCreate
        required_keys = ['main', 'description', 'temp', 'humidity', 'wind_speed']
        
        if 'main' in v and isinstance(v['main'], dict):
            # OpenWeatherMap format
            if not all(key in v['main'] for key in ['temp', 'humidity']):
                raise ValueError("Missing required weather data fields in 'main' object")
            
            if 'wind' not in v or not isinstance(v['wind'], dict) or 'speed' not in v['wind']:
                raise ValueError("Missing wind speed data")
                
            if 'weather' not in v or not isinstance(v['weather'], list) or not v['weather']:
                raise ValueError("Missing weather description data")
        else:
            # Simplified format
            missing_keys = [key for key in required_keys if key not in v]
            if missing_keys:
                raise ValueError(f"Missing required weather data fields: {', '.join(missing_keys)}")
        
        return v


class WeatherDataResponse(BaseModel):
    id: str
    city_id: int
    city_name: str
    coordinates: Dict[str, float]
    weather_data: Dict[str, Any]
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    user_id: Optional[str] = None
    temperature_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class TemperatureQueryParams(BaseModel):
    location: LocationIdentifier
    date_range: DateRangeFilter 
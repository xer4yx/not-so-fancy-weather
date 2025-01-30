from typing import Optional, Dict, Any
import requests
from requests.exceptions import RequestException

from core.interface import ApiInterface
from utils.configs import NSFWApiSettings

api_settings = NSFWApiSettings()

# TODO: Add optional paramaters where user can query either
# using zip/postal, gps coords (long & lat), town, or city
class OpenWeatherApi(ApiInterface):
    """OpenWeatherMap API"""
    def __init__(self):
        self.settings = NSFWApiSettings()
    
    def call(
        self, 
        lat: Optional[float] = None, 
        lon: Optional[float] = None,
        zip_code: Optional[str] = None,
        city_name: Optional[str] = None,
        city_id: Optional[int] = None) -> Dict[str, Any]: 
        """Calls the API returning JSON serializable data."""
        
        params = {"appid": self.settings.OPENWEATHER_API_KEY}
        
        if lat and lon:
            params["lat"] = lat
            params["lon"] = lon
        elif zip_code:
            params["zip"] = zip_code
        elif city_name:
            params["q"] = city_name
        elif city_id:
            params["id"] = city_id
        else:
            raise ValueError("Must provide lat & lon coordinates")
        
        response = requests.get(
            url=f"https://api.openweathermap.org/data/2.5/forecast",
            params=params
        )
        
        if response.status_code != 200:
            raise RequestException(f"API request failed with status code: {response.status_code}")
        
        return response.json()
from typing import Optional, Dict, Any
import requests
from requests.exceptions import RequestException

from utils.configs import NSFWApiSettings

api_settings = NSFWApiSettings()

# TODO: Add optional paramaters where user can query either
# using zip/postal, gps coords (long & lat), town, or city
def call_api(lat: float, lon: float) -> Dict[str, Any]:
    response = requests.get(
        url=f"https://api.openweathermap.org/data/2.5/forecast",
        params={
            "lat": lat,
            "lon": lon,
            "appid": api_settings.OPENWEATHER_API_KEY
        }
    )
    
    if response.status_code != 200:
        raise RequestException(f"API request failed with status code: {response.status_code}")
    
    return response.json()
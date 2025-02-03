from typing import Annotated, Optional
import pydantic

from fastapi import APIRouter, Depends, Query, Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.interface import ApiInterface
from infrastructure.api import get_weather_api

weather_router = APIRouter(prefix="/weather", tags=["weather"])
request_limiter = Limiter(key_func=get_remote_address)  

# FIXME: Query raises internal server error on /docs
@weather_router.get(path="/forecast")
@request_limiter.limit("60/minute")
async def get_forecast(
    request: Request,
    api: Annotated[ApiInterface, Depends(get_weather_api)],
    lat: Annotated[Optional[float], Query(description="Latitude")] = None,
    lon: Annotated[Optional[float], Query(description="Longitude")] = None,
    zip_code: Annotated[Optional[str], Query(description="Zip Code")] = None, 
    city_name: Annotated[Optional[str], Query(description="City Name")] = None,
    city_id: Annotated[Optional[int], Query(description="City ID")] = None):
    try:
        return api.call(
            lat=lat, 
            lon=lon, 
            zip_code=zip_code, 
            city_name=city_name, 
            city_id=city_id)
    except pydantic.errors.PydanticUserError as query_error:
        raise
    except Exception as base_error:
        raise

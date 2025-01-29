from typing import Annotated
import pydantic
from fastapi import APIRouter, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from infrastructure.api import call_api

weather_router = APIRouter(prefix="/weather", tags=["weather"])
request_limiter = Limiter(key_func=get_remote_address)  

# FIXME: Query raises internal server error on /docs
@weather_router.get(path="/forecast")
@request_limiter.limit("60/minute")
async def get_forecast_now(   
    request: Request,
    lat: Annotated[float, Query(..., description="Latitude")],
    lon: Annotated[float, Query(..., description="Longitude")]
):
    try:
        return call_api(lat=lat, lon=lon)
    except pydantic.errors.PydanticUserError as query_error:
        raise
    except Exception as base_error:
        raise

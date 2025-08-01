from typing import Annotated, Optional, List
import pydantic
import logging
from fastapi import APIRouter, Depends, Query, Request, Response, HTTPException, status, Path, Body
from slowapi import Limiter
from slowapi.util import get_remote_address
from bson.errors import InvalidId
from bson.objectid import ObjectId
from datetime import datetime

from core.interface import ApiInterface
from core.services import WeatherService
from infrastructure.api import get_weather_api
from interfaces.api.di.services import get_weather_service
from interfaces.api.schemas import WeatherDataCreate, WeatherDataUpdate, WeatherDataResponse
from interfaces.api.schemas.weather_schemas import DateRangeFilter, LocationIdentifier, TemperatureQueryParams

# Configure logger
logger = logging.getLogger(__name__)

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
    city_id: Annotated[Optional[int], Query(description="City ID")] = None,
    fuzzy_search: Annotated[bool, Query(description="Enable fuzzy matching for city names")] = False):
    
    # Log request parameters (excluding None values)
    params = {
        "lat": lat,
        "lon": lon,
        "zip_code": zip_code,
        "city_name": city_name,
        "city_id": city_id,
        "fuzzy_search": fuzzy_search
    }
    request_params = {k: v for k, v in params.items() if v is not None}
    
    logger.info(f"Weather forecast request with params: {request_params}")
    
    # Validate that at least one parameter is provided
    if not any([lat, lon, zip_code, city_name, city_id]):
        logger.warning("Weather forecast request rejected: No location parameters provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one location parameter (lat/lon, zip_code, city_name, or city_id) must be provided"
        )
    
    try:
        result = api.call(
            lat=lat, 
            lon=lon, 
            zip_code=zip_code, 
            city_name=city_name, 
            city_id=city_id)
        
        logger.info(f"Weather forecast successfully retrieved for {request_params}")
        return result
    except pydantic.errors.PydanticUserError as query_error:
        logger.error(f"Validation error in weather forecast request: {str(query_error)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request parameters: {str(query_error)}"
        )
    except ValueError as value_error:
        logger.error(f"Value error in weather forecast request: {str(value_error)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(value_error)
        )
    except Exception as base_error:
        logger.error(f"Error retrieving weather forecast: {str(base_error)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve weather forecast. Please try again later."
        )


@weather_router.post(path="/forecast/save", response_model=WeatherDataResponse, status_code=status.HTTP_201_CREATED)
async def save_forecast_to_db(
    request: Request,
    api: Annotated[ApiInterface, Depends(get_weather_api)],
    service: Annotated[WeatherService, Depends(get_weather_service)],
    lat: Annotated[Optional[float], Query(description="Latitude")] = None,
    lon: Annotated[Optional[float], Query(description="Longitude")] = None,
    zip_code: Annotated[Optional[str], Query(description="Zip Code")] = None, 
    city_name: Annotated[Optional[str], Query(description="City Name")] = None,
    city_id: Annotated[Optional[int], Query(description="City ID")] = None,
    date_from: Annotated[Optional[datetime], Query(description="Start date for forecast")] = None,
    date_to: Annotated[Optional[datetime], Query(description="End date for forecast")] = None,
    user_id: Annotated[Optional[str], Query(description="ID of the user requesting the forecast")] = None,
    fuzzy_search: Annotated[bool, Query(description="Enable fuzzy matching for city names")] = False
):
    """Fetch weather forecast and save it to the database"""
    try:
        # Log request parameters (excluding None values)
        params = {
            "lat": lat,
            "lon": lon,
            "zip_code": zip_code,
            "city_name": city_name,
            "city_id": city_id,
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
            "user_id": user_id,
            "fuzzy_search": fuzzy_search
        }
        request_params = {k: v for k, v in params.items() if v is not None}
        
        logger.info(f"Weather forecast save request with params: {request_params}")
        
        # Validate that at least one location parameter is provided
        if not any([lat, lon, zip_code, city_name, city_id]):
            logger.warning("Weather forecast save request rejected: No location parameters provided")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one location parameter (lat/lon, zip_code, city_name, or city_id) must be provided"
            )
        
        # Validate date range if provided
        if date_from and date_to and date_from > date_to:
            raise ValueError("End date must be after start date")
        
        # Get forecast from API
        forecast_data = api.call(
            lat=lat, 
            lon=lon, 
            zip_code=zip_code, 
            city_name=city_name, 
            city_id=city_id
        )
        
        # Extract the city information
        try:
            city_data = forecast_data.get("city", {})
            actual_city_id = city_data.get("id")
            actual_city_name = city_data.get("name")
            coordinates = city_data.get("coord", {})
            
            # Validate critical data
            if not actual_city_id or not actual_city_name:
                raise ValueError("Missing city information in weather data")
                
            if not coordinates or not all(k in coordinates for k in ["lat", "lon"]):
                raise ValueError("Missing coordinates in weather data")
                
            # Create a weather data record
            weather_create_data = {
                "city_id": actual_city_id,
                "city_name": actual_city_name,
                "coordinates": coordinates,
                "weather_data": forecast_data,
                "date_from": date_from,
                "date_to": date_to,
                "user_id": user_id
            }
            
            # Check if data already exists for this city
            existing_data = service.get_weather_data_by_city_id(actual_city_id)
            
            if existing_data:
                # Update existing record
                record_id = existing_data.get("id")
                update_data = {
                    "coordinates": coordinates,
                    "city_name": actual_city_name,
                    "weather_data": forecast_data,
                    "updated_at": datetime.utcnow()
                }
                
                # Only update date range and user_id if provided
                if date_from:
                    update_data["date_from"] = date_from
                if date_to:
                    update_data["date_to"] = date_to
                if user_id:
                    update_data["user_id"] = user_id
                
                service.update_weather_data(record_id, update_data)
                
                # Get updated data
                updated_data = service.get_weather_data(record_id)
                logger.info(f"Updated weather data for city ID: {actual_city_id}, record ID: {record_id}")
                
                return updated_data
            else:
                # Create new record
                record_id = service.create_weather_data(weather_create_data)
                
                # Get created data
                created_data = service.get_weather_data(record_id)
                if not created_data:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Weather data was created but could not be retrieved"
                    )
                
                # Include the ID in the response
                created_data["id"] = record_id
                
                logger.info(f"Created weather data for city ID: {actual_city_id}, record ID: {record_id}")
                return created_data
                
        except (KeyError, ValueError) as e:
            logger.error(f"Error processing forecast data: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Error processing forecast data: {str(e)}"
            )
    except pydantic.errors.PydanticUserError as query_error:
        logger.error(f"Validation error in forecast save request: {str(query_error)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request parameters: {str(query_error)}"
        )
    except ValueError as value_error:
        logger.error(f"Value error in forecast save request: {str(value_error)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(value_error)
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error saving forecast to database: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save forecast data to database"
        )


# Weather data CRUD operations
@weather_router.post(path="/data", response_model=WeatherDataResponse, status_code=status.HTTP_201_CREATED)
async def create_weather_data(
    request: Request,
    weather_data: WeatherDataCreate,
    service: Annotated[WeatherService, Depends(get_weather_service)]
):
    """Create a new weather data record in the database"""
    try:
        # Create weather data record
        record_id = service.create_weather_data(weather_data.model_dump())
        
        # Retrieve the created record to return
        created_record = service.get_weather_data(record_id)
        if not created_record:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Weather data was created but could not be retrieved"
            )
        
        # Include the ID in the response
        created_record["id"] = record_id
        
        logger.info(f"Weather data created with ID: {record_id}")
        return created_record
    except pydantic.ValidationError as val_error:
        logger.error(f"Validation error creating weather data: {str(val_error)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid weather data: {str(val_error)}"
        )
    except ValueError as value_error:
        logger.error(f"Value error creating weather data: {str(value_error)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(value_error)
        )
    except Exception as e:
        logger.error(f"Error creating weather data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create weather data record"
        )


@weather_router.get(path="/data/search", response_model=List[WeatherDataResponse])
async def search_weather_data(
    request: Request,
    service: Annotated[WeatherService, Depends(get_weather_service)],
    city_name: Annotated[str, Query(description="City name to search for")],
    fuzzy_search: Annotated[bool, Query(description="Enable fuzzy matching for city names")] = False
):
    """Search for weather data by city name with optional fuzzy matching"""
    try:
        # Search by city name
        results = service.get_weather_data_by_city_name(city_name, fuzzy_search)
        
        if not results:
            logger.warning(f"No weather data found for city name: {city_name}, fuzzy: {fuzzy_search}")
            # Return empty list instead of 404 for collection endpoints
            return []
        
        logger.info(f"Found {len(results)} weather data records for city name: {city_name}, fuzzy: {fuzzy_search}")
        return results
    except Exception as e:
        logger.error(f"Error searching weather data by city name: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search weather data"
        )


@weather_router.get(path="/data/temperature")
async def get_temperature_data(
    request: Request,
    service: Annotated[WeatherService, Depends(get_weather_service)],
    date_from: Annotated[datetime, Query(description="Start date for temperature data")],
    date_to: Annotated[datetime, Query(description="End date for temperature data")],
    city_id: Annotated[Optional[int], Query(description="City ID")] = None,
    city_name: Annotated[Optional[str], Query(description="City name")] = None,
    lat: Annotated[Optional[float], Query(description="Latitude")] = None,
    lon: Annotated[Optional[float], Query(description="Longitude")] = None,
    fuzzy_search: Annotated[bool, Query(description="Enable fuzzy matching for city names")] = False
):
    """Get temperature data for a location within a date range"""
    try:
        # Validate date range
        if date_from > date_to:
            raise ValueError("End date must be after start date")
            
        # Validate that at least one location parameter is provided
        if not any([city_id, city_name, (lat is not None and lon is not None)]):
            logger.warning("Temperature data request rejected: No location parameters provided")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one location parameter (city_id, city_name, or lat/lon) must be provided"
            )
            
        # Prepare coordinates if provided
        coordinates = None
        if lat is not None and lon is not None:
            coordinates = {"lat": lat, "lon": lon}
            
        # Log request parameters
        params = {
            "city_id": city_id,
            "city_name": city_name,
            "coordinates": coordinates,
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "fuzzy_search": fuzzy_search
        }
        request_params = {k: v for k, v in params.items() if v is not None}
        logger.info(f"Temperature data request with params: {request_params}")
        
        # Search by location and date range
        results = []
        
        if city_id is not None:
            # Search by city ID
            results = service.get_weather_data_by_date_range(
                date_from=date_from,
                date_to=date_to,
                city_id=city_id
            )
        elif city_name is not None:
            # Search by city name
            results = service.get_weather_data_by_date_range(
                date_from=date_from,
                date_to=date_to,
                city_name=city_name,
                fuzzy_search=fuzzy_search
            )
            
        if not results:
            logger.warning(f"No temperature data found for the specified parameters")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No temperature data found for the specified location and date range"
            )
            
        # Return temperature data from the first matching result
        return {
            "location": {
                "city_id": results[0]["city_id"],
                "city_name": results[0]["city_name"],
                "coordinates": results[0]["coordinates"]
            },
            "date_range": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat()
            },
            "temperature_data": results[0]["temperature_data"]
        }
    except ValueError as value_error:
        logger.error(f"Value error in temperature data request: {str(value_error)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(value_error)
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving temperature data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve temperature data"
        )


@weather_router.get(path="/data/city/{city_id}", response_model=WeatherDataResponse)
async def get_weather_data_by_city_id(
    request: Request,
    city_id: Annotated[int, Path(description="City ID")],
    service: Annotated[WeatherService, Depends(get_weather_service)]
):
    """Retrieve a weather data record by city ID"""
    try:
        # Get weather data
        weather_data = service.get_weather_data_by_city_id(city_id)
        
        if not weather_data:
            logger.warning(f"Weather data not found for city ID: {city_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Weather data not found for this city"
            )
        
        return weather_data
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving weather data for city ID {city_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve weather data"
        )


@weather_router.get(path="/data", response_model=List[WeatherDataResponse])
async def get_all_weather_data(
    request: Request,
    service: Annotated[WeatherService, Depends(get_weather_service)]
):
    """Retrieve all weather data records"""
    try:
        # Get all weather data
        weather_data_list = service.get_all_weather_data()
        
        if not weather_data_list:
            # Return empty list instead of 404 for collection endpoints
            return []
        
        return weather_data_list
    except Exception as e:
        logger.error(f"Error retrieving all weather data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve weather data"
        )


# Modify the record_id route to use a regex pattern
@weather_router.get(path="/data/{record_id:str}", response_model=WeatherDataResponse)
async def get_weather_data_by_id(
    request: Request,
    record_id: Annotated[str, Path(description="Weather data record ID")],
    service: Annotated[WeatherService, Depends(get_weather_service)]
):
    """Retrieve a weather data record by ID"""
    try:
        # Validate ObjectId format
        try:
            ObjectId(record_id)
        except InvalidId:
            logger.warning(f"Invalid record ID format: {record_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid record ID format"
            )
        
        # Get weather data
        weather_data = service.get_weather_data(record_id)
        
        if not weather_data:
            logger.warning(f"Weather data not found for ID: {record_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Weather data not found"
            )
        
        # Include the ID in the response
        weather_data["id"] = record_id
        
        return weather_data
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving weather data for ID {record_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve weather data"
        )


@weather_router.put(path="/data/{record_id:str}", response_model=WeatherDataResponse)
async def update_weather_data(
    request: Request,
    record_id: Annotated[str, Path(description="Weather data record ID")],
    update_data: WeatherDataUpdate,
    service: Annotated[WeatherService, Depends(get_weather_service)]
):
    """Update a weather data record by ID"""
    try:
        # Validate ObjectId format
        try:
            ObjectId(record_id)
        except InvalidId:
            logger.warning(f"Invalid record ID format: {record_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid record ID format"
            )
        
        # Check if record exists
        existing_data = service.get_weather_data(record_id)
        if not existing_data:
            logger.warning(f"Weather data not found for ID: {record_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Weather data not found"
            )
        
        # Only update non-None fields
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        
        if not update_dict:
            # Nothing to update
            existing_data["id"] = record_id
            return existing_data
        
        # Update weather data
        service.update_weather_data(record_id, update_dict)
        
        # Get updated data
        updated_data = service.get_weather_data(record_id)
        if not updated_data:
            # This should not happen but handle it just in case
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Weather data was updated but could not be retrieved"
            )
        
        # Include the ID in the response
        updated_data["id"] = record_id
        
        return updated_data
    except pydantic.ValidationError as val_error:
        logger.error(f"Validation error updating weather data: {str(val_error)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid weather data: {str(val_error)}"
        )
    except ValueError as value_error:
        logger.error(f"Value error updating weather data: {str(value_error)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(value_error)
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error updating weather data for ID {record_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update weather data"
        )


@weather_router.delete(path="/data/{record_id:str}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_weather_data(
    request: Request,
    record_id: Annotated[str, Path(description="Weather data record ID")],
    service: Annotated[WeatherService, Depends(get_weather_service)]
):
    """Delete a weather data record by ID"""
    try:
        # Validate ObjectId format
        try:
            ObjectId(record_id)
        except InvalidId:
            logger.warning(f"Invalid record ID format: {record_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid record ID format"
            )
        
        # Check if record exists
        existing_data = service.get_weather_data(record_id)
        if not existing_data:
            logger.warning(f"Weather data not found for ID: {record_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Weather data not found"
            )
        
        # Delete weather data
        result = service.delete_weather_data(record_id)
        
        if not result:
            # This should not happen since we checked existence above
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete weather data"
            )
        
        # Return 204 No Content (handled by status_code decorator)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error deleting weather data for ID {record_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete weather data"
        )


@weather_router.post(path="/forecast/date-range")
async def get_forecast_by_date_range(
    request: Request,
    api: Annotated[ApiInterface, Depends(get_weather_api)],
    service: Annotated[WeatherService, Depends(get_weather_service)],
    params: Annotated[TemperatureQueryParams, Body(description="Location and date range parameters")]
):
    """Get weather forecast for a specific location and date range"""
    try:
        # Extract parameters
        location = params.location
        date_range = params.date_range
        
        # Log request
        logger.info(
            f"Weather forecast date range request: {location.model_dump()} - "
            f"From: {date_range.date_from.isoformat()} To: {date_range.date_to.isoformat()}"
        )
        
        # Check if we already have data for this location and date range
        results = []
        
        if location.city_id is not None:
            # Search by city ID
            results = service.get_weather_data_by_date_range(
                date_from=date_range.date_from,
                date_to=date_range.date_to,
                city_id=location.city_id
            )
        elif location.city_name is not None:
            # Search by city name
            results = service.get_weather_data_by_date_range(
                date_from=date_range.date_from,
                date_to=date_range.date_to,
                city_name=location.city_name,
                fuzzy_search=location.fuzzy_search
            )
        elif location.coordinates is not None:
            # For coordinates, we need to get fresh data as there's no direct DB query
            # This will be saved later if needed
            pass
        
        # If we found data, return it
        if results:
            logger.info(f"Found existing weather data for the requested date range: {len(results)} record(s)")
            # Just return the first matching result's temperature data
            return {
                "location": {
                    "city_id": results[0]["city_id"],
                    "city_name": results[0]["city_name"],
                    "coordinates": results[0]["coordinates"]
                },
                "date_range": {
                    "from": date_range.date_from.isoformat(),
                    "to": date_range.date_to.isoformat()
                },
                "temperature_data": results[0]["temperature_data"]
            }
        
        # If no data found, fetch new data
        api_params = {}
        
        if location.city_id is not None:
            api_params["city_id"] = location.city_id
        elif location.city_name is not None:
            api_params["city_name"] = location.city_name
        elif location.coordinates is not None:
            api_params["lat"] = location.coordinates["lat"]
            api_params["lon"] = location.coordinates["lon"]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one location parameter (city_name, city_id, or coordinates) must be provided"
            )
        
        # Get forecast from API
        forecast_data = api.call(**api_params)
        
        # Extract the city information
        city_data = forecast_data.get("city", {})
        actual_city_id = city_data.get("id")
        actual_city_name = city_data.get("name")
        coordinates = city_data.get("coord", {})
        
        # Validate critical data
        if not actual_city_id or not actual_city_name:
            raise ValueError("Missing city information in weather data")
            
        if not coordinates or not all(k in coordinates for k in ["lat", "lon"]):
            raise ValueError("Missing coordinates in weather data")
        
        # Create a weather data record with date range
        weather_create_data = {
            "city_id": actual_city_id,
            "city_name": actual_city_name,
            "coordinates": coordinates,
            "weather_data": forecast_data,
            "date_from": date_range.date_from,
            "date_to": date_range.date_to
        }
        
        # Save data to database
        record_id = service.create_weather_data(weather_create_data)
        
        # Get created data
        created_data = service.get_weather_data(record_id)
        if not created_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Weather data was created but could not be retrieved"
            )
        
        # Return the temperature data
        return {
            "location": {
                "city_id": created_data["city_id"],
                "city_name": created_data["city_name"],
                "coordinates": created_data["coordinates"]
            },
            "date_range": {
                "from": date_range.date_from.isoformat(),
                "to": date_range.date_to.isoformat()
            },
            "temperature_data": created_data["temperature_data"]
        }
    except ValueError as value_error:
        logger.error(f"Value error in forecast date range request: {str(value_error)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(value_error)
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing forecast date range request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve weather forecast for date range"
        )

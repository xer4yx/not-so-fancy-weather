import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime
from bson.objectid import ObjectId

from main import app
from core.services import WeatherService
from infrastructure.api import OpenWeatherApi
from interfaces.api.routers.weather_router import weather_router, get_weather_api, get_weather_service

client = TestClient(app)
app.include_router(weather_router)

@pytest.fixture
def mock_weather_api():
    weather_api = MagicMock(spec=OpenWeatherApi)
    weather_api.call.return_value = {
        "city": {
            "id": 12345,
            "name": "Test City",
            "coord": {
                "lat": 40.7128,
                "lon": -74.0060
            }
        },
        "list": [
            {
                "dt": 1619631600,
                "main": {
                    "temp": 20.5,
                    "feels_like": 19.8,
                    "temp_min": 18.2,
                    "temp_max": 22.7,
                    "pressure": 1010,
                    "humidity": 65
                },
                "weather": [
                    {
                        "id": 800,
                        "main": "Clear",
                        "description": "clear sky",
                        "icon": "01d"
                    }
                ],
                "wind": {
                    "speed": 3.5,
                    "deg": 120
                }
            }
        ]
    }
    app.dependency_overrides[get_weather_api] = lambda: weather_api
    return weather_api

@pytest.fixture
def mock_weather_service():
    weather_service = MagicMock(spec=WeatherService)
    # Use a valid ObjectId string
    valid_id = "507f1f77bcf86cd799439011"
    
    weather_service.get_weather_data.return_value = {
        "_id": valid_id,
        "id": valid_id,
        "city_id": 12345,
        "city_name": "Test City",
        "coordinates": {
            "lat": 40.7128,
            "lon": -74.0060
        },
        "weather_data": {
            "city": {
                "id": 12345,
                "name": "Test City",
                "coord": {
                    "lat": 40.7128,
                    "lon": -74.0060
                }
            },
            "list": [
                {
                    "dt": 1619631600,
                    "main": {
                        "temp": 20.5,
                        "feels_like": 19.8,
                        "temp_min": 18.2,
                        "temp_max": 22.7,
                        "pressure": 1010,
                        "humidity": 65
                    },
                    "weather": [
                        {
                            "id": 800,
                            "main": "Clear",
                            "description": "clear sky",
                            "icon": "01d"
                        }
                    ],
                    "wind": {
                        "speed": 3.5,
                        "deg": 120
                    }
                }
            ]
        },
        "date_from": datetime(2023, 1, 1).isoformat(),
        "date_to": datetime(2023, 1, 5).isoformat(),
        "created_at": datetime(2023, 1, 1).isoformat(),
        "updated_at": datetime(2023, 1, 1).isoformat(),
        "temperature_data": {
            "hourly": [
                {
                    "timestamp": "2023-01-01T12:00:00",
                    "temp": 20.5,
                    "description": "clear sky"
                }
            ],
            "daily": {
                "2023-01-01": {
                    "temps": [20.5],
                    "min": 18.2,
                    "max": 22.7,
                    "avg": 20.5
                }
            },
            "summary": {
                "min_temp": 18.2,
                "max_temp": 22.7,
                "avg_temp": 20.5
            }
        }
    }
    weather_service.get_weather_data_by_city_id.return_value = None  # Default to not found
    weather_service.create_weather_data.return_value = valid_id
    weather_service.update_weather_data.return_value = valid_id
    weather_service.delete_weather_data.return_value = True
    weather_service.get_all_weather_data.return_value = [
        weather_service.get_weather_data.return_value
    ]
    weather_service.get_weather_data_by_city_name.side_effect = [
        [weather_service.get_weather_data.return_value]
    ]
    weather_service.get_weather_data_by_date_range.side_effect = [
        [weather_service.get_weather_data.return_value]
    ]
    app.dependency_overrides[get_weather_service] = lambda: weather_service
    return weather_service

@pytest.mark.asyncio
async def test_get_forecast(mock_weather_api):
    # Test get forecast endpoint
    response = client.get("/weather/forecast?lat=40.7128&lon=-74.0060")
    
    # Assert response
    assert response.status_code == 200
    forecast = response.json()
    assert forecast["city"]["id"] == 12345
    assert forecast["city"]["name"] == "Test City"
    
    # Verify service calls
    mock_weather_api.call.assert_called_once_with(
        lat=40.7128, 
        lon=-74.0060, 
        zip_code=None, 
        city_name=None, 
        city_id=None
    )

@pytest.mark.asyncio
async def test_get_forecast_missing_params():
    # Test get forecast endpoint with missing parameters
    response = client.get("/weather/forecast")
    
    # Assert response
    assert response.status_code == 400
    assert "At least one location parameter" in response.json()["detail"]

@pytest.mark.asyncio
async def test_save_forecast_to_db(mock_weather_api, mock_weather_service):
    # Test save forecast endpoint
    response = client.post(
        "/weather/forecast/save?city_name=Test%20City&date_from=2023-01-01T00:00:00&date_to=2023-01-05T00:00:00"
    )
    
    # Assert response
    assert response.status_code == 201
    data = response.json()
    assert data["city_id"] == 12345
    assert data["city_name"] == "Test City"
    
    # Verify service calls
    mock_weather_api.call.assert_called_once_with(
        lat=None, 
        lon=None, 
        zip_code=None, 
        city_name="Test City", 
        city_id=None
    )
    mock_weather_service.create_weather_data.assert_called_once()

@pytest.mark.asyncio
async def test_save_forecast_update_existing(mock_weather_api, mock_weather_service):
    # Setup existing data
    mock_weather_service.get_weather_data_by_city_id.return_value = mock_weather_service.get_weather_data.return_value
    # Test save forecast endpoint with existing data
    response = client.post(
        "/weather/forecast/save?city_name=Test%20City&date_from=2023-01-01T00:00:00&date_to=2023-01-05T00:00:00"
    )
    
    # Assert response
    assert response.status_code == 201
    data = response.json()
    assert data["city_id"] == 12345
    assert data["city_name"] == "Test City"
    
    # Verify service calls
    mock_weather_api.call.assert_called_once()
    mock_weather_service.get_weather_data_by_city_id.assert_called_once_with(12345)
    mock_weather_service.update_weather_data.assert_called_once()

@pytest.mark.asyncio
async def test_create_weather_data(mock_weather_service):
    # Test create weather data endpoint
    response = client.post(
        "/weather/data",
        json={
            "city_id": 12345,
            "city_name": "Test City",
            "coordinates": {
                "lat": 40.7128,
                "lon": -74.0060
            },
            "weather_data": {
                "main": {
                    "temp": 20.5,
                    "humidity": 65
                },
                "weather": [
                    {
                        "id": 800,
                        "main": "Clear",
                        "description": "clear sky",
                        "icon": "01d"
                    }
                ],
                "wind": {
                    "speed": 3.5,
                    "deg": 120
                }
            }
        }
    )
    
    # Assert response
    assert response.status_code == 201
    data = response.json()
    assert data["city_id"] == 12345
    assert data["city_name"] == "Test City"
    
    # Verify service calls
    mock_weather_service.create_weather_data.assert_called_once()
    mock_weather_service.get_weather_data.assert_called_once_with("507f1f77bcf86cd799439011")

@pytest.mark.asyncio
async def test_get_weather_data_by_id(mock_weather_service):
    # Valid ObjectId
    valid_id = "507f1f77bcf86cd799439011"
    valid_object_id = ObjectId(valid_id)
        
    # Test get weather data by ID endpoint
    response = client.get(f"/weather/data/{valid_id}")
    
    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["city_id"] == 12345
    assert data["city_name"] == "Test City"
    
    # Verify service calls
    mock_weather_service.get_weather_data.assert_called_once_with(valid_id)

@pytest.mark.asyncio
async def test_get_weather_data_not_found(mock_weather_service):
    # Setup data not found
    mock_weather_service.get_weather_data.return_value = None
    
    # Valid ObjectId for the non-existent record
    valid_id = "507f1f77bcf86cd799439012"
    valid_object_id = ObjectId(valid_id)
    # Test get weather data by ID endpoint with non-existent ID
    response = client.get(f"/weather/data/{valid_id}")
    
    # Assert response
    assert response.status_code == 404
    assert "Weather data not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_weather_data_by_city_id(mock_weather_service):
    # Setup data found
    mock_weather_service.get_weather_data_by_city_id.return_value = mock_weather_service.get_weather_data.return_value
    
    # Test get weather data by city ID endpoint
    response = client.get("/weather/data/city/12345")
    
    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["city_id"] == 12345
    assert data["city_name"] == "Test City"
    
    # Verify service calls
    mock_weather_service.get_weather_data_by_city_id.assert_called_once_with(12345)

@pytest.mark.asyncio
async def test_get_all_weather_data(mock_weather_service):
    # Test get all weather data endpoint
    response = client.get("/weather/data")
    
    # Assert response
    assert response.status_code == 200
    data_list = response.json()
    assert len(data_list) == 1
    assert data_list[0]["city_id"] == 12345
    assert data_list[0]["city_name"] == "Test City"
    
    # Verify service calls
    mock_weather_service.get_all_weather_data.assert_called_once()

@pytest.mark.asyncio
async def test_update_weather_data(mock_weather_service):
    # Valid ObjectId
    valid_id = "507f1f77bcf86cd799439011"
    valid_object_id = ObjectId(valid_id)
        
    # Test update weather data endpoint
    response = client.put(
        f"/weather/data/{valid_id}",
        json={
            "city_name": "Updated City",
        }
    )
    
    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["city_id"] == 12345
    assert data["city_name"] == "Test City"  # From mock, not actually updated
    
    # Verify service calls
    mock_weather_service.get_weather_data.assert_called()
    mock_weather_service.update_weather_data.assert_called_once_with(
        valid_id, 
        {"city_name": "Updated City"}
    )

@pytest.mark.asyncio
async def test_delete_weather_data(mock_weather_service):
    # Valid ObjectId
    valid_id = "507f1f77bcf86cd799439011"
    valid_object_id = ObjectId(valid_id)
        
    # Test delete weather data endpoint
    response = client.delete(f"/weather/data/{valid_id}")
    
    # Assert response
    assert response.status_code == 204
    
    # Verify service calls
    mock_weather_service.get_weather_data.assert_called_once_with(valid_id)
    mock_weather_service.delete_weather_data.assert_called_once_with(valid_id)

@pytest.mark.asyncio
async def test_search_weather_data(mock_weather_service):
    # Test search weather data endpoint
    response = client.get("/weather/data/search?city_name=Test&fuzzy_search=False")
    
    # Assert response
    assert response.status_code == 200
    data_list = response.json()
    assert len(data_list) == 1
    assert data_list[0]["city_name"] == "Test City"
    
    # Verify service calls
    mock_weather_service.get_weather_data_by_city_name.assert_called_once_with("Test", False)

@pytest.mark.asyncio
async def test_get_temperature_data(mock_weather_service):
    # Test get temperature data endpoint
    response = client.get(
        "/weather/data/temperature?date_from=2023-01-01T00:00:00&date_to=2023-01-05T00:00:00&city_id=12345"
    )
    
    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["location"]["city_id"] == 12345
    assert data["location"]["city_name"] == "Test City"
    assert "hourly" in data["temperature_data"]
    assert "daily" in data["temperature_data"]
    assert "summary" in data["temperature_data"]
    
    # Verify service calls
    mock_weather_service.get_weather_data_by_date_range.assert_called_once_with(
        date_from=datetime(2023, 1, 1, 0, 0),
        date_to=datetime(2023, 1, 5, 0, 0),
        city_id=12345
    )

@pytest.mark.asyncio
async def test_get_forecast_by_date_range(mock_weather_api, mock_weather_service):
    # Test get forecast by date range endpoint
    response = client.post(
        "/weather/forecast/date-range",
        json={
            "location": {
                "city_id": 12345
            },
            "date_range": {
                "date_from": "2023-01-01T00:00:00",
                "date_to": "2023-01-05T00:00:00"
            }
        }
    )
    
    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["location"]["city_id"] == 12345
    assert data["location"]["city_name"] == "Test City"
    assert "hourly" in data["temperature_data"]
    assert "daily" in data["temperature_data"]
    assert "summary" in data["temperature_data"]
    
    # Verify service calls
    mock_weather_service.get_weather_data_by_date_range.assert_called_once_with(
        date_from=datetime(2023, 1, 1, 0, 0),
        date_to=datetime(2023, 1, 5, 0, 0),
        city_id=12345
    ) 
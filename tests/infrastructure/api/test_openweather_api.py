import pytest
from unittest.mock import patch, MagicMock
from requests.exceptions import RequestException

from infrastructure.api.openweather_api import OpenWeatherApi

class TestOpenWeatherApi:
    def setup_method(self):
        self.api = OpenWeatherApi()
        self.mock_response = MagicMock()
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {"weather": "sunny"}
    
    @patch("infrastructure.api.openweather_api.requests.get")
    def test_call_with_lat_lon(self, mock_get):
        # Arrange
        mock_get.return_value = self.mock_response
        
        # Act
        result = self.api.call(lat=40.7128, lon=-74.0060)
        
        # Assert
        mock_get.assert_called_once()
        assert "lat" in mock_get.call_args[1]["params"]
        assert "lon" in mock_get.call_args[1]["params"]
        assert mock_get.call_args[1]["params"]["lat"] == 40.7128
        assert mock_get.call_args[1]["params"]["lon"] == -74.0060
        assert result == {"weather": "sunny"}
    
    @patch("infrastructure.api.openweather_api.requests.get")
    def test_call_with_zip_code(self, mock_get):
        # Arrange
        mock_get.return_value = self.mock_response
        
        # Act
        result = self.api.call(zip_code="10001")
        
        # Assert
        mock_get.assert_called_once()
        assert "zip" in mock_get.call_args[1]["params"]
        assert mock_get.call_args[1]["params"]["zip"] == "10001"
        assert result == {"weather": "sunny"}
    
    @patch("infrastructure.api.openweather_api.requests.get")
    def test_call_with_city_name(self, mock_get):
        # Arrange
        mock_get.return_value = self.mock_response
        
        # Act
        result = self.api.call(city_name="New York")
        
        # Assert
        mock_get.assert_called_once()
        assert "q" in mock_get.call_args[1]["params"]
        assert mock_get.call_args[1]["params"]["q"] == "New York"
        assert result == {"weather": "sunny"}
    
    @patch("infrastructure.api.openweather_api.requests.get")
    def test_call_with_city_id(self, mock_get):
        # Arrange
        mock_get.return_value = self.mock_response
        
        # Act
        result = self.api.call(city_id=5128581)
        
        # Assert
        mock_get.assert_called_once()
        assert "id" in mock_get.call_args[1]["params"]
        assert mock_get.call_args[1]["params"]["id"] == 5128581
        assert result == {"weather": "sunny"}
    
    def test_call_with_no_parameters(self):
        # Act & Assert
        with pytest.raises(ValueError, match="Must provide lat & lon coordinates"):
            self.api.call()
    
    @patch("infrastructure.api.openweather_api.requests.get")
    def test_call_api_error(self, mock_get):
        # Arrange
        error_response = MagicMock()
        error_response.status_code = 401
        error_response.url = "https://api.openweathermap.org/data/2.5/forecast"
        error_response.headers = {"Content-Type": "application/json"}
        error_response.text = '{"message": "Invalid API key"}'
        mock_get.return_value = error_response
        
        # Act & Assert
        with pytest.raises(RequestException, match="API request failed with status code: 401"):
            self.api.call(lat=40.7128, lon=-74.0060) 
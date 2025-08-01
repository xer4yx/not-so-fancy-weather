from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import re

from core.entities import Weather
from core.interface import DatabaseRepository
from infrastructure.logger import get_logger


class WeatherService:
    def __init__(self, repository: DatabaseRepository):
        self.repository = repository
        self.logger = get_logger("core.services.weather", "logs/core.log")
        
    def create_weather_data(self, weather_data: Dict[str, Any]) -> str:
        """
        Create a new weather data entry in the database
        
        Args:
            weather_data: A dictionary containing the weather data
            
        Returns:
            The ID of the newly created record
        """
        try:
            # Create a Weather entity
            weather = Weather(**weather_data)
            
            # Extract temperature data if date range is provided
            if weather.date_from and weather.date_to and not weather.temperature_data:
                weather.temperature_data = self._extract_temperature_data(
                    weather.weather_data, weather.date_from, weather.date_to
                )
            
            # Convert to dict for storage
            weather_dict = weather.model_dump()
            # Remove ID if it's None as MongoDB will generate one
            if weather_dict.get('id') is None:
                weather_dict.pop('id', None)
                
            # Create in database
            record_id = self.repository.create(weather_dict)
            
            self.logger.info(
                f"Created weather data for city_id: {weather_data.get('city_id')}",
                extra={
                    "city_id": weather_data.get("city_id"),
                    "city_name": weather_data.get("city_name"),
                    "record_id": record_id
                }
            )
            
            return record_id
        except Exception as e:
            self.logger.error(
                f"Error creating weather data: {str(e)}",
                extra={
                    "error_type": type(e).__name__,
                    "city_id": weather_data.get("city_id", "N/A"),
                    "city_name": weather_data.get("city_name", "N/A")
                },
                exc_info=True
            )
            raise
    
    def get_weather_data(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve weather data by ID
        
        Args:
            record_id: The ID of the weather record to retrieve
            
        Returns:
            The weather data or None if not found
        """
        try:
            data = self.repository.read('_id', record_id)
            if data:
                # Convert MongoDB data to Weather entity
                weather = Weather(**data)
                return weather.model_dump()
            return None
        except Exception as e:
            self.logger.error(
                f"Error retrieving weather data for ID {record_id}: {str(e)}",
                extra={"error_type": type(e).__name__, "record_id": record_id},
                exc_info=True
            )
            raise
    
    def get_weather_data_by_city_id(self, city_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve weather data by city ID
        
        Args:
            city_id: The city ID to find weather data for
            
        Returns:
            The weather data or None if not found
        """
        try:
            data = self.repository.read('city_id', city_id)
            if data:
                # Convert MongoDB data to Weather entity
                weather = Weather(**data)
                return weather.model_dump()
            return None
        except Exception as e:
            self.logger.error(
                f"Error retrieving weather data for city ID {city_id}: {str(e)}",
                extra={"error_type": type(e).__name__, "city_id": city_id},
                exc_info=True
            )
            raise
    
    def get_weather_data_by_city_name(self, city_name: str, fuzzy_search: bool = False) -> List[Dict[str, Any]]:
        """
        Retrieve weather data by city name, with optional fuzzy search
        
        Args:
            city_name: The city name to find weather data for
            fuzzy_search: If True, performs a partial/fuzzy match on city name
            
        Returns:
            A list of matching weather data records
        """
        try:
            all_records = self.repository.get_all_records()
            result = []
            
            if fuzzy_search:
                # For fuzzy search, create a case-insensitive regex pattern
                pattern = re.compile(f".*{re.escape(city_name)}.*", re.IGNORECASE)
                
                for record in all_records:
                    if pattern.match(record.get('city_name', '')):
                        try:
                            weather = Weather(**record)
                            result.append(weather.model_dump())
                        except Exception as e:
                            self.logger.warning(
                                f"Error converting weather record in fuzzy search: {str(e)}",
                                extra={"error_type": type(e).__name__, "record": record},
                                exc_info=True
                            )
            else:
                # Exact match (case-insensitive)
                city_name_lower = city_name.lower()
                for record in all_records:
                    if record.get('city_name', '').lower() == city_name_lower:
                        try:
                            weather = Weather(**record)
                            result.append(weather.model_dump())
                        except Exception as e:
                            self.logger.warning(
                                f"Error converting weather record in exact search: {str(e)}",
                                extra={"error_type": type(e).__name__, "record": record},
                                exc_info=True
                            )
            
            return result
        except Exception as e:
            self.logger.error(
                f"Error retrieving weather data for city name {city_name}: {str(e)}",
                extra={"error_type": type(e).__name__, "city_name": city_name},
                exc_info=True
            )
            raise
    
    def get_weather_data_by_date_range(
        self, 
        date_from: datetime, 
        date_to: datetime,
        city_id: Optional[int] = None,
        city_name: Optional[str] = None,
        fuzzy_search: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieve weather data within a date range, optionally filtered by location
        
        Args:
            date_from: Start date for the search
            date_to: End date for the search
            city_id: Optional city ID to filter by
            city_name: Optional city name to filter by
            fuzzy_search: If True, performs a partial/fuzzy match on city name
            
        Returns:
            A list of matching weather data records
        """
        try:
            all_records = self.repository.get_all_records()
            result = []
            
            for record in all_records:
                try:
                    # Apply city ID filter if provided
                    if city_id is not None and record.get('city_id') != city_id:
                        continue
                    
                    # Apply city name filter if provided
                    if city_name is not None:
                        record_city_name = record.get('city_name', '')
                        if fuzzy_search:
                            pattern = re.compile(f".*{re.escape(city_name)}.*", re.IGNORECASE)
                            if not pattern.match(record_city_name):
                                continue
                        else:
                            if record_city_name.lower() != city_name.lower():
                                continue
                    
                    # Create weather entity for further processing
                    weather = Weather(**record)
                    weather_data = weather.weather_data
                    
                    # If we don't have a date range in the record but we have weather data,
                    # extract the date range from the weather data
                    if not weather.date_from or not weather.date_to:
                        # Try to extract date range from the forecast data
                        if 'list' in weather_data and weather_data['list']:
                            first_forecast = weather_data['list'][0]
                            last_forecast = weather_data['list'][-1]
                            
                            if 'dt' in first_forecast and 'dt' in last_forecast:
                                record_date_from = datetime.fromtimestamp(first_forecast['dt'])
                                record_date_to = datetime.fromtimestamp(last_forecast['dt'])
                            else:
                                # Skip records without proper timestamps
                                continue
                        else:
                            # Skip records without forecast data
                            continue
                    else:
                        record_date_from = weather.date_from
                        record_date_to = weather.date_to
                    
                    # Check if record's date range overlaps with requested date range
                    if (record_date_from <= date_to and record_date_to >= date_from):
                        # Extract temperature data for the requested date range if not already present
                        if not weather.temperature_data or record_date_from != date_from or record_date_to != date_to:
                            weather.temperature_data = self._extract_temperature_data(
                                weather_data, date_from, date_to
                            )
                            
                            # Update the record with the extracted temperature data
                            update_data = {
                                'temperature_data': weather.temperature_data,
                                'date_from': date_from,
                                'date_to': date_to,
                                'updated_at': datetime.utcnow()
                            }
                            self.repository.update('_id', str(record.get('_id')), update_data)
                            weather.date_from = date_from
                            weather.date_to = date_to
                            weather.updated_at = datetime.utcnow()
                        
                        # Add to results
                        result.append(weather.model_dump())
                except Exception as e:
                    self.logger.warning(
                        f"Error processing record in date range search: {str(e)}",
                        extra={"error_type": type(e).__name__, "record_id": record.get('_id')},
                        exc_info=True
                    )
                    # Continue processing other records
            
            return result
        except Exception as e:
            self.logger.error(
                f"Error retrieving weather data by date range: {str(e)}",
                extra={
                    "error_type": type(e).__name__, 
                    "date_from": date_from.isoformat(), 
                    "date_to": date_to.isoformat()
                },
                exc_info=True
            )
            raise
    
    def _extract_temperature_data(
        self, 
        weather_data: Dict[str, Any], 
        date_from: datetime, 
        date_to: datetime
    ) -> Dict[str, Any]:
        """
        Extract temperature data from weather forecast for a specific date range
        
        Args:
            weather_data: The full weather forecast data
            date_from: Start date for extraction
            date_to: End date for extraction
            
        Returns:
            A dictionary with extracted temperature data
        """
        result = {
            'hourly': [],
            'daily': {},
            'summary': {
                'min_temp': float('inf'),
                'max_temp': float('-inf'),
                'avg_temp': 0
            }
        }
        
        if 'list' not in weather_data or not weather_data['list']:
            return result
            
        forecast_list = weather_data['list']
        valid_forecasts = []
        
        # Extract forecasts within the date range
        for forecast in forecast_list:
            if 'dt' not in forecast:
                continue
                
            forecast_date = datetime.fromtimestamp(forecast['dt'])
            if date_from <= forecast_date <= date_to:
                valid_forecasts.append(forecast)
                
                # Extract temperature
                temp = None
                if 'main' in forecast and 'temp' in forecast['main']:
                    temp = forecast['main']['temp']
                elif 'temp' in forecast:
                    temp = forecast['temp']
                
                if temp is not None:
                    # Add hourly data
                    hourly_data = {
                        'timestamp': forecast_date.isoformat(),
                        'temp': temp,
                        'description': None
                    }
                    
                    # Extract weather description
                    if 'weather' in forecast and forecast['weather']:
                        hourly_data['description'] = forecast['weather'][0].get('description')
                    
                    result['hourly'].append(hourly_data)
                    
                    # Update summary
                    result['summary']['min_temp'] = min(result['summary']['min_temp'], temp)
                    result['summary']['max_temp'] = max(result['summary']['max_temp'], temp)
                    
                    # Group by day
                    day_key = forecast_date.date().isoformat()
                    if day_key not in result['daily']:
                        result['daily'][day_key] = {
                            'temps': [],
                            'min': float('inf'),
                            'max': float('-inf'),
                            'avg': 0
                        }
                    
                    result['daily'][day_key]['temps'].append(temp)
                    result['daily'][day_key]['min'] = min(result['daily'][day_key]['min'], temp)
                    result['daily'][day_key]['max'] = max(result['daily'][day_key]['max'], temp)
        
        # Calculate averages
        total_temp = 0
        count = 0
        
        for day, day_data in result['daily'].items():
            if day_data['temps']:
                day_data['avg'] = sum(day_data['temps']) / len(day_data['temps'])
                total_temp += sum(day_data['temps'])
                count += len(day_data['temps'])
        
        if count > 0:
            result['summary']['avg_temp'] = total_temp / count
        
        # Handle edge cases for min/max
        if result['summary']['min_temp'] == float('inf'):
            result['summary']['min_temp'] = None
        if result['summary']['max_temp'] == float('-inf'):
            result['summary']['max_temp'] = None
            
        return result
    
    def update_weather_data(self, record_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update weather data by ID
        
        Args:
            record_id: The ID of the weather record to update
            update_data: A dictionary containing the fields to update
            
        Returns:
            True if the update was successful, False otherwise
        """
        try:
            # Add updated_at timestamp
            update_data['updated_at'] = datetime.utcnow()
            
            # Check if we need to update temperature data
            if ('date_from' in update_data or 'date_to' in update_data) and 'temperature_data' not in update_data:
                # Get current record
                current_data = self.get_weather_data(record_id)
                if current_data:
                    # Determine new date range
                    date_from = update_data.get('date_from', current_data.get('date_from'))
                    date_to = update_data.get('date_to', current_data.get('date_to'))
                    
                    if date_from and date_to:
                        # Extract temperature data with new date range
                        update_data['temperature_data'] = self._extract_temperature_data(
                            current_data['weather_data'], date_from, date_to
                        )
            
            # Update in database
            self.repository.update('_id', record_id, update_data)
            
            self.logger.info(
                f"Updated weather data for ID: {record_id}",
                extra={
                    "record_id": record_id,
                    "updated_fields": list(update_data.keys())
                }
            )
            
            return True
        except Exception as e:
            self.logger.error(
                f"Error updating weather data for ID {record_id}: {str(e)}",
                extra={"error_type": type(e).__name__, "record_id": record_id},
                exc_info=True
            )
            raise
            
    def delete_weather_data(self, record_id: str) -> bool:
        """
        Delete weather data by ID
        
        Args:
            record_id: The ID of the weather record to delete
            
        Returns:
            True if the deletion was successful, False otherwise
        """
        try:
            result = self.repository.delete('_id', record_id)
            
            if result:
                self.logger.info(
                    f"Deleted weather data for ID: {record_id}",
                    extra={"record_id": record_id}
                )
            else:
                self.logger.warning(
                    f"No weather data found to delete for ID: {record_id}",
                    extra={"record_id": record_id}
                )
                
            return result
        except Exception as e:
            self.logger.error(
                f"Error deleting weather data for ID {record_id}: {str(e)}",
                extra={"error_type": type(e).__name__, "record_id": record_id},
                exc_info=True
            )
            raise
            
    def get_all_weather_data(self) -> List[Dict[str, Any]]:
        """
        Retrieve all weather data records
        
        Returns:
            A list of all weather data records
        """
        try:
            data_list = self.repository.get_all_records()
            
            # Convert each record to a Weather entity
            result = []
            for data in data_list:
                try:
                    weather = Weather(**data)
                    result.append(weather.model_dump())
                except Exception as e:
                    # Log error but continue processing other records
                    self.logger.warning(
                        f"Error converting weather record: {str(e)}",
                        extra={"error_type": type(e).__name__, "record": data},
                        exc_info=True
                    )
                    
            return result
        except Exception as e:
            self.logger.error(
                f"Error retrieving all weather data: {str(e)}",
                extra={"error_type": type(e).__name__},
                exc_info=True
            )
            raise 
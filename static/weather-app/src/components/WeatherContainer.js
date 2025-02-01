import React, { useState } from 'react';
import api from '../api';
import WeatherDisplay from '../components/WeatherDisplay';
import WeatherSearch from '../components/WeatherSearch';
import Map from '../components/MapContainer';
import '../components/WeatherContainer.css';

const WeatherContainer = () => {
    const [weather, setWeather] = useState(null);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
  
    const handleSearch = async (searchParams) => {
      setLoading(true);
      setError(null);
      
      try {
        const data = await api.getForecast(searchParams);
        setWeather(data);
      } catch (err) {
        setError('Failed to fetch weather data');
        console.error('Error fetching weather:', err);
      } finally {
        setLoading(false);
      }
    };

    return (
      <div className="weather-container" style={{ backgroundColor: '#282c34' }}>
        <div className="weather-box">
          <WeatherSearch onSearch={handleSearch} />
          <WeatherDisplay 
              weather={weather}
              loading={loading}
              error={error}
          />
        </div>
        {weather && weather.city && (
          <Map lat={weather.city.coord.lat} lon={weather.city.coord.lon} style={{ backgroundColor: '#282c34' }} />
        )}
      </div>
    );
};

export default WeatherContainer;
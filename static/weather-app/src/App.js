import React, { useState } from 'react';
import api from './api';
import WeatherDisplay from './components/WeatherDisplay';
import WeatherSearch from './components/WeatherSearch';
import './App.css';

function App() {
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
    <div className="App">
      <header className="App-header">
        <h1>Weather Forecast</h1>
        <WeatherSearch onSearch={handleSearch} />
        <WeatherDisplay 
          weather={weather}
          loading={loading}
          error={error}
        />
      </header>
    </div>
  );
}

export default App;

import React from 'react';

const WeatherDisplay = ({ weather, loading, error }) => {
  if (loading) {
    return <p>Loading weather data...</p>;
  }

  if (error) {
    return <p className="error">{error}</p>;
  }

  if (!weather) {
    return <p>No weather data available</p>;
  }

  // Convert Kelvin to Celsius
  const kelvinToCelsius = (kelvin) => Math.round(kelvin - 273.15);

  // Format date and time
  const formatDateTime = (timestamp) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString([], {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  return (
    <div className="weather-container">
      {weather.city && (
        <div className="city-info">
          <h2>{weather.city.name}, {weather.city.country}</h2>
          <p className="coordinates">
            Coordinates: {weather.city.coord.lat}°, {weather.city.coord.lon}°
          </p>
        </div>
      )}

      <div className="weather-timeline">
        {weather.list.map((forecast) => (
          <div key={forecast.dt} className="timeline-item">
            <div className="timeline-time">
              {formatDateTime(forecast.dt)}
            </div>
            <div className="timeline-content">
              <div className="timeline-main">
                <div className="timeline-temp">
                  <span className="temp-value">{kelvinToCelsius(forecast.main.temp)}°C</span>
                  <span className="temp-feels">Feels like: {kelvinToCelsius(forecast.main.feels_like)}°C</span>
                </div>
                <div className="timeline-condition">
                  <h4>{forecast.weather[0].main}</h4>
                  <p>{forecast.weather[0].description}</p>
                </div>
              </div>
              <div className="timeline-details">
                <div className="detail-item">
                  <span className="detail-label">Humidity</span>
                  <span className="detail-value">{forecast.main.humidity}%</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Wind</span>
                  <span className="detail-value">{forecast.wind.speed} m/s</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Pressure</span>
                  <span className="detail-value">{forecast.main.pressure} hPa</span>
                </div>
                {forecast.rain && (
                  <div className="detail-item">
                    <span className="detail-label">Rain (3h)</span>
                    <span className="detail-value">{forecast.rain['3h']} mm</span>
                  </div>
                )}
                <div className="detail-item">
                  <span className="detail-label">Clouds</span>
                  <span className="detail-value">{forecast.clouds.all}%</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default WeatherDisplay; 
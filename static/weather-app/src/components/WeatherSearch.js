import React, { useState } from 'react';

const WeatherSearch = ({ onSearch }) => {
  const [searchType, setSearchType] = useState('coordinates');
  const [searchParams, setSearchParams] = useState({
    lat: '',
    lon: '',
    cityName: '',
    zipCode: ''
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setSearchParams(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const params = {};
    
    if (searchType === 'coordinates' && searchParams.lat && searchParams.lon) {
      params.lat = parseFloat(searchParams.lat);
      params.lon = parseFloat(searchParams.lon);
    } else if (searchType === 'city' && searchParams.cityName) {
      params.cityName = searchParams.cityName;
    } else if (searchType === 'zip' && searchParams.zipCode) {
      params.zipCode = searchParams.zipCode;
    }

    onSearch(params);
  };

  return (
    <div className="search-container">
      <form onSubmit={handleSubmit}>
        <div className="search-type">
          <label>
            <input
              type="radio"
              value="coordinates"
              checked={searchType === 'coordinates'}
              onChange={(e) => setSearchType(e.target.value)}
            />
            Coordinates
          </label>
          <label>
            <input
              type="radio"
              value="city"
              checked={searchType === 'city'}
              onChange={(e) => setSearchType(e.target.value)}
            />
            City Name
          </label>
          <label>
            <input
              type="radio"
              value="zip"
              checked={searchType === 'zip'}
              onChange={(e) => setSearchType(e.target.value)}
            />
            Zip Code
          </label>
        </div>

        {searchType === 'coordinates' && (
          <div className="coordinates-input">
            <input
              type="number"
              name="lat"
              value={searchParams.lat}
              onChange={handleInputChange}
              placeholder="Latitude"
              step="any"
            />
            <input
              type="number"
              name="lon"
              value={searchParams.lon}
              onChange={handleInputChange}
              placeholder="Longitude"
              step="any"
            />
          </div>
        )}

        {searchType === 'city' && (
          <input
            type="text"
            name="cityName"
            value={searchParams.cityName}
            onChange={handleInputChange}
            placeholder="Enter city name"
          />
        )}

        {searchType === 'zip' && (
          <input
            type="text"
            name="zipCode"
            value={searchParams.zipCode}
            onChange={handleInputChange}
            placeholder="Enter zip code"
          />
        )}

        <button type="submit">Get Weather</button>
      </form>
    </div>
  );
};

export default WeatherSearch; 
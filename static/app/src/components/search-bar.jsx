import React, { useState, useEffect, useCallback, memo } from "react";

const SearchBar = memo(({ onSearch, initialSearch }) => {
  const [searchType, setSearchType] = useState("cityName");
  const [searchValue, setSearchValue] = useState("");
  const [lat, setLat] = useState("");
  const [lon, setLon] = useState("");
  const [zipCode, setZipCode] = useState("");
  const [cityName, setCityName] = useState("");
  const [cityId, setCityId] = useState("");
  const [error, setError] = useState("");

  // Reset form when search type changes
  useEffect(() => {
    setSearchValue("");
    setLat("");
    setLon("");
    setZipCode("");
    setCityName("");
    setCityId("");
    setError("");
  }, [searchType]);

  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    setError("");

    // Create empty params object - we'll only add the parameters we need
    const params = {};

    switch (searchType) {
      case "coordinates":
        if (!lat || !lon) {
          setError("Please enter both latitude and longitude");
          return;
        }
        params.lat = lat;
        params.lon = lon;
        break;

      case "cityName":
        if (!cityName) {
          setError("Please enter a city name");
          return;
        }
        params.cityName = cityName;
        break;
        
      case "cityId":
        if (!cityId) {
          setError("Please enter a city ID");
          return;
        }
        params.cityId = cityId;
        break;

      case "zipCode":
        if (!zipCode) {
          setError("Please enter a zip code");
          return;
        }
        params.zipCode = zipCode;
        break;

      default:
        if (!searchValue.trim()) {
          setError("Please enter a search value");
          return;
        }
        break;
    }
    
    onSearch(params);
  }, [searchType, lat, lon, cityName, cityId, zipCode, searchValue, onSearch]);

  const getSearchTypeIcon = () => {
    switch (searchType) {
      case "cityName":
        return (
          <svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        );
      case "zipCode":
        return (
          <svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        );
      case "cityId":
        return (
          <svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c1.306 0 2.417.835 2.83 2M9 14a3.001 3.001 0 00-2.83 2M15 11h3m-3 4h2" />
          </svg>
        );
      case "coordinates":
        return (
          <svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
          </svg>
        );
      default:
        return null;
    }
  };

  const handleInputChange = useCallback((e, setter) => {
    setter(e.target.value);
    if (searchType !== "coordinates") {
      setSearchValue(e.target.value);
    }
  }, [searchType]);

  const searchOptions = [
    { id: "cityName", label: "City Name" },
    { id: "zipCode", label: "Zip Code" },
    { id: "cityId", label: "City ID" },
    { id: "coordinates", label: "Coordinates" }
  ];

  return (
    <div className="max-w-3xl mx-auto bg-white rounded-xl shadow-lg overflow-hidden" role="search">
      <div className="bg-gradient-to-r from-sky-700 to-sky-800 p-5">
        <h2 className="text-xl font-bold text-white flex items-center">
          <svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          Search Weather
        </h2>
      </div>

      <div className="p-6">
        <div className="mb-6">
          <fieldset>
            <legend className="block text-gray-700 text-sm font-medium mb-3">Search by:</legend>
            <div className="flex flex-wrap gap-2" role="radiogroup">
              {searchOptions.map((option) => (
                <button
                  key={option.id}
                  type="button"
                  role="radio"
                  aria-checked={searchType === option.id}
                  aria-label={`Search by ${option.label}`}
                  className={`flex items-center px-4 py-2.5 rounded-lg transition-all ${
                    searchType === option.id
                      ? "bg-sky-600 text-white shadow-md"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                  onClick={() => setSearchType(option.id)}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </fieldset>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border-l-4 border-red-500 text-red-700" role="alert">
            <p>{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          {searchType === "coordinates" ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="latitude" className="block text-gray-700 text-sm font-medium mb-1">
                  Latitude
                </label>
                <div className="relative mt-1">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500" aria-hidden="true">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5" />
                    </svg>
                  </div>
                  <input
                    type="text"
                    id="latitude"
                    value={lat}
                    onChange={(e) => handleInputChange(e, setLat)}
                    placeholder="51.5074"
                    className="pl-10 w-full p-3 bg-gray-50 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
                    required
                    aria-required="true"
                    aria-invalid={error && !lat ? "true" : "false"}
                  />
                </div>
              </div>
              <div>
                <label htmlFor="longitude" className="block text-gray-700 text-sm font-medium mb-1">
                  Longitude
                </label>
                <div className="relative mt-1">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500" aria-hidden="true">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5" />
                    </svg>
                  </div>
                  <input
                    type="text"
                    id="longitude"
                    value={lon}
                    onChange={(e) => handleInputChange(e, setLon)}
                    placeholder="-0.1278"
                    className="pl-10 w-full p-3 bg-gray-50 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
                    required
                    aria-required="true"
                    aria-invalid={error && !lon ? "true" : "false"}
                  />
                </div>
              </div>
            </div>
          ) : (
            <div>
              <label htmlFor="searchValue" className="block text-gray-700 text-sm font-medium mb-1">
                {searchType === "cityName"
                  ? "City Name"
                  : searchType === "zipCode"
                    ? "Zip Code"
                    : "City ID"}
              </label>
              <div className="relative mt-1">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500" aria-hidden="true">
                  {getSearchTypeIcon()}
                </div>
                <input
                  type="text"
                  id="searchValue"
                  value={searchType === "cityName" ? cityName : searchType === "zipCode" ? zipCode : cityId}
                  onChange={(e) => {
                    if (searchType === "cityName") handleInputChange(e, setCityName);
                    else if (searchType === "zipCode") handleInputChange(e, setZipCode);
                    else handleInputChange(e, setCityId);
                  }}
                  placeholder={
                    searchType === "cityName"
                      ? "London"
                      : searchType === "zipCode"
                        ? "90210"
                        : "2643743"
                  }
                  className="pl-10 w-full p-3 bg-gray-50 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
                  required
                  aria-required="true"
                  aria-invalid={error ? "true" : "false"}
                />
              </div>
            </div>
          )}

          <div className="text-right">
            <button
              type="submit"
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-sky-600 hover:bg-sky-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500 transition-colors"
              aria-label="Search for weather data"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Search
            </button>
          </div>
        </form>
      </div>
    </div>
  );
});

SearchBar.displayName = 'SearchBar';

export { SearchBar };
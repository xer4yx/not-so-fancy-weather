import React, { useState, useEffect, lazy, Suspense, useCallback } from "react";
import { WeatherProvider } from "../context/WeatherContext";
import { useWeatherSearch } from "../hooks/useWeatherSearch";
import { LoadingIndicator, ErrorMessage, SearchBar } from "../components";
import { userApi } from "../services/apiService";

// Lazy load components
const WeatherDisplay = lazy(() => import("../components/weather-display").then(module => ({ default: module.WeatherDisplay })));
const WeatherMap = lazy(() => import("../components/weather-map").then(module => ({ default: module.WeatherMap })));

const WeatherPageContent = () => {
  const { 
    weatherData, 
    loading, 
    error, 
    hasSearched, 
    defaultLocation, 
    preferences,
    handleSearch 
  } = useWeatherSearch();
  
  const [initialLoadDone, setInitialLoadDone] = useState(false);
  const [showMap, setShowMap] = useState(false);

  // Load default weather data on component mount
  useEffect(() => {
    const loadWeatherData = async () => {
      try {
        // Check if user is logged in
        const token = localStorage.getItem('accessToken');
        
        if (token) {
          // User is logged in, try to get preferences using cached API
          try {
            console.log("Fetching user preferences...");
            const userPreferences = await userApi.getPreferences();
            
            if (userPreferences && userPreferences.defaultLocation) {
              const defaultCity = userPreferences.defaultLocation.trim();
              if (defaultCity) {
                console.log("Using user's preferred default location:", defaultCity);
                await handleSearch({ cityName: defaultCity });
                setInitialLoadDone(true);
                return;
              }
            }
          } catch (error) {
            console.error("Error fetching user preferences:", error);
            // Continue to fallback if preference fetch fails
          }
        }
        
        // Fallback to localStorage preferences if API request failed
        const cachedPreferences = JSON.parse(localStorage.getItem('userPreferences') || 'null');
        
        if (token && cachedPreferences && cachedPreferences.defaultLocation) {
          const defaultCity = cachedPreferences.defaultLocation.trim();
          if (defaultCity) {
            console.log("Using user's preferred default location from localStorage:", defaultCity);
            await handleSearch({ cityName: defaultCity });
            setInitialLoadDone(true);
            return;
          }
        }
        
        // Final fallback to default location
        console.log("Using system default location");
        await handleSearch(defaultLocation);
        setInitialLoadDone(true);
      } catch (error) {
        console.error("Error loading initial weather data:", error);
        setInitialLoadDone(true);
      }
    };

    if (!initialLoadDone) {
      loadWeatherData();
    }
    
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialLoadDone]);

  // Toggle map view function
  const toggleMapView = () => {
    setShowMap(prev => !prev);
  };

  return (
    <div className="h-full w-full bg-gradient-to-b from-sky-600 to-sky-300 py-6 px-4">
      <div className="container mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-white drop-shadow-md">
            Weather Forecast
          </h1>
          <p className="mt-2 text-sky-100 max-w-2xl mx-auto">
            Get real-time weather updates for any location around the world
          </p>
        </div>
        
        {/* Search Section */}
        <div className="mb-8">
          <SearchBar onSearch={handleSearch} />
        </div>
        
        {/* Content Area */}
        <div className="mb-8" aria-live="polite">
          {loading && <LoadingIndicator message="Loading weather data..." />}
          
          {error && !loading && <ErrorMessage message={error} />}
          
          {weatherData && !loading && (
            <div>
              {/* Toggle button for mobile - only visible on mobile */}
              <div className="lg:hidden mb-4 flex justify-center">
                <button 
                  onClick={toggleMapView}
                  className="px-4 py-2 bg-white text-sky-600 rounded-full shadow-md hover:bg-sky-50 transition-all duration-300 flex items-center font-medium"
                  aria-label={showMap ? "Show weather details" : "Show map view"}
                >
                  {showMap ? (
                    <>
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                        <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
                      </svg>
                      Weather Details
                    </>
                  ) : (
                    <>
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                      </svg>
                      View Map
                    </>
                  )}
                </button>
              </div>

              {/* Desktop View: Two-column layout */}
              <div className="hidden lg:grid lg:grid-cols-2 gap-6">
                <div className="h-full">
                  <Suspense fallback={<div className="h-full w-full bg-gray-100 rounded-xl animate-pulse"></div>}>
                    <WeatherDisplay weatherData={weatherData} />
                  </Suspense>
                </div>
                <div className="h-[500px] md:h-auto rounded-lg overflow-hidden shadow-lg">
                  <Suspense fallback={<div className="h-full w-full bg-gray-100 rounded-xl animate-pulse"></div>}>
                    <WeatherMap weatherData={weatherData} />
                  </Suspense>
                </div>
              </div>

              {/* Mobile View: Animated toggle between weather and map */}
              <div className="lg:hidden overflow-y-auto overflow-x-hidden scrollbar-hide rounded-lg">
                <div className="relative h-[500px]">
                  <div 
                    className={`absolute w-full transition-all duration-500 ease-in-out transform ${
                      showMap ? "-translate-x-full opacity-0" : "translate-x-0 opacity-100"
                    }`}
                    style={{ visibility: showMap ? 'hidden' : 'visible' }}
                  >
                    <Suspense fallback={<div className="h-full w-full bg-gray-100 rounded-xl animate-pulse"></div>}>
                      <WeatherDisplay weatherData={weatherData} />
                    </Suspense>
                  </div>
                  <div 
                    className={`absolute h-full w-full transition-all duration-500 ease-in-out transform ${
                      showMap ? "translate-x-0 opacity-100" : "translate-x-full opacity-0"
                    }`}
                    style={{ visibility: showMap ? 'visible' : 'hidden' }}
                  >
                    <Suspense fallback={<div className="h-full w-full bg-gray-100 rounded-xl animate-pulse"></div>}>
                      <WeatherMap weatherData={weatherData} />
                    </Suspense>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {!hasSearched && !loading && !weatherData && (
            <div className="max-w-2xl mx-auto p-8 bg-white rounded-lg shadow-lg text-center" role="region" aria-label="Search instructions">
              <div className="text-sky-600 mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16l2.879-2.879m0 0a3 3 0 104.243-4.242 3 3 0 00-4.243 4.242zM21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-800 mb-2">Search for a Location</h2>
              <p className="text-gray-600 mb-4">
                Enter a location above to see the current weather forecast.
              </p>
              <div className="text-sm text-gray-500 max-w-md mx-auto">
                <p className="mb-2 font-medium">You can search by:</p>
                <div className="grid grid-cols-2 gap-3 text-left">
                  <div className="flex items-start">
                    <span className="text-sky-600 mr-2">•</span>
                    <span>City name (e.g., "London")</span>
                  </div>
                  <div className="flex items-start">
                    <span className="text-sky-600 mr-2">•</span>
                    <span>Zip code (e.g., "10001")</span>
                  </div>
                  <div className="flex items-start">
                    <span className="text-sky-600 mr-2">•</span>
                    <span>City ID (e.g., "2643743")</span>
                  </div>
                  <div className="flex items-start">
                    <span className="text-sky-600 mr-2">•</span>
                    <span>Coordinates (lat/lon)</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center text-sky-100 text-sm">
          <p>Data provided by OpenWeatherMap • Updated every 3 hours</p>
        </div>
      </div>
    </div>
  );
};

export const WeatherPage = () => {
  return (
    <WeatherProvider>
      <WeatherPageContent />
    </WeatherProvider>
  );
};

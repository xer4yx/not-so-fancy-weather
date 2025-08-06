import React, { memo, useState, useRef, useEffect } from 'react';
import { getIcon } from "../utils/WeatherIcons";
import { getCelcius, getLocalTime } from "../utils/WeatherUtils";
import { useWeather } from "../context/WeatherContext";
import { weatherApi } from "../services/apiService";

export const WeatherDisplay = memo(({ weatherData }) => {
  // Connect to the weather context to access user preferences
  const { state } = useWeather();
  const { preferences } = state;
  
  // Initialize all hooks at the top level, before any conditionals
  const [selectedForecast, setSelectedForecast] = useState(null);
  const [visibleForecasts, setVisibleForecasts] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const carouselRef = useRef(null);
  
  // Update selected forecast when weatherData changes
  useEffect(() => {
    if (weatherData && weatherData.list && weatherData.list.length > 0) {
      const forecasts = weatherData.list.slice(0, 8);
      setSelectedForecast(forecasts[0]);
      setVisibleForecasts(createCircularArray(forecasts));
      setCurrentIndex(0);
    }
  }, [weatherData]);
  
  // Animation for appearing
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, 50);
    
    return () => clearTimeout(timer);
  }, []);
  
  // Creates a circular array by repeating forecasts for infinite scroll effect
  const createCircularArray = (forecasts) => {
    // Duplicate the array to create a circular effect
    return [...forecasts, ...forecasts, ...forecasts];
  };
  
  // Scroll to the center on first render and when visibleForecasts changes
  useEffect(() => {
    if (carouselRef.current && visibleForecasts.length > 0) {
      // We want to center it on the middle section (the original array)
      setTimeout(() => {
        const itemWidth = 90 + 12; // width + gap of each forecast item
        const originalArrayLength = visibleForecasts.length / 3;
        const scrollPosition = originalArrayLength * itemWidth;
        carouselRef.current.scrollLeft = scrollPosition;
      }, 100);
    }
  }, [visibleForecasts]);
  
  // Detect scroll changes and update the selected forecast
  useEffect(() => {
    const handleScroll = () => {
      if (!carouselRef.current || visibleForecasts.length === 0) return;
      
      const scrollPosition = carouselRef.current.scrollLeft;
      const itemWidth = 90 + 12; // item width + gap
      
      // Calculate which item is in the center of the viewport
      const containerWidth = carouselRef.current.clientWidth;
      const centerPosition = scrollPosition + (containerWidth / 2);
      const centerIndex = Math.floor(centerPosition / itemWidth);
      
      // Don't update if the index is the same
      if (centerIndex !== currentIndex && centerIndex < visibleForecasts.length) {
        setCurrentIndex(centerIndex);
        setSelectedForecast(visibleForecasts[centerIndex]);
      }
      
      // Loop back if we're near the ends
      const isNearStart = scrollPosition < itemWidth * 3;
      const isNearEnd = scrollPosition > (visibleForecasts.length - 9) * itemWidth;
      
      if (isNearStart || isNearEnd) {
        // Jump to the middle copy of the array without animation
        const originalArrayLength = visibleForecasts.length / 3;
        const newScrollPosition = isNearStart 
          ? originalArrayLength * itemWidth
          : originalArrayLength * itemWidth;
          
        // Use setTimeout to avoid scroll event loop
        setTimeout(() => {
          carouselRef.current.scrollLeft = newScrollPosition;
        }, 50);
      }
    };
    
    const carousel = carouselRef.current;
    if (carousel) {
      carousel.addEventListener('scroll', handleScroll);
      return () => carousel.removeEventListener('scroll', handleScroll);
    }
  }, [visibleForecasts, currentIndex]);
  
  // Load default location from preferences if no weather data and preferences are loaded
  useEffect(() => {
    if (!weatherData && preferences && preferences.defaultLocation) {
      const fetchDefaultLocationWeather = async () => {
        try {
          // Parse city name from preferences
          const defaultCity = preferences.defaultLocation.trim();
          if (!defaultCity) return;
          
          // Fetch weather for the default location
          const result = await weatherApi.getForecast({ cityName: defaultCity });
          
          // Dispatch is handled by parent component, data will come back via weatherData prop
          console.log("Fetched weather for default location:", defaultCity);
        } catch (error) {
          console.error("Failed to fetch weather for default location:", error);
        }
      };
      
      fetchDefaultLocationWeather();
    }
  }, [weatherData, preferences]);
  
  // Early return for null data
  if (!weatherData || !selectedForecast) return null;

  const city = weatherData.city.name;
  const country = weatherData.city.country;
  const sunrise = getLocalTime(weatherData.city.sunrise);
  const sunset = getLocalTime(weatherData.city.sunset);
  
  // Function to scroll carousel horizontally
  const scrollCarousel = (direction) => {
    if (carouselRef.current) {
      const itemWidth = 90 + 12; // item width + gap
      
      // Scroll one item at a time, which will trigger the handleScroll event
      carouselRef.current.scrollBy({
        left: direction === 'left' ? -itemWidth : itemWidth,
        behavior: 'smooth'
      });
    }
  };

  // Get weather condition for styling based on selected forecast
  const getWeatherBackground = () => {
    const condition = selectedForecast.weather[0].main.toLowerCase();
    
    if (condition.includes('clear')) {
      return 'from-sky-500 to-blue-600';
    } else if (condition.includes('cloud')) {
      return 'from-gray-400 to-gray-600';
    } else if (condition.includes('rain') || condition.includes('drizzle')) {
      return 'from-blue-700 to-blue-900';
    } else if (condition.includes('snow')) {
      return 'from-blue-200 to-blue-400';
    } else if (condition.includes('thunder')) {
      return 'from-purple-600 to-purple-900';
    } else if (condition.includes('mist') || condition.includes('fog')) {
      return 'from-gray-300 to-gray-500';
    } else {
      return 'from-sky-600 to-sky-800';
    }
  };

  return (
    <div 
      className={`bg-white rounded-xl shadow-xl overflow-hidden h-full flex flex-col transition-all duration-500 ease-in-out transform ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`} 
      role="region" 
      aria-label={`Weather information for ${weatherData?.city?.name || ''}, ${weatherData?.city?.country || ''}`}
    >
      {/* Header - Shows selected forecast */}
      <div className={`p-6 bg-gradient-to-r ${getWeatherBackground()} text-white transition-all duration-500 ease-in-out`}>
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div className="flex items-center mb-4 md:mb-0">
            <img
              src={getIcon(selectedForecast.weather[0].icon)}
              alt={selectedForecast.weather[0].description}
              className="w-20 h-20 mr-4 transition-opacity duration-300"
            />
            <div>
              <h1 className="text-4xl font-bold">{getCelcius(selectedForecast.main.temp)}°C</h1>
              <p className="text-xl capitalize">{selectedForecast.weather[0].description}</p>
              <p className="text-sm opacity-90">Feels like {getCelcius(selectedForecast.main.feels_like)}°C</p>
            </div>
          </div>
          
          <div className="text-right">
            <h2 className="text-2xl font-bold">{city}, {country}</h2>
            <p className="text-sm opacity-90">
              {new Date(selectedForecast.dt * 1000).toLocaleDateString([], {
                weekday: 'long',
                month: 'long', 
                day: 'numeric'
              })}
            </p>
            <p className="text-sm opacity-90">
              {new Date(selectedForecast.dt * 1000).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit'
              })}
            </p>
          </div>
        </div>
      </div>

      {/* Selected Weather Details */}
      <div className="p-4 md:p-6 grid grid-cols-2 sm:grid-cols-4 gap-3 transition-all duration-300" role="list" aria-label="Weather details">
        <div className="bg-gray-50 p-3 md:p-4 rounded-lg border border-gray-100 shadow-sm flex flex-col items-center transform hover:scale-105 transition-transform duration-200" role="listitem">
          <img src="/assets/humidity.svg" alt="Humidity" className="h-6 w-6 text-sky-500 mb-2" />
          <p className="text-xs text-gray-500 uppercase font-medium">Humidity</p>
          <p className="text-xl font-semibold">{selectedForecast.main.humidity}%</p>
        </div>
        <div className="bg-gray-50 p-3 md:p-4 rounded-lg border border-gray-100 shadow-sm flex flex-col items-center transform hover:scale-105 transition-transform duration-200" role="listitem">
          <img src="/assets/wind.svg" alt="Wind" className="h-6 w-6 text-sky-500 mb-2" />
          <p className="text-xs text-gray-500 uppercase font-medium">Wind</p>
          <p className="text-xl font-semibold">{Math.round(selectedForecast.wind.speed)} m/s</p>
        </div>
        <div className="bg-gray-50 p-3 md:p-4 rounded-lg border border-gray-100 shadow-sm flex flex-col items-center transform hover:scale-105 transition-transform duration-200" role="listitem">
          <img src="/assets/pressure.svg" alt="Pressure" className="h-6 w-6 text-sky-500 mb-2" />
          <p className="text-xs text-gray-500 uppercase font-medium">Pressure</p>
          <p className="text-xl font-semibold">{selectedForecast.main.pressure}</p>
          <p className="text-xs text-gray-500">hPa</p>
        </div>
        <div className="bg-gray-50 p-3 md:p-4 rounded-lg border border-gray-100 shadow-sm flex flex-col items-center transform hover:scale-105 transition-transform duration-200" role="listitem">
          <img src="/assets/visiblity.svg" alt="Visibility" className="h-6 w-6 text-sky-500 mb-2" />
          <p className="text-xs text-gray-500 uppercase font-medium">Visibility</p>
          <p className="text-xl font-semibold">{Math.round(selectedForecast.visibility / 1000)}</p>
          <p className="text-xs text-gray-500">km</p>
        </div>
      </div>
      
      {/* Hourly Forecast Carousel */}
      <div className="p-4 md:p-6 bg-gray-50 border-t border-gray-200 transition-all duration-300">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-700 flex items-center" id="hourly-forecast">
            <img src="/assets/clock.svg" alt="Clock" className="h-5 w-5 mr-2 text-sky-500" />
            Weather Forecast
          </h3>
        </div>
        <div className="relative">
          <div 
            ref={carouselRef}
            className="relative flex overflow-x-auto pb-4 gap-3 scrollbar-hide snap-x snap-mandatory scroll-smooth no-scrollbar" 
            role="list" 
            aria-labelledby="hourly-forecast"
            style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
          >
            {visibleForecasts.map((forecast, index) => {
              // Extract time from the dt_txt field (format: "2025-02-01 06:00:00")
              const time = forecast.dt_txt 
                ? forecast.dt_txt.split(' ')[1].substring(0, 5) 
                : new Date(forecast.dt * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
              
              const isSelected = selectedForecast.dt === forecast.dt;
              
              return (
                <div 
                  key={`${forecast.dt}-${index}`} 
                  className={`flex-shrink-0 flex flex-col items-center p-3 rounded-lg border ${isSelected ? 'bg-sky-100 border-sky-300 shadow-md' : 'bg-white border-gray-100 shadow-sm'} hover:shadow-md transition-all duration-300 min-w-[90px] cursor-pointer snap-center transform ${isSelected ? 'scale-105' : 'scale-100 hover:scale-105'}`}
                  role="listitem"
                  tabIndex="0"
                  aria-selected={isSelected}
                >
                  <p className="text-sm font-medium text-gray-700">{time}</p>
                  <img 
                    src={getIcon(forecast.weather[0].icon)} 
                    alt={forecast.weather[0].description}
                    className="w-10 h-10 my-2"
                  />
                  <p className={`text-lg font-semibold ${isSelected ? 'text-sky-800' : 'text-sky-700'}`}>{getCelcius(forecast.main.temp)}°</p>
                  <p className="text-xs text-gray-500 capitalize">{forecast.weather[0].main}</p>
                </div>
              );
            })}
            
            {/* Visual guide for center position */}
            <div className="absolute left-1/2 top-0 bottom-0 w-px bg-sky-300 opacity-0 pointer-events-none" aria-hidden="true"></div>
          </div>
          
          {/* Navigation buttons as overlays */}
          <button 
            onClick={() => scrollCarousel('left')}
            className="absolute left-0 top-1/2 -translate-y-1/2 p-2 bg-white/80 text-sky-600 rounded-full hover:bg-sky-100 transition-all duration-200 shadow-md z-10 transform hover:scale-110"
            aria-label="Scroll left"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </button>
          <button 
            onClick={() => scrollCarousel('right')}
            className="absolute right-0 top-1/2 -translate-y-1/2 p-2 bg-white/80 text-sky-600 rounded-full hover:bg-sky-100 transition-all duration-200 shadow-md z-10 transform hover:scale-110"
            aria-label="Scroll right"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      </div>

      {/* Additional Info */}
      <div className="p-4 md:p-6 mt-auto bg-gradient-to-r from-sky-50 to-blue-50 border-t border-gray-200 transition-all duration-300">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4" role="list" aria-label="Daily weather summary">
          <div className="text-center transition-all duration-200 hover:bg-white hover:shadow-sm rounded-lg p-2" role="listitem">
            <p className="text-xs text-gray-500 uppercase font-medium mb-1">Min Temp</p>
            <p className="text-lg font-semibold text-gray-700 flex items-center justify-center">
              <img src="/assets/min-temp.svg" alt="Minimum Temperature" className="h-4 w-4 mr-1" />
              {getCelcius(selectedForecast.main.temp_min)}°C
            </p>
          </div>
          <div className="text-center transition-all duration-200 hover:bg-white hover:shadow-sm rounded-lg p-2" role="listitem">
            <p className="text-xs text-gray-500 uppercase font-medium mb-1">Max Temp</p>
            <p className="text-lg font-semibold text-gray-700 flex items-center justify-center">
              <img src="/assets/max-temp.svg" alt="Maximum Temperature" className="h-4 w-4 mr-1" />
              {getCelcius(selectedForecast.main.temp_max)}°C
            </p>
          </div>
          <div className="text-center transition-all duration-200 hover:bg-white hover:shadow-sm rounded-lg p-2" role="listitem">
            <p className="text-xs text-gray-500 uppercase font-medium mb-1">Sunrise</p>
            <p className="text-lg font-semibold text-gray-700 flex items-center justify-center">
              <img src="/assets/sunrise.svg" alt="Sunrise" className="h-4 w-4 mr-1" />
              {sunrise}
            </p>
          </div>
          <div className="text-center transition-all duration-200 hover:bg-white hover:shadow-sm rounded-lg p-2" role="listitem">
            <p className="text-xs text-gray-500 uppercase font-medium mb-1">Sunset</p>
            <p className="text-lg font-semibold text-gray-700 flex items-center justify-center">
              <img src="/assets/sunset.svg" alt="Sunset" className="h-4 w-4 mr-1" />
              {sunset}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
});

WeatherDisplay.displayName = 'WeatherDisplay'; 
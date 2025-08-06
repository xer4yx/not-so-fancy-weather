import React, { createContext, useContext, useReducer, useMemo, useEffect } from 'react';
import { userApi } from '../services/apiService';

// Initial state
const initialState = {
  weatherData: null,
  loading: false,
  error: null,
  hasSearched: false,
  defaultLocation: { lat: 51.505, lon: -0.09 },
  preferences: null,
};

// Action types
export const ACTIONS = {
  SET_LOADING: 'SET_LOADING',
  SET_WEATHER_DATA: 'SET_WEATHER_DATA',
  SET_ERROR: 'SET_ERROR',
  SET_HAS_SEARCHED: 'SET_HAS_SEARCHED',
  SET_PREFERENCES: 'SET_PREFERENCES',
  RESET_STATE: 'RESET_STATE',
};

// Reducer function
const weatherReducer = (state, action) => {
  switch (action.type) {
    case ACTIONS.SET_LOADING:
      return { ...state, loading: action.payload };
    case ACTIONS.SET_WEATHER_DATA:
      return { ...state, weatherData: action.payload, error: null };
    case ACTIONS.SET_ERROR:
      return { ...state, error: action.payload, weatherData: null };
    case ACTIONS.SET_HAS_SEARCHED:
      return { ...state, hasSearched: action.payload };
    case ACTIONS.SET_PREFERENCES:
      // Store preferences in localStorage when they're updated
      if (action.payload) {
        localStorage.setItem('userPreferences', JSON.stringify(action.payload));
        // Update the cache with the new preferences
        userApi._preferencesCache.data = action.payload;
        userApi._preferencesCache.timestamp = Date.now();
      } else {
        // If preferences are being reset, clear cache
        userApi.clearPreferencesCache();
      }
      return { ...state, preferences: action.payload };
    case ACTIONS.RESET_STATE:
      // Clear preferences cache when resetting state
      userApi.clearPreferencesCache();
      return { ...initialState };
    default:
      return state;
  }
};

// Create context
const WeatherContext = createContext();

// Context provider component
export const WeatherProvider = ({ children }) => {
  const [state, dispatch] = useReducer(weatherReducer, initialState);

  // Fetch user preferences when the context is initialized
  useEffect(() => {
    const fetchUserPreferences = async () => {
      // Check if user is logged in by looking for token
      const token = localStorage.getItem('accessToken');
      if (!token) return;
      
      try {
        console.log('Fetching user preferences from context...');
        const preferences = await userApi.getPreferences();
        console.log('User preferences received:', preferences);
        
        dispatch({ 
          type: ACTIONS.SET_PREFERENCES, 
          payload: preferences 
        });
      } catch (error) {
        console.error('Failed to fetch user preferences:', error);
      }
    };

    fetchUserPreferences();
  }, []);

  // Memoized value to prevent unnecessary re-renders
  const contextValue = useMemo(() => {
    return { state, dispatch };
  }, [state, dispatch]);

  return (
    <WeatherContext.Provider value={contextValue}>
      {children}
    </WeatherContext.Provider>
  );
};

// Custom hook to use weather context
export const useWeather = () => {
  const context = useContext(WeatherContext);
  if (context === undefined) {
    throw new Error('useWeather must be used within a WeatherProvider');
  }
  return context;
}; 
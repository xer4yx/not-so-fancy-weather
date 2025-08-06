import { useCallback } from 'react';
import { weatherApi, userApi } from '../services/apiService';
import { useWeather } from '../context/WeatherContext';
import { ACTIONS } from '../context/WeatherContext';

export const useWeatherSearch = () => {
  const { state, dispatch } = useWeather();
  
  const handleSearch = useCallback(async (searchParams) => {
    // Reset previous states
    dispatch({ type: ACTIONS.SET_ERROR, payload: null });
    dispatch({ type: ACTIONS.SET_LOADING, payload: true });
    dispatch({ type: ACTIONS.SET_HAS_SEARCHED, payload: true });
    
    try {
      const data = await weatherApi.getForecast(searchParams);
      dispatch({ type: ACTIONS.SET_WEATHER_DATA, payload: data });
      return data;
    } catch (error) {
      console.error("Weather search error:", error);
      dispatch({ 
        type: ACTIONS.SET_ERROR, 
        payload: error.message || "An error occurred while fetching weather data" 
      });
    } finally {
      dispatch({ type: ACTIONS.SET_LOADING, payload: false });
    }
  }, [dispatch]);
  
  // Function to update user preferences
  const updatePreferences = useCallback(async (newPreferences) => {
    try {
      // Update preferences via API
      const result = await userApi.updatePreferences(newPreferences);
      
      // Update preferences in context
      dispatch({ 
        type: ACTIONS.SET_PREFERENCES, 
        payload: result || newPreferences 
      });
      
      return result;
    } catch (error) {
      console.error("Error updating preferences:", error);
      throw error;
    }
  }, [dispatch]);

  return {
    weatherData: state.weatherData,
    loading: state.loading,
    error: state.error,
    hasSearched: state.hasSearched,
    defaultLocation: state.defaultLocation,
    preferences: state.preferences,
    handleSearch,
    updatePreferences
  };
}; 
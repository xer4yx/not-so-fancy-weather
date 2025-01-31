import axios from 'axios';

const API_BASE_URL = 'http://localhost:8668/api';

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 5000, // 10 seconds timeout
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add response interceptor for better error handling
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

const api = {
  getForecast: async (params = {}) => {
    try {
      const response = await axiosInstance.get('/weather/forecast', {
        params: {
          lat: params.lat,
          lon: params.lon,
          zip_code: params.zipCode,
          city_name: params.cityName,
          city_id: params.cityId
        }
      });
      return response.data;
    } catch (error) {
      if (error.code === 'ERR_NETWORK') {
        throw new Error('Cannot connect to the server. Please make sure the backend server is running on http://localhost:8000');
      } else if (error.response) {
        throw new Error(error.response.data?.detail || 'Failed to fetch weather data');
      } else if (error.request) {
        throw new Error('No response from server. Please check if the server is running.');
      } else {
        throw new Error('Error setting up the request');
      }
    }
  }
};

export default api;
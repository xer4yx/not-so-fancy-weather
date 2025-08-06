import axios from "axios";

export const API_HOST = process.env.REACT_APP_API_HOST;
const API_BASE_URL = `http://${API_HOST}:8668/api`;

// Cache implementation
class WeatherCache {
  constructor(maxAge = 10 * 60 * 1000) { // 10 minutes default cache time
    this.cache = new Map();
    this.maxAge = maxAge;
  }

  generateKey(endpoint, params) {
    const sortedParams = Object.keys(params)
      .sort()
      .reduce((result, key) => {
        result[key] = params[key];
        return result;
      }, {});

    return `${endpoint}:${JSON.stringify(sortedParams)}`;
  }

  get(endpoint, params) {
    const key = this.generateKey(endpoint, params);
    const cachedItem = this.cache.get(key);

    if (!cachedItem) return null;

    const { data, timestamp } = cachedItem;
    const now = Date.now();

    // Check if cache is still valid
    if (now - timestamp > this.maxAge) {
      this.cache.delete(key);
      return null;
    }

    return data;
  }

  set(endpoint, params, data) {
    const key = this.generateKey(endpoint, params);
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  clear() {
    this.cache.clear();
  }
}

// API client with caching
class ApiClient {
  constructor() {
    this.cache = new WeatherCache();
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 8000, // 8 seconds timeout
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Add request interceptor to add authorization header
    this.client.interceptors.request.use(
      async (config) => {
        // Try to get the token
        let token = localStorage.getItem('accessToken');

        console.log("Making request to:", config.url);

        // If we have a token, add it to the headers
        if (token) {
          // Important: Make sure there's no leading/trailing whitespace in the token
          token = token.trim();

          // Check if token is an access token, if not, try to get a refresh token
          const refreshToken = localStorage.getItem('refreshToken');

          // Only log partial token info for debugging  
          const maskedToken = token.length > 15
            ? token.substring(0, 10) + "..." + token.substring(token.length - 5)
            : "[token too short]";

          // Enhanced token logging
          console.log("Token details for request to:", config.url);

          // Determine if this is an access token or refresh token
          const isAccessToken = token === localStorage.getItem('accessToken')?.trim();
          const isRefreshToken = token === refreshToken?.trim();
          console.log("- Token role:", isAccessToken ? "ACCESS_TOKEN" :
            isRefreshToken ? "REFRESH_TOKEN" : "UNKNOWN_TOKEN_TYPE");
          console.log("- Token type:", token.includes("eyJ") ? "JWT" : "unknown format");
          console.log("- Token length:", token.length);

          // Show token suffix instead of prefix
          const tokenSuffix = token.length > 15
            ? "..." + token.substring(token.length - 15)
            : token;
          console.log("- Token suffix:", tokenSuffix);

          // Try to decode JWT token parts if it appears to be a JWT
          if (token.includes("eyJ") && token.split('.').length === 3) {
            try {
              const [header, payload, signature] = token.split('.');
              const decodedHeader = JSON.parse(atob(header));
              console.log("- Token algorithm:", decodedHeader.alg);
              console.log("- Token issuer:", JSON.parse(atob(payload)).iss || "not specified");
            } catch (e) {
              console.log("- Could not decode token parts:", e.message);
            }
          }

          console.log("Using token for request:", config.url, "token type:",
            token.includes("eyJ") ? "JWT" : "unknown");

          config.headers.Authorization = `Bearer ${token}`;
        } else {
          console.log("No token available for request:", config.url);
        }

        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        console.log("API Error status:", error.response?.status);
        console.log("API Error details:", error.response?.data);

        // If 401 error and not already retrying, try to refresh token
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          console.log("401 error, attempting to refresh token");

          try {
            // Get current tokens
            const refreshToken = localStorage.getItem('refreshToken');

            if (!refreshToken) {
              console.error("No refresh token available");
              throw new Error("No refresh token available");
            }

            console.log("Attempting to refresh token with refresh token");

            // Log token information for debugging
            try {
              const tokenParts = refreshToken.trim().split('.');
              if (tokenParts.length === 3) {
                const payload = JSON.parse(atob(tokenParts[1]));
                console.log("Refresh token details:", {
                  type: payload.token_type || "unknown",
                  exp: payload.exp ? new Date(payload.exp * 1000).toISOString() : "unknown",
                  username: payload.username || "unknown"
                });
              }
            } catch (decodeError) {
              console.warn("Could not decode refresh token for debugging:", decodeError.message);
            }

            // Create a separate axios instance for token refresh to avoid interceptors
            const tokenResponse = await axios({
              method: 'post',
              url: `${API_BASE_URL}/v1/refresh`,
              data: {
                refresh_token: refreshToken.trim()
              },
              headers: {
                'Content-Type': 'application/json'
              }
            });

            if (!tokenResponse.data.access_token) {
              console.error("Invalid token response:", tokenResponse.data);
              throw new Error("Invalid token response from server");
            }

            const { access_token, refresh_token } = tokenResponse.data;

            console.log("Token refreshed successfully");

            // Update tokens in storage - ensure no extra whitespace
            localStorage.setItem('accessToken', access_token.trim());
            localStorage.setItem('refreshToken', refresh_token.trim());

            // Update authorization header with the new token for retry
            originalRequest.headers.Authorization = `Bearer ${access_token.trim()}`;

            // Retry the original request with the new token
            console.log("Retrying original request with new token");
            return axios(originalRequest);
          } catch (refreshError) {
            console.error("Token refresh failed:", refreshError.message || refreshError);
            if (refreshError.response) {
              console.error("Server response:", refreshError.response.status, refreshError.response.data);
            }

            // Clear tokens and reject
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');

            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(this.handleError(error));
      }
    );
  }

  handleError(error) {
    if (error.code === "ERR_NETWORK") {
      return new Error(
        "Oops! Cannot connect to the server right now. Try again later."
      );
    } else if (error.response) {
      const message = error.response.data?.detail || "Sorry, could not complete the request.";
      console.error("API Error response:", message);
      return new Error(message);
    } else if (error.request) {
      return new Error(
        "Something happened to your request. Try again later."
      );
    } else {
      return new Error("Oops! Something went wrong. Try again later.");
    }
  }

  async get(endpoint, params = {}, useCache = true) {
    console.log(`GET ${endpoint} request, params:`, params);

    // Try to get from cache first if caching is enabled
    if (useCache) {
      const cachedData = this.cache.get(endpoint, params);
      if (cachedData) {
        console.log("Using cached data for:", endpoint);
        return cachedData;
      }
    }

    // If not in cache, make the API call
    try {
      console.log(`Making GET request to ${endpoint}`);
      const response = await this.client.get(endpoint, { params });
      console.log(`GET ${endpoint} response:`, response.status);

      // Store in cache if caching is enabled
      if (useCache) {
        this.cache.set(endpoint, params, response.data);
      }

      return response.data;
    } catch (error) {
      console.error(`GET ${endpoint} error:`, error.message);
      throw error;
    }
  }

  async post(endpoint, data, config = {}) {
    console.log(`POST ${endpoint} request, data:`, data);

    try {
      const response = await this.client.post(endpoint, data, config);
      console.log(`POST ${endpoint} response:`, response.status);
      return response.data;
    } catch (error) {
      console.error(`POST ${endpoint} error:`, error.message);
      throw error;
    }
  }

  async delete(endpoint, data) {
    console.log(`DELETE ${endpoint} request`);

    try {
      const response = await this.client.delete(endpoint, { data });
      console.log(`DELETE ${endpoint} response:`, response.status);
      return response.data;
    } catch (error) {
      console.error(`DELETE ${endpoint} error:`, error.message);
      throw error;
    }
  }

  clearCache() {
    this.cache.clear();
  }
}

// Create a singleton instance
const apiClient = new ApiClient();

export const docSchemaApi = {
  _schemaCache: null,
  _schemaCacheTimestamp: 0,
  _schemaCacheMaxAge: 30 * 60 * 1000, // 30 minutes cache time
  
  // Get OpenAPI schema with caching
  getOpenAPISchema: async () => {
    try {
      // Check if we have valid cached schema
      const now = Date.now();
      if (docSchemaApi._schemaCache && 
          (now - docSchemaApi._schemaCacheTimestamp < docSchemaApi._schemaCacheMaxAge)) {
        console.log("Using cached OpenAPI schema");
        return docSchemaApi._schemaCache;
      }
      
      console.log("Fetching fresh OpenAPI schema");
      const response = await axios.get(`${API_BASE_URL}/openapi.json`);
      
      // Update cache
      docSchemaApi._schemaCache = response.data;
      docSchemaApi._schemaCacheTimestamp = now;
      
      return response.data;
    } catch (error) {
      console.error("Error fetching OpenAPI schema:", error);
      throw error;
    }
  },
  
  // Manually clear the schema cache if needed
  clearSchemaCache: () => {
    docSchemaApi._schemaCache = null;
    docSchemaApi._schemaCacheTimestamp = 0;
    console.log("OpenAPI schema cache cleared");
  }
}

// Weather API functions
export const weatherApi = {
  getForecast: async (params = {}) => {
    // Filter out empty parameters
    const filteredParams = {};
    if (params.lat) filteredParams.lat = params.lat;
    if (params.lon) filteredParams.lon = params.lon;
    if (params.zipCode) filteredParams.zip_code = params.zipCode;
    if (params.cityName) filteredParams.city_name = params.cityName;
    if (params.cityId) filteredParams.city_id = params.cityId;

    return apiClient.get("/weather/forecast", filteredParams);
  }
};

// Auth API functions
export const authApi = {
  // Register a new user
  signup: async (username, email, password) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/v1/user`, {
        username,
        email,
        password
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || "Signup failed");
    }
  },

  // Login using OAuth2 password flow (form-urlencoded)
  login: async (username, password) => {
    try {
      console.log("Login attempt for:", username);

      // Ensure the credentials are properly trimmed to avoid whitespace issues
      const trimmedUsername = username.trim();
      const trimmedPassword = password.trim();

      const params = new URLSearchParams();
      params.append('username', trimmedUsername);
      params.append('password', trimmedPassword);

      // Direct axios call to bypass default JSON Content-Type
      const response = await axios.post(`${API_BASE_URL}/v1/login`, params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });

      console.log("Login response:", response.data);
      return response.data;
    } catch (error) {
      console.error("Login error details:", error.response?.status, error.response?.data);
      throw new Error(error.response?.data?.detail || "Login failed");
    }
  },

  // Logout (blacklist tokens)
  logout: async (access_token, refresh_token) => {
    try {
      return apiClient.post('/v1/logout', {
        access_token,
        refresh_token
      });
    } catch (error) {
      console.error("Logout error:", error);
      // Treat as successful even if server-side logout fails
      return true;
    }
  },

  // Refresh tokens
  refreshToken: async (refresh_token) => {
    try {
      console.log("Calling refresh token API directly");

      // Ensure the token is trimmed
      refresh_token = refresh_token.trim();

      // Use direct axios call (not through interceptor)
      const response = await axios({
        method: 'post',
        url: `${API_BASE_URL}/v1/refresh`,
        data: { refresh_token },
        headers: { 'Content-Type': 'application/json' }
      });

      console.log("Refresh token response received");
      return response.data;
    } catch (error) {
      console.error("Refresh token error:", error);
      throw new Error(error.response?.data?.detail || "Token refresh failed");
    }
  }
};

// User API functions
export const userApi = {
  // Cache for preferences
  _preferencesCache: {
    data: null,
    timestamp: 0,
    maxAge: 5 * 60 * 1000 // 5 minutes cache time
  },

  // Get current user profile
  getProfile: async () => {
    console.log("Getting user profile");
    return apiClient.get("/v1/user/me");
  },

  // Update user profile
  updateProfile: async (data) => {
    console.log("Updating user profile");
    return apiClient.post("/v1/user/me", data);
  },

  // Update user password
  updatePassword: async (currentPassword, newPassword) => {
    console.log("Updating user password");

    // Make sure to trim whitespace from password inputs
    const trimmedCurrentPassword = currentPassword.trim();
    const trimmedNewPassword = newPassword.trim();

    return apiClient.post("/v1/user/password", {
      current_password: trimmedCurrentPassword,
      new_password: trimmedNewPassword
    });
  },

  // Get user preferences
  getPreferences: async () => {
    console.log("Getting user preferences");

    // Check if we have valid cached preferences
    const now = Date.now();
    if (userApi._preferencesCache.data &&
      (now - userApi._preferencesCache.timestamp < userApi._preferencesCache.maxAge)) {
      console.log("Using cached preferences data");
      return userApi._preferencesCache.data;
    }

    // No valid cache, fetch preferences from API
    try {
      const preferences = await apiClient.get("/v1/user/preferences");

      // Update cache
      userApi._preferencesCache.data = preferences;
      userApi._preferencesCache.timestamp = now;

      return preferences;
    } catch (error) {
      console.error("Error fetching preferences:", error);
      throw error;
    }
  },

  // Update user preferences
  updatePreferences: async (preferences) => {
    console.log("Updating user preferences");

    try {
      const result = await apiClient.post("/v1/user/preferences", preferences);

      // Update cache with new preferences
      userApi._preferencesCache.data = result;
      userApi._preferencesCache.timestamp = Date.now();

      return result;
    } catch (error) {
      console.error("Error updating preferences:", error);
      throw error;
    }
  },

  // Clear preferences cache
  clearPreferencesCache: () => {
    userApi._preferencesCache.data = null;
    userApi._preferencesCache.timestamp = 0;
    console.log("Preferences cache cleared");
  }
};

export default apiClient; 
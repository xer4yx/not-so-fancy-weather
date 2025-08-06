import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../services/apiService';
import { userApi } from '../services/apiService';

// Create the Authentication Context
const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check if user is already logged in on component mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('accessToken');
      if (token) {
        try {
          // Try to get user info from localStorage
          const username = localStorage.getItem('username');
          
          // If we have a username, set the user
          if (username) {
            setUser({ username });
            
            // Also verify the token expiration and refresh if needed
            try {
              // Decode the token to check expiration
              // JWT tokens are in format: header.payload.signature
              const payload = JSON.parse(atob(token.split('.')[1]));
              const expiration = payload.exp * 1000; // Convert to milliseconds
              
              // If token is expired or about to expire (less than 5 minutes left)
              if (Date.now() > expiration - 5 * 60 * 1000) {
                console.log("Token expired or about to expire, refreshing...");
                await refreshToken();
              }
            } catch (decodeError) {
              console.error("Error decoding token:", decodeError);
              // Continue with the existing token
            }
          } else {
            // If no username found, clear storage
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('username');
          }
        } catch (err) {
          console.error('Auth validation error:', err);
          // If token validation fails, clear local storage
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');
          localStorage.removeItem('username');
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  // Signup function
  const signup = async (username, email, password) => {
    setIsLoading(true);
    setError(null);
    try {
      // Use authApi for signup
      await authApi.signup(username, email, password);
      return true;
    } catch (err) {
      setError(err.message || 'Signup failed');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  // Login function
  const login = async (username, password) => {
    setIsLoading(true);
    setError(null);
    try {
      console.log("Attempting login with username:", username);
      
      // Use authApi for login with proper error handling
      const data = await authApi.login(username, password);
      
      if (!data || !data.access_token) {
        throw new Error("Invalid response from server. Missing access token.");
      }
      
      // Store tokens in localStorage (ensure they're properly trimmed)
      localStorage.setItem('accessToken', data.access_token.trim());
      localStorage.setItem('refreshToken', data.refresh_token.trim());
      localStorage.setItem('username', username.trim());
      
      setUser({ username: username.trim() });
      return true;
    } catch (err) {
      console.error("Login error in AuthContext:", err);
      setError(err.message || 'Login failed');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  // Logout function
  const logout = async () => {
    setIsLoading(true);
    try {
      const accessToken = localStorage.getItem('accessToken');
      const refreshToken = localStorage.getItem('refreshToken');
      
      // Call logout endpoint if tokens exist
      if (accessToken) {
        await authApi.logout(accessToken, refreshToken);
      }
    } catch (err) {
      console.error('Logout error:', err);
      // Continue with local logout regardless of server response
    } finally {
      // Clear local storage
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('username');
      
      // Also clear the preferences cache
      if (typeof userApi !== 'undefined' && userApi.clearPreferencesCache) {
        userApi.clearPreferencesCache();
      }
      
      setUser(null);
      setIsLoading(false);
    }
  };

  // Handle token refresh
  const refreshToken = async () => {
    try {
      const currentRefreshToken = localStorage.getItem('refreshToken');
      if (!currentRefreshToken) {
        throw new Error('No refresh token available');
      }

      console.log("AuthContext: refreshing token");
      const data = await authApi.refreshToken(currentRefreshToken);
      console.log("AuthContext: token refreshed successfully");
      
      localStorage.setItem('accessToken', data.access_token);
      localStorage.setItem('refreshToken', data.refresh_token);
      
      return data.access_token;
    } catch (err) {
      // Log the user out on refresh failure
      console.error('Token refresh error:', err);
      // Clear tokens
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('username');
      setUser(null);
      throw err;
    }
  };

  const value = {
    user,
    isLoading,
    error,
    signup,
    login,
    logout,
    refreshToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Custom hook to use the AuthContext
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 
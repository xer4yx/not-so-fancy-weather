import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * Hook to guard routes based on authentication status
 * @param {boolean} requireAuth - If true, redirects to redirectPath if user is not authenticated
 *                              - If false, redirects to redirectPath if user is authenticated
 * @param {string} redirectPath - Path to redirect to if condition is not met
 */
export const useAuthGuard = (requireAuth = true, redirectPath = '/login') => {
  const { user, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // Wait until authentication check is complete
    if (!isLoading) {
      // If requireAuth is true and user is not authenticated, redirect to login
      // If requireAuth is false and user is authenticated, redirect to home
      if ((requireAuth && !user) || (!requireAuth && user)) {
        navigate(redirectPath, { replace: true });
      }
    }
  }, [isLoading, navigate, redirectPath, requireAuth, user]);

  return { isLoading, isAuthenticated: !!user };
}; 
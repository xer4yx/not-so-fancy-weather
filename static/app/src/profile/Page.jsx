import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { userApi } from '../services/apiService';
import { useNavigate } from 'react-router-dom';

// Loading component for profile sections
const SectionLoader = () => (
  <div className="animate-pulse">
    <div className="h-4 bg-slate-300 rounded w-3/4 mb-2.5"></div>
    <div className="h-4 bg-slate-300 rounded w-1/2 mb-2.5"></div>
    <div className="h-4 bg-slate-300 rounded w-5/6 mb-2.5"></div>
  </div>
);

export const ProfilePage = () => {
  const { user, logout, refreshToken } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('general');
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [preferences, setPreferences] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [updateSuccess, setUpdateSuccess] = useState(false);
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [passwordError, setPasswordError] = useState(null);
  const [passwordSuccess, setPasswordSuccess] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const MAX_RETRIES = 5;

  // Get user profile data
  useEffect(() => {
    const fetchUserData = async () => {
      if (retryCount > MAX_RETRIES) {
        console.error(`Maximum retry attempts (${MAX_RETRIES}) reached, showing profile with error`);
        // Create a fallback profile from local storage data
        const username = localStorage.getItem('username');
        if (username) {
          setProfile({
            username,
            email: 'Unable to load email - authentication issue',
            name: ''
          });
          
          // Set default preferences
          setPreferences({
            units: 'metric',
            theme: 'auto',
            defaultLocation: ''
          });
        }
        
        setError(`We're having trouble connecting to the server. Some profile features may be limited. 
                 You can try logging out and back in to resolve this issue.`);
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        console.log(`Attempting to fetch user profile, attempt ${retryCount + 1} of ${MAX_RETRIES}`);
        
        // For the first attempt, try with the existing token
        // For subsequent attempts, try refreshing the token
        if (retryCount > 0) {
          try {
            console.log("Explicitly refreshing token before retry");
            const newToken = await refreshToken();
            console.log("Token refreshed, continuing with profile fetch");
            
            // Short delay before trying the API call to ensure token is saved
            await new Promise(resolve => setTimeout(resolve, 1000));
          } catch (refreshError) {
            console.error("Failed to refresh token:", refreshError);
            // On refresh failure, increment retry count and try again
            setRetryCount(prev => prev + 1);
            // Short delay before trying again
            setTimeout(fetchUserData, 1000);
            return;
          }
        }
        
        // Get profile data
        console.log("Fetching user profile data...");
        const profileData = await userApi.getProfile();
        console.log("Profile data received successfully");
        setProfile(profileData);
        
        // Try to get user preferences
        try {
          console.log("Fetching user preferences...");
          const preferencesData = await userApi.getPreferences();
          console.log("Preferences data received successfully");
          setPreferences(preferencesData);
        } catch (prefError) {
          console.error("Failed to get preferences:", prefError);
          // Default preferences if not found
          setPreferences({
            units: 'metric',
            theme: 'auto',
            defaultLocation: ''
          });
        }
        
        setError(null);
        setRetryCount(0); // Reset retry count on success
      } catch (err) {
        console.error("Profile fetch error:", err);
        
        // Increment retry counter for all errors
        setRetryCount(prev => prev + 1);
        
        // Check if we should try again
        if (retryCount < MAX_RETRIES) {
          console.log(`Retry ${retryCount + 1} of ${MAX_RETRIES}, waiting before next attempt...`);
          // Try again after increasing delay (backoff)
          setTimeout(fetchUserData, Math.min(1000 * retryCount, 5000));
        }
      } finally {
        if (retryCount >= MAX_RETRIES) {
          setLoading(false);
        }
      }
    };

    if (user) {
      fetchUserData();
    } else {
      // Redirect to login if not authenticated
      navigate('/login');
    }
  }, [user, navigate, logout, refreshToken]);

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setUpdateSuccess(false);
    
    try {
      // First try to refresh token
      await refreshToken();
      
      await userApi.updateProfile(profile);
      setUpdateSuccess(true);
      // Reset success message after 3 seconds
      setTimeout(() => setUpdateSuccess(false), 3000);
    } catch (err) {
      setError('Failed to update profile. Please try again.');
      console.error('Profile update error:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handlePreferencesUpdate = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setUpdateSuccess(false);
    
    try {
      // First try to refresh token
      await refreshToken();
      
      // Use the API with caching
      await userApi.updatePreferences(preferences);
      
      setUpdateSuccess(true);
      // Reset success message after 3 seconds
      setTimeout(() => setUpdateSuccess(false), 3000);
    } catch (err) {
      setError('Failed to update preferences. Please try again.');
      console.error('Preferences update error:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    
    // Validate passwords
    const currentPassword = passwordForm.currentPassword;
    const newPassword = passwordForm.newPassword;
    const confirmPassword = passwordForm.confirmPassword;
    
    // Perform validation on trimmed values
    if (!currentPassword) {
      setPasswordError('Current password is required');
      return;
    }
    
    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match');
      return;
    }
    
    if (newPassword.length < 8) {
      setPasswordError('Password must be at least 8 characters');
      return;
    }
    
    setIsSaving(true);
    setPasswordError(null);
    setPasswordSuccess(false);
    
    console.log("Attempting to update password for user");
    
    try {
      // First try to refresh token
      await refreshToken();
      
      // Using trimmed password values for API call
      await userApi.updatePassword(
        currentPassword,
        newPassword
      );
      
      // Clear form and show success
      setPasswordForm({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      });
      
      console.log("Password updated successfully");
      setPasswordSuccess(true);
      // Reset success message after 3 seconds
      setTimeout(() => setPasswordSuccess(false), 3000);
    } catch (err) {
      console.error('Password update error:', err);
      setPasswordError(err.message || 'Failed to update password');
    } finally {
      setIsSaving(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  // Loading state
  if (loading && !profile) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-3xl mx-auto bg-white rounded-lg shadow-md p-6 mb-8">
          <h1 className="text-2xl font-bold text-slate-800 mb-6">Loading profile...</h1>
          <SectionLoader />
          <SectionLoader />
          <SectionLoader />
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {error && (
        <div className="max-w-3xl mx-auto mb-4 bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded" role="alert">
          <p>{error}</p>
          {retryCount > MAX_RETRIES && (
            <div className="mt-2">
              <button 
                onClick={handleLogout}
                className="underline hover:text-red-900 mr-4"
              >
                Log out
              </button>
              <button 
                onClick={() => {
                  setRetryCount(0);
                  setError(null);
                  navigate('/');
                }}
                className="underline hover:text-red-900"
              >
                Go to weather forecast
              </button>
            </div>
          )}
        </div>
      )}
      
      {updateSuccess && (
        <div className="max-w-3xl mx-auto mb-4 bg-green-100 border-l-4 border-green-500 text-green-700 p-4 rounded" role="alert">
          <p>Successfully updated!</p>
        </div>
      )}
      
      {/* Profile header with avatar */}
      <div className="max-w-3xl mx-auto bg-white rounded-lg shadow-md overflow-hidden mb-8">
        <div className="bg-gradient-to-r from-sky-600 to-blue-500 p-6">
          <div className="flex flex-col sm:flex-row items-center">
            <div className="h-24 w-24 rounded-full bg-sky-300 flex items-center justify-center text-white text-4xl font-bold border-4 border-white shadow-md">
              {profile?.username ? profile.username.charAt(0).toUpperCase() : user?.username?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="mt-4 sm:mt-0 sm:ml-6 text-center sm:text-left">
              <h1 className="text-2xl font-bold text-white">{profile?.username || user?.username}</h1>
              <p className="text-blue-100">{profile?.email || 'No email provided'}</p>
              <p className="text-blue-100 text-sm">Member since: {profile?.created_at ? new Date(profile.created_at).toLocaleDateString() : 'Unknown'}</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Tabs and content */}
      <div className="max-w-3xl mx-auto bg-white rounded-lg shadow-md overflow-hidden">
        {/* Tab navigation */}
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab('general')}
            className={`px-6 py-3 font-medium text-sm focus:outline-none ${activeTab === 'general' ? 'text-sky-600 border-b-2 border-sky-600' : 'text-gray-500 hover:text-gray-700'}`}
          >
            General Information
          </button>
          <button
            onClick={() => setActiveTab('preferences')}
            className={`px-6 py-3 font-medium text-sm focus:outline-none ${activeTab === 'preferences' ? 'text-sky-600 border-b-2 border-sky-600' : 'text-gray-500 hover:text-gray-700'}`}
          >
            Weather Preferences
          </button>
          <button
            onClick={() => setActiveTab('security')}
            className={`px-6 py-3 font-medium text-sm focus:outline-none ${activeTab === 'security' ? 'text-sky-600 border-b-2 border-sky-600' : 'text-gray-500 hover:text-gray-700'}`}
          >
            Security
          </button>
        </div>
        
        {/* Tab content */}
        <div className="p-6">
          {/* General Information Tab */}
          {activeTab === 'general' && (
            <form onSubmit={handleProfileUpdate}>
              <div className="mb-5">
                <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
                  Username
                </label>
                <input
                  type="text"
                  id="username"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sky-500 focus:border-sky-500"
                  value={profile?.username || ''}
                  onChange={(e) => setProfile({...profile, username: e.target.value})}
                  disabled={isSaving || retryCount > MAX_RETRIES}
                />
              </div>
              
              <div className="mb-5">
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  id="email"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sky-500 focus:border-sky-500"
                  value={profile?.email || ''}
                  onChange={(e) => setProfile({...profile, email: e.target.value})}
                  disabled={isSaving || retryCount > MAX_RETRIES}
                />
              </div>
              
              <div className="mb-5">
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name (Optional)
                </label>
                <input
                  type="text"
                  id="name"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sky-500 focus:border-sky-500"
                  value={profile?.name || ''}
                  onChange={(e) => setProfile({...profile, name: e.target.value})}
                  disabled={isSaving || retryCount > MAX_RETRIES}
                />
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="submit"
                  className="bg-sky-600 hover:bg-sky-700 text-white font-medium py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500 transition-colors disabled:opacity-50"
                  disabled={isSaving || retryCount > MAX_RETRIES}
                >
                  {isSaving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          )}
          
          {/* Weather Preferences Tab */}
          {activeTab === 'preferences' && (
            <form onSubmit={handlePreferencesUpdate}>
              <div className="mb-5">
                <label htmlFor="units" className="block text-sm font-medium text-gray-700 mb-1">
                  Temperature Units
                </label>
                <select
                  id="units"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sky-500 focus:border-sky-500"
                  value={preferences?.units || 'metric'}
                  onChange={(e) => setPreferences({...preferences, units: e.target.value})}
                  disabled={isSaving || retryCount > MAX_RETRIES}
                >
                  <option value="metric">Celsius (°C)</option>
                  <option value="imperial">Fahrenheit (°F)</option>
                  <option value="standard">Kelvin (K)</option>
                </select>
              </div>
              
              <div className="mb-5">
                <label htmlFor="theme" className="block text-sm font-medium text-gray-700 mb-1">
                  Theme Preference
                </label>
                <select
                  id="theme"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sky-500 focus:border-sky-500"
                  value={preferences?.theme || 'auto'}
                  onChange={(e) => setPreferences({...preferences, theme: e.target.value})}
                  disabled={isSaving || retryCount > MAX_RETRIES}
                >
                  <option value="auto">Auto (System Default)</option>
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                </select>
              </div>
              
              <div className="mb-5">
                <label htmlFor="defaultLocation" className="block text-sm font-medium text-gray-700 mb-1">
                  Default Location (city name, postal code, or coordinates)
                </label>
                <input
                  type="text"
                  id="defaultLocation"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sky-500 focus:border-sky-500"
                  placeholder="e.g., London, 90210, or 40.7128,-74.0060"
                  value={preferences?.defaultLocation || ''}
                  onChange={(e) => setPreferences({...preferences, defaultLocation: e.target.value})}
                  disabled={isSaving || retryCount > MAX_RETRIES}
                />
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="submit"
                  className="bg-sky-600 hover:bg-sky-700 text-white font-medium py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500 transition-colors disabled:opacity-50"
                  disabled={isSaving || retryCount > MAX_RETRIES}
                >
                  {isSaving ? 'Saving...' : 'Save Preferences'}
                </button>
              </div>
            </form>
          )}
          
          {/* Security Tab */}
          {activeTab === 'security' && (
            <div>
              {retryCount > MAX_RETRIES ? (
                <div className="p-4 mb-4 bg-yellow-100 border-l-4 border-yellow-400 text-yellow-700">
                  <p className="font-medium">Authentication Issue</p>
                  <p>Password change is unavailable due to authentication issues. Please try logging out and back in.</p>
                </div>
              ) : (
                <form onSubmit={handlePasswordChange} className="mb-8">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Change Password</h3>
                  
                  {passwordError && (
                    <div className="mb-4 bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded" role="alert">
                      <p>{passwordError}</p>
                    </div>
                  )}
                  
                  {passwordSuccess && (
                    <div className="mb-4 bg-green-100 border-l-4 border-green-500 text-green-700 p-4 rounded" role="alert">
                      <p>Password updated successfully!</p>
                    </div>
                  )}
                  
                  <div className="mb-5">
                    <label htmlFor="currentPassword" className="block text-sm font-medium text-gray-700 mb-1">
                      Current Password
                    </label>
                    <input
                      type="password"
                      id="currentPassword"
                      className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sky-500 focus:border-sky-500"
                      value={passwordForm.currentPassword}
                      onChange={(e) => setPasswordForm({...passwordForm, currentPassword: e.target.value})}
                      disabled={isSaving}
                      required
                    />
                  </div>
                  
                  <div className="mb-5">
                    <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700 mb-1">
                      New Password
                    </label>
                    <input
                      type="password"
                      id="newPassword"
                      className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sky-500 focus:border-sky-500"
                      value={passwordForm.newPassword}
                      onChange={(e) => setPasswordForm({...passwordForm, newPassword: e.target.value})}
                      disabled={isSaving}
                      required
                      minLength={8}
                    />
                    <p className="mt-1 text-sm text-gray-500">Password must be at least 8 characters</p>
                  </div>
                  
                  <div className="mb-5">
                    <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
                      Confirm New Password
                    </label>
                    <input
                      type="password"
                      id="confirmPassword"
                      className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sky-500 focus:border-sky-500"
                      value={passwordForm.confirmPassword}
                      onChange={(e) => setPasswordForm({...passwordForm, confirmPassword: e.target.value})}
                      disabled={isSaving}
                      required
                    />
                  </div>
                  
                  <div className="flex justify-end space-x-3">
                    <button
                      type="submit"
                      className="bg-sky-600 hover:bg-sky-700 text-white font-medium py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500 transition-colors disabled:opacity-50"
                      disabled={isSaving}
                    >
                      {isSaving ? 'Updating...' : 'Update Password'}
                    </button>
                  </div>
                </form>
              )}
              
              <div className="border-t border-gray-200 pt-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Account Actions</h3>
                <button
                  onClick={handleLogout}
                  className="bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
                >
                  Logout
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
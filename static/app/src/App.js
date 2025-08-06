import React, { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Navbar, ErrorBoundary } from './components';
import { AuthProvider, useAuth } from './context/AuthContext';

// Lazy load pages for code splitting
const WeatherPage = lazy(() => import('./weather/Page').then(module => ({ default: module.WeatherPage })));
const LoginPage = lazy(() => import('./login/Page').then(module => ({ default: module.LoginPage })));
const SignupPage = lazy(() => import('./signup/Page').then(module => ({ default: module.SignupPage })));
const ProfilePage = lazy(() => import('./profile/Page').then(module => ({ default: module.ProfilePage })));
const DocumentationPage = lazy(() => import('./documentation/Page').then(module => ({ default: module.DocumentationPage })));

// Loading fallback component
const PageLoader = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-100">
    <div className="p-6 max-w-sm mx-auto bg-white rounded-xl shadow-lg flex items-center space-x-4">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-sky-500"></div>
      <div className="text-xl text-gray-700 font-medium">Loading...</div>
    </div>
  </div>
);

// Protected route component
const ProtectedRoute = ({ children }) => {
  const { user, isLoading } = useAuth();
  
  // Show loading state while authentication is being checked
  if (isLoading) {
    return <PageLoader />;
  }
  
  // Redirect to login if not authenticated
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

function AppRoutes() {
  return (
    <BrowserRouter>
      <div className="min-h-screen min-w-screen bg-gradient-to-b from-slate-400 to-slate-200">
        <Navbar />
        <main role="main">
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route 
                path="/" 
                element={
                  <ProtectedRoute>
                    <WeatherPage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/forecast" 
                element={
                  <ProtectedRoute>
                    <WeatherPage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/profile" 
                element={
                  <ProtectedRoute>
                    <ProfilePage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/docs" 
                element={
                  <ErrorBoundary>
                    <DocumentationPage />
                  </ErrorBoundary>
                } 
              />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/signup" element={<SignupPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </BrowserRouter>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}

export default App;

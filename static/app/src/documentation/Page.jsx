import React, { useState, useEffect } from 'react';
import { docSchemaApi } from '../services/apiService';
import { EndpointList, EndpointDetail, ErrorBoundary, LoadingIndicator } from '../components';

export const DocumentationPage = () => {
  const [schema, setSchema] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedEndpoint, setSelectedEndpoint] = useState(null);
  const [isMobileView, setIsMobileView] = useState(window.innerWidth < 768);
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    const fetchSchema = async () => {
      try {
        setIsLoading(true);
        const data = await docSchemaApi.getOpenAPISchema();
        setSchema(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching OpenAPI schema:', err);
        setError('Failed to load API documentation. Please try again later.');
      } finally {
        // Add a small delay to ensure smooth transitions
        setTimeout(() => {
          setIsLoading(false);
        }, 100);
      }
    };

    fetchSchema();

    // Handle window resize for responsive design
    const handleResize = () => {
      setIsMobileView(window.innerWidth < 768);
    };

    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      // Reset state on unmount to prevent memory leaks or stale references
      setSelectedEndpoint(null);
      setIsTransitioning(true); // Mark as transitioning to prevent additional renders
    };
  }, []);

  // Handler for selecting an endpoint with transition protection
  const handleSelectEndpoint = (endpoint) => {
    console.log('Endpoint selected:', endpoint.path, endpoint.method);
    
    // Set endpoint immediately without transition delay
    setSelectedEndpoint(endpoint);

    // On mobile, scroll to detail section when an endpoint is selected
    if (isMobileView && endpoint) {
      // Wrap in setTimeout to ensure DOM is updated first
      setTimeout(() => {
        const detailElement = document.getElementById('endpoint-detail');
        if (detailElement) {
          detailElement.scrollIntoView({ behavior: 'smooth' });
        }
      }, 50);
    }
  };

  if (isLoading) {
    return <LoadingIndicator />;
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-slate-50">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg max-w-lg w-full shadow-sm">
          <p className="font-medium">Error Loading Documentation</p>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-800 mb-3">API Documentation</h1>
          <p className="text-slate-600 max-w-3xl">
            Check out all available endpoints and details in the API.
          </p>
        </div>

        <div className="flex flex-col md:flex-row gap-6">
          {/* Sidebar with endpoint list */}
          <div className={`md:w-1/3 lg:w-1/4 ${selectedEndpoint && isMobileView ? 'hidden' : 'block'}`}>
            <div className="bg-white rounded-lg shadow-md p-4 sticky top-20 border border-slate-100">
              <h2 className="text-xl font-semibold mb-4 text-slate-700 pb-2 border-b border-slate-100">Endpoints</h2>
              <ErrorBoundary>
                {schema && <EndpointList schema={schema} onSelectEndpoint={handleSelectEndpoint} />}
              </ErrorBoundary>
            </div>
          </div>

          {/* Main content area */}
          <div id="endpoint-detail" className={`md:w-2/3 lg:w-3/4 ${!selectedEndpoint && isMobileView ? 'hidden' : 'block'}`}>
            <ErrorBoundary>
              {selectedEndpoint ? (
                <EndpointDetail 
                  endpoint={selectedEndpoint} 
                  schema={schema}
                  onBack={() => isMobileView && setSelectedEndpoint(null)}
                  isMobileView={isMobileView}
                />
              ) : (
                <div className="bg-white rounded-lg shadow-md p-8 text-center hidden md:flex items-center justify-center min-h-[300px] border border-slate-100">
                  <div>
                    <svg className="w-16 h-16 mx-auto text-slate-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
                    </svg>
                    <h3 className="text-xl text-slate-600">Select an endpoint from the list to view its details</h3>
                  </div>
                </div>
              )}
            </ErrorBoundary>
          </div>
        </div>
      </div>
    </div>
  );
}; 
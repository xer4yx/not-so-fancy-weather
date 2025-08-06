import React from 'react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error to the console
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ errorInfo });
    
    // You can also log the error to an error reporting service
    // logErrorToService(error, errorInfo);
  }
  
  // Reset the error state - useful for navigation
  reset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  }

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-slate-50">
          <div className="bg-white rounded-lg shadow-md p-6 max-w-lg w-full border border-slate-200">
            <div className="mb-4 text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 text-red-600 mb-4">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-slate-800 mb-2">Something went wrong</h2>
              <p className="text-slate-600">{this.state.error?.message || 'An unexpected error occurred'}</p>
            </div>
            
            <div className="space-y-4">
              <button 
                onClick={this.reset}
                className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-center transition-colors font-medium"
              >
                Try again
              </button>
              <button 
                onClick={() => window.location.reload()}
                className="w-full py-2 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md text-center transition-colors font-medium"
              >
                Reload page
              </button>
            </div>
            
            {/* Display more error details in development environment */}
            {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
              <div className="mt-6 p-4 bg-slate-100 rounded-md overflow-auto max-h-[300px]">
                <p className="text-sm font-bold mb-2 text-slate-700">Error details (visible in development only):</p>
                <pre className="text-xs text-slate-800 font-mono whitespace-pre-wrap">
                  {this.state.error?.stack || this.state.error?.toString()}
                </pre>
                <p className="text-sm font-bold mt-4 mb-2 text-slate-700">Component stack:</p>
                <pre className="text-xs text-slate-800 font-mono whitespace-pre-wrap">
                  {this.state.errorInfo.componentStack}
                </pre>
              </div>
            )}
          </div>
        </div>
      );
    }

    // If there's no error, render children normally
    return this.props.children;
  }
} 
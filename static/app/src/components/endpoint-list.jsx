import React, { useState } from 'react';

// HTTP Method Badge component to color-code methods
const MethodBadge = ({ method }) => {
  // Using semantic colors for HTTP methods
  const colors = {
    get: 'bg-emerald-100 text-emerald-800',   // Green for safe operations
    post: 'bg-blue-100 text-blue-800',        // Blue for creating resources
    put: 'bg-amber-100 text-amber-800',       // Amber for updating resources
    delete: 'bg-red-100 text-red-800',        // Red for danger/deletion
    patch: 'bg-purple-100 text-purple-800'    // Purple for partial updates
  };

  return (
    <span className={`inline-block px-2 py-1 text-xs font-medium rounded ${colors[method.toLowerCase()] || 'bg-slate-100 text-slate-800'}`}>
      {method.toUpperCase()}
    </span>
  );
};

export const EndpointList = ({ schema, onSelectEndpoint }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTag, setActiveTag] = useState('');

  // Extract paths from schema
  const paths = schema?.paths || {};
  
  // Get unique tags from operations
  let tags = new Set();
  Object.entries(paths).forEach(([path, pathItem]) => {
    Object.entries(pathItem).forEach(([method, operation]) => {
      if (operation.tags && operation.tags.length > 0) {
        operation.tags.forEach(tag => tags.add(tag));
      }
    });
  });
  tags = Array.from(tags).sort();

  // Filter endpoints based on search query and active tag
  const filteredEndpoints = Object.entries(paths)
    .flatMap(([path, pathItem]) => {
      return Object.entries(pathItem).map(([method, operation]) => {
        return {
          path,
          method,
          operation,
          summary: operation.summary || '',
          tags: operation.tags || []
        };
      });
    })
    .filter(endpoint => {
      const matchesSearch = searchQuery === '' || 
        endpoint.path.toLowerCase().includes(searchQuery.toLowerCase()) ||
        endpoint.summary.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesTag = activeTag === '' || endpoint.tags.includes(activeTag);
      
      return matchesSearch && matchesTag;
    })
    .sort((a, b) => {
      // Sort by tag first, then by path
      if (a.tags[0] !== b.tags[0]) {
        return a.tags[0] > b.tags[0] ? 1 : -1;
      }
      return a.path.localeCompare(b.path);
    });

  return (
    <div>
      {/* Search input */}
      <div className="mb-4">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
            <svg className="w-4 h-4 text-slate-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            placeholder="Search endpoints..."
            className="w-full pl-10 pr-3 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-slate-800 placeholder:text-slate-400"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Tags filter */}
      {tags.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          <button
            onClick={() => setActiveTag('')}
            className={`px-3 py-1 text-xs rounded-full transition-colors duration-200 ${
              activeTag === '' 
                ? 'bg-blue-600 text-white shadow-sm' 
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            All
          </button>
          {tags.map(tag => (
            <button
              key={tag}
              onClick={() => setActiveTag(tag)}
              className={`px-3 py-1 text-xs rounded-full transition-colors duration-200 ${
                activeTag === tag 
                  ? 'bg-blue-600 text-white shadow-sm' 
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {tag}
            </button>
          ))}
        </div>
      )}

      {/* Endpoints list */}
      <div className="px-1 py-1 space-y-2 overflow-y-auto max-h-[70vh] pr-2 scrollbar-hide">
        {filteredEndpoints.length > 0 ? (
          filteredEndpoints.map((endpoint, index) => (
            <button
              key={`${endpoint.path}-${endpoint.method}-${index}`}
              className="w-full text-left p-3 bg-white hover:bg-blue-50 rounded-md transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-blue-500 border border-slate-100 shadow-sm"
              onClick={() => onSelectEndpoint(endpoint)}
            >
              <div className="flex items-center justify-between mb-1">
                <MethodBadge method={endpoint.method} />
                {endpoint.tags[0] && (
                  <span className="text-xs bg-slate-100 px-2 py-0.5 rounded-full text-slate-700">
                    {endpoint.tags[0]}
                  </span>
                )}
              </div>
              <p className="font-mono text-sm truncate text-slate-800">{endpoint.path}</p>
              {endpoint.operation.summary && (
                <p className="text-sm text-slate-600 mt-1 truncate">{endpoint.operation.summary}</p>
              )}
            </button>
          ))
        ) : (
          <div className="text-slate-500 text-center py-8 bg-white rounded-md border border-slate-100 shadow-sm">
            <svg className="w-10 h-10 mx-auto text-slate-300 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M12 12.5h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p>No endpoints found matching your criteria</p>
          </div>
        )}
      </div>
    </div>
  );
};
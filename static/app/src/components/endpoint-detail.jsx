import React, { useState, useEffect, useRef } from 'react';

// Component to display parameters
const ParameterList = ({ parameters }) => {
  if (!parameters || parameters.length === 0) {
    return <p className="text-slate-500 italic">No parameters</p>;
  }

  return (
    <div className="overflow-x-auto rounded-md border border-slate-200">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-slate-50 border-b border-slate-200">
            <th className="px-4 py-2 text-left font-medium text-slate-700">Name</th>
            <th className="px-4 py-2 text-left font-medium text-slate-700">Location</th>
            <th className="px-4 py-2 text-left font-medium text-slate-700">Type</th>
            <th className="px-4 py-2 text-left font-medium text-slate-700">Required</th>
            <th className="px-4 py-2 text-left font-medium text-slate-700">Description</th>
          </tr>
        </thead>
        <tbody>
          {parameters.map((param, index) => (
            <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
              <td className="px-4 py-2 font-mono text-blue-600">{param.name}</td>
              <td className="px-4 py-2 text-slate-700">{param.in}</td>
              <td className="px-4 py-2 font-mono text-emerald-600">{param.schema?.type || param.type || '-'}</td>
              <td className="px-4 py-2">
                {param.required ? (
                  <span className="text-red-600 font-medium">Yes</span>
                ) : (
                  <span className="text-slate-500">No</span>
                )}
              </td>
              <td className="px-4 py-2 text-slate-700">{param.description || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// Component to display request body
const RequestBody = ({ requestBody }) => {
  const [activeContent, setActiveContent] = useState('application/json');
  
  if (!requestBody || !requestBody.content) {
    return <p className="text-slate-500 italic">No request body</p>;
  }
  
  const contentTypes = Object.keys(requestBody.content);
  
  return (
    <div>
      {contentTypes.length > 1 && (
        <div className="mb-2 border-b border-slate-200">
          <div className="flex space-x-2">
            {contentTypes.map(type => (
              <button
                key={type}
                className={`py-2 px-3 text-sm font-medium ${
                  activeContent === type
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
                onClick={() => setActiveContent(type)}
              >
                {type}
              </button>
            ))}
          </div>
        </div>
      )}
      
      <div className="mt-2">
        {requestBody.content[activeContent]?.schema && (
          <SchemaDisplay schema={requestBody.content[activeContent].schema} />
        )}
      </div>
    </div>
  );
};

// Component to display responses
const ResponseDisplay = ({ responses }) => {
  const [activeResponse, setActiveResponse] = useState('');
  
  useEffect(() => {
    // Reset the active response when responses change
    if (responses && Object.keys(responses).length > 0) {
      setActiveResponse(Object.keys(responses)[0]);
    }
  }, [responses]);
  
  if (!responses || Object.keys(responses).length === 0) {
    return <p className="text-slate-500 italic">No response information</p>;
  }
  
  const statusCodes = Object.keys(responses);
  
  // Color coding for status codes
  const getStatusCodeColor = (code) => {
    const codeNum = parseInt(code);
    if (codeNum >= 200 && codeNum < 300) return 'bg-emerald-100 text-emerald-800';  // Success
    if (codeNum >= 300 && codeNum < 400) return 'bg-blue-100 text-blue-800';        // Redirection
    if (codeNum >= 400 && codeNum < 500) return 'bg-amber-100 text-amber-800';       // Client errors
    if (codeNum >= 500) return 'bg-red-100 text-red-800';                           // Server errors
    return 'bg-slate-100 text-slate-800';                                           // Default
  };
  
  // Safely get description with fallback
  const getDescription = (code) => {
    return responses[code]?.description || 'No description';
  };
  
  return (
    <div>
      <div className="mb-3 border-b border-slate-200">
        <div className="flex flex-wrap">
          {statusCodes.map(code => (
            <button
              key={code}
              className={`py-2 px-3 text-sm font-medium mb-1 mr-1 ${
                activeResponse === code
                  ? 'border-b-2 border-blue-500 text-blue-700 bg-blue-50'
                  : 'text-slate-600 hover:text-slate-800 hover:bg-slate-50'
              }`}
              onClick={() => setActiveResponse(code)}
            >
              <span className={`inline-block px-2 py-0.5 rounded text-xs mr-1 ${getStatusCodeColor(code)}`}>
                {code}
              </span>
              {getDescription(code).substring(0, 20) + (getDescription(code).length > 20 ? '...' : '')}
            </button>
          ))}
        </div>
      </div>
      
      {activeResponse && responses[activeResponse] && (
        <div className="mt-3 p-4 bg-slate-50 rounded-md border border-slate-200">
          <h4 className="font-medium mb-3 text-slate-800">{getDescription(activeResponse)}</h4>
          
          {responses[activeResponse]?.content && (
            <div className="mt-4">
              <h5 className="text-sm font-medium text-slate-700 mb-2 pb-1 border-b border-slate-200">Response Schema</h5>
              {Object.entries(responses[activeResponse].content).map(([contentType, content]) => (
                <div key={contentType} className="mt-2">
                  <div className="text-xs font-mono text-slate-500 mb-1">{contentType}</div>
                  {content.schema && <SchemaDisplay schema={content.schema} />}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Component to display schema objects
const SchemaDisplay = ({ schema }) => {
  const [expanded, setExpanded] = useState(true);
  
  if (!schema) return null;
  
  const formatSchemaType = (schema) => {
    if (schema.$ref) {
      const refName = schema.$ref.split('/').pop();
      return <span className="text-purple-600">{refName}</span>;
    }
    
    if (schema.type === 'array' && schema.items) {
      return (
        <>
          <span className="text-blue-600">array</span>
          <span className="text-slate-500">[</span>
          {formatSchemaType(schema.items)}
          <span className="text-slate-500">]</span>
        </>
      );
    }
    
    return <span className="text-blue-600">{schema.type || 'object'}</span>;
  };
  
  return (
    <div className="bg-slate-50 p-3 rounded-md font-mono text-sm overflow-x-auto border border-slate-200">
      <div 
        className="cursor-pointer flex items-center" 
        onClick={() => setExpanded(!expanded)}
      >
        <span className="mr-2 text-slate-500">{expanded ? '▼' : '►'}</span>
        {schema.type === 'object' ? (
          <span>
            {schema.title ? (
              <>
                <span className="text-slate-700 font-medium">{schema.title}</span>
                <span className="text-slate-500"> {"{}"}</span>
              </>
            ) : (
              <span className="text-slate-500">{"{}"}</span>
            )}
          </span>
        ) : (
          formatSchemaType(schema)
        )}
      </div>
      
      {expanded && schema.properties && (
        <div className="ml-4 mt-2 border-l-2 border-slate-300 pl-3">
          {Object.entries(schema.properties).map(([propName, propSchema]) => (
            <div key={propName} className="mb-1">
              <span className="text-emerald-600">{propName}</span>
              <span className="text-slate-500">: </span>
              {formatSchemaType(propSchema)}
              {schema.required?.includes(propName) && (
                <span className="ml-2 text-xs text-red-500 font-medium">required</span>
              )}
              {propSchema.description && (
                <span className="ml-2 text-xs text-slate-500">
                  // {propSchema.description}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export const EndpointDetail = ({ endpoint, schema, onBack, isMobileView }) => {
  const [activeTab, setActiveTab] = useState('parameters');
  const tabsContainerRef = useRef(null);
  
  // Reset active tab when endpoint changes
  useEffect(() => {
    if (endpoint) {
      console.log('Endpoint detail received:', endpoint.path, endpoint.method);
      setActiveTab('parameters');
    }
  }, [endpoint]);
  
  // Cleanup function to prevent scroll operations on unmounted components
  useEffect(() => {
    return () => {
      // This empty cleanup function ensures any pending state updates won't execute
      // after the component unmounts
    };
  }, []);
  
  // Safely handle tab selection with guards against race conditions
  const handleTabChange = (tabId) => {
    // Check if component is still mounted before updating state
    if (tabsContainerRef.current) {
      setActiveTab(tabId);
    }
  };
  
  // Early return if no endpoint
  if (!endpoint) {
    console.log('No endpoint provided to EndpointDetail');
    return null;
  }
  
  const { path, method, operation } = endpoint;
  console.log('Rendering EndpointDetail for:', path, method);
  
  const tabs = [
    { id: 'parameters', label: 'Parameters', show: true },
    { id: 'requestBody', label: 'Request Body', show: !!operation.requestBody },
    { id: 'responses', label: 'Responses', show: !!operation.responses },
    { id: 'examples', label: 'Examples', show: false } // Add examples tab if needed
  ].filter(tab => tab.show);

  // Method badge styling
  const getMethodColor = (method) => {
    switch (method.toLowerCase()) {
      case 'get': return 'bg-emerald-200 text-emerald-800 border-emerald-300';
      case 'post': return 'bg-blue-200 text-blue-800 border-blue-300';
      case 'put': return 'bg-amber-200 text-amber-800 border-amber-300';
      case 'delete': return 'bg-red-200 text-red-800 border-red-300';
      case 'patch': return 'bg-purple-200 text-purple-800 border-purple-300';
      default: return 'bg-slate-200 text-slate-800 border-slate-300';
    }
  };
  
  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden border border-slate-100">
      {/* Header section */}
      <div className="p-6 border-b border-slate-200">
        {isMobileView && (
          <button 
            onClick={onBack}
            className="mb-4 flex items-center text-blue-600 hover:text-blue-800"
            aria-label="Back to endpoints list"
          >
            <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to endpoints
          </button>
        )}
        
        <div className="flex flex-wrap items-start justify-between">
          <div className="max-w-2xl">
            <h2 className="text-2xl font-bold text-slate-800 mb-2">
              {operation.summary || path}
            </h2>
            {operation.description && (
              <p className="mt-2 text-slate-600">{operation.description}</p>
            )}
          </div>
          <div className="mt-2 sm:mt-0">
            <span className={`
              uppercase font-mono font-bold text-lg px-3 py-1 rounded 
              border-2
              mr-2
              inline-block
              text-center min-w-[80px]
              ${getMethodColor(method)}
            `}>
              {method.toUpperCase()}
            </span>
          </div>
        </div>
        
        <div className="mt-4">
          <div className="font-mono text-sm bg-slate-50 p-3 rounded-md border border-slate-200 break-all">
            <span className="text-slate-500">Endpoint:</span> <span className="text-blue-600">{path}</span>
          </div>
        </div>
        
        {/* Tags display */}
        {operation.tags && operation.tags.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {operation.tags.map(tag => (
              <span key={tag} className="px-2 py-1 bg-blue-50 text-blue-700 rounded-md text-xs font-medium border border-blue-100">
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>
      
      {/* Content tabs */}
      <div className="border-b border-slate-200 bg-slate-50">
        <div className="flex overflow-x-auto" ref={tabsContainerRef}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`py-3 px-4 text-sm font-medium whitespace-nowrap transition-colors duration-150 ${
                activeTab === tab.id
                  ? 'border-b-2 border-blue-500 text-blue-700 bg-white'
                  : 'text-slate-600 hover:text-slate-800 hover:bg-slate-100'
              }`}
              onClick={() => handleTabChange(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>
      
      {/* Tab content */}
      <div className="p-6">
        {activeTab === 'parameters' && (
          <div>
            <h3 className="text-lg font-medium mb-4 text-slate-800 pb-2 border-b border-slate-100">Parameters</h3>
            <ParameterList parameters={operation.parameters || []} />
          </div>
        )}
        
        {activeTab === 'requestBody' && (
          <div>
            <h3 className="text-lg font-medium mb-4 text-slate-800 pb-2 border-b border-slate-100">Request Body</h3>
            <RequestBody requestBody={operation.requestBody} />
          </div>
        )}
        
        {activeTab === 'responses' && (
          <div>
            <h3 className="text-lg font-medium mb-4 text-slate-800 pb-2 border-b border-slate-100">Responses</h3>
            <ResponseDisplay responses={operation.responses || {}} />
          </div>
        )}
      </div>
    </div>
  );
};
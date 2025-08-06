import React, { memo } from 'react';

export const LoadingIndicator = memo(({ message = "Loading..." }) => {
    return (
        <div 
            className="flex flex-col items-center justify-center p-8 max-w-md mx-auto"
            role="status"
            aria-live="polite"
        >
            <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-sky-500 mb-4"></div>
            <div className="text-xl text-sky-700 font-medium text-center">{message}</div>
            <p className="text-sm text-sky-600 mt-2">Please wait while we fetch your data</p>
        </div>
    );
});

LoadingIndicator.displayName = 'LoadingIndicator';
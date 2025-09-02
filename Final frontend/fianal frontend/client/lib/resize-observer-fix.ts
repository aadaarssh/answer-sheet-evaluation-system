// Fix for ResizeObserver loop error
// This is a common issue with UI libraries that use ResizeObserver

let resizeObserverErrorFixed = false;

export const fixResizeObserverError = () => {
  if (resizeObserverErrorFixed) return;
  
  resizeObserverErrorFixed = true;

  // Store original ResizeObserver
  const OriginalResizeObserver = window.ResizeObserver;

  // Create a wrapper that catches and ignores the loop error
  window.ResizeObserver = class extends OriginalResizeObserver {
    constructor(callback: ResizeObserverCallback) {
      super((entries, observer) => {
        try {
          callback(entries, observer);
        } catch (error) {
          // Ignore ResizeObserver loop errors
          if (error instanceof Error && error.message.includes('ResizeObserver loop completed with undelivered notifications')) {
            return;
          }
          throw error;
        }
      });
    }
  };

  // Also handle errors that might bubble up
  const handleError = (event: ErrorEvent) => {
    if (event.message?.includes('ResizeObserver loop completed with undelivered notifications')) {
      event.preventDefault();
      event.stopImmediatePropagation();
      return false;
    }
  };

  window.addEventListener('error', handleError, true);

  // Return cleanup function
  return () => {
    window.ResizeObserver = OriginalResizeObserver;
    window.removeEventListener('error', handleError, true);
    resizeObserverErrorFixed = false;
  };
};

// Auto-fix on import
if (typeof window !== 'undefined') {
  fixResizeObserverError();
}

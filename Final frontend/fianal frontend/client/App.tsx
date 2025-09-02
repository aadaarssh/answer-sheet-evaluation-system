import "./global.css";
import "@/lib/resize-observer-fix";

import { Toaster } from "@/components/ui/toaster";
import { createRoot } from "react-dom/client";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import IndexReal from "./pages/IndexReal";
import LoginReal from "./pages/LoginReal";
import NotFound from "./pages/NotFound";
import { useEffect, useState } from "react";
import { authApi } from "./services/api";

const queryClient = new QueryClient();

// Suppress ResizeObserver errors globally
const suppressResizeObserverErrors = () => {
  // Override console.error to filter out ResizeObserver warnings
  const originalConsoleError = console.error;
  console.error = (...args: any[]) => {
    const errorMessage = args[0]?.toString() || '';
    if (errorMessage.includes('ResizeObserver loop completed with undelivered notifications')) {
      return;
    }
    originalConsoleError.apply(console, args);
  };

  // Handle unhandled errors
  const handleError = (event: ErrorEvent) => {
    if (event.message?.includes('ResizeObserver loop completed with undelivered notifications')) {
      event.preventDefault();
      event.stopPropagation();
      return false;
    }
  };

  // Handle unhandled promise rejections
  const handleRejection = (event: PromiseRejectionEvent) => {
    if (event.reason?.message?.includes('ResizeObserver loop completed with undelivered notifications')) {
      event.preventDefault();
      return false;
    }
  };

  window.addEventListener('error', handleError);
  window.addEventListener('unhandledrejection', handleRejection);

  return () => {
    console.error = originalConsoleError;
    window.removeEventListener('error', handleError);
    window.removeEventListener('unhandledrejection', handleRejection);
  };
};

// Initialize error suppression immediately
suppressResizeObserverErrors();

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState<{name: string; email: string} | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already authenticated
    const checkAuth = async () => {
      try {
        if (authApi.isAuthenticated()) {
          const user = await authApi.getCurrentUser();
          setCurrentUser({ name: user.full_name, email: user.email });
          setIsAuthenticated(true);
        }
      } catch (error) {
        console.log('Not authenticated');
        authApi.logout();
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const handleLogin = async (name: string, email: string) => {
    setCurrentUser({ name, email });
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    authApi.logout();
    setCurrentUser(null);
    setIsAuthenticated(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-600 via-blue-600 to-purple-800">
        <div className="text-white text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={
              isAuthenticated && currentUser ? 
                <IndexReal currentUser={currentUser} onLogout={handleLogout} /> : 
                <LoginReal onLogin={handleLogin} />
            } />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

createRoot(document.getElementById("root")!).render(<App />);

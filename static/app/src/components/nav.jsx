import React, { useState, useMemo, useEffect, useRef } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { API_HOST } from "../services/apiService";

export function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const sidebarRef = useRef(null);

  const isActive = (path) => {
    return location.pathname === path;
  };

  // Dynamic nav items based on authentication status
  const navItems = useMemo(() => {
    const items = {
      "/": "Forecast",
      "/docs": "Docs",
      [`http://${API_HOST}:8668/docs`]: "Sandbox",
    };
    
    // Add login link for unauthenticated users
    if (!user) {
      items["/login"] = "Login";
    }
    
    return items;
  }, [user]);

  const handleLogout = async () => {
    await logout();
    navigate("/login");
    setIsUserMenuOpen(false);
    setIsSidebarOpen(false);
  };

  // Close sidebar when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (sidebarRef.current && !sidebarRef.current.contains(event.target)) {
        setIsSidebarOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // Prevent scrolling when sidebar is open
  useEffect(() => {
    if (isSidebarOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'auto';
    }
    
    return () => {
      document.body.style.overflow = 'auto';
    };
  }, [isSidebarOpen]);

  return (
    <header className="bg-slate-800 shadow-lg sticky top-0 z-50 w-full">
      <div className="container mx-auto px-4">
        <nav className="flex items-center justify-between h-16">
          {/* Logo and brand */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2 group">
              <div className="h-9 w-9 bg-sky-500 rounded-lg flex items-center justify-center group-hover:bg-sky-500 transition-colors">
                <img src="/assets/logo.svg" alt="Logo" className="h-6 w-6 text-white" />
              </div>
              <span className="text-xl text-white font-bold group-hover:text-sky-300 transition-colors">
                NotSoFancyWeather
              </span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-1">
            {Object.entries(navItems).map(([path, name]) => (
              <Link
                key={path}
                to={path}
                className={`
                  px-4 py-2 rounded-md font-medium transition-all
                  ${isActive(path) 
                    ? "bg-sky-600 text-white" 
                    : "text-gray-300 hover:text-white hover:bg-slate-700"}
                `}
              >
                {name}
              </Link>
            ))}
            
            {/* User menu - only show when logged in */}
            {user && (
              <div className="relative ml-3">
                <button
                  type="button"
                  className="flex items-center max-w-xs text-sm bg-slate-700 rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500"
                  id="user-menu-button"
                  aria-expanded={isUserMenuOpen}
                  aria-haspopup="true"
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                >
                  <span className="sr-only">Open user menu</span>
                  <div className="h-8 w-8 rounded-full bg-sky-500 flex items-center justify-center text-white font-semibold">
                    {user.username ? user.username.charAt(0).toUpperCase() : "U"}
                  </div>
                </button>
                
                {/* Dropdown menu */}
                {isUserMenuOpen && (
                  <div
                    className="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none"
                    role="menu"
                    aria-orientation="vertical"
                    aria-labelledby="user-menu-button"
                    tabIndex="-1"
                  >
                    <div className="py-1" role="none">
                      <Link
                        to="/profile"
                        onClick={() => setIsUserMenuOpen(false)}
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        role="menuitem"
                      >
                        Your Profile
                      </Link>
                      <button
                        onClick={handleLogout}
                        className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        role="menuitem"
                        tabIndex="-1"
                      >
                        Sign out
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button 
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="text-gray-300 hover:text-white focus:outline-none"
              aria-expanded={isSidebarOpen}
            >
              <span className="sr-only">Open main menu</span>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {isSidebarOpen 
                  ? <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  : <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                }
              </svg>
            </button>
          </div>
        </nav>

        {/* Mobile Sidebar Navigation */}
        <div className={`fixed inset-0 z-50 md:hidden ${isSidebarOpen ? 'visible' : 'invisible'} transition-visibility duration-300`}>
          {/* Overlay */}
          <div 
            className={`fixed inset-0 bg-black ${isSidebarOpen ? 'opacity-50' : 'opacity-0'} transition-opacity duration-300`} 
            onClick={() => setIsSidebarOpen(false)} 
            aria-hidden="true"
          ></div>
          
          {/* Sidebar */}
          <div 
            ref={sidebarRef} 
            className={`absolute top-0 right-0 flex flex-col w-full max-w-xs h-full bg-slate-800 border-l border-slate-700 shadow-xl transform ${
              isSidebarOpen ? 'translate-x-0' : 'translate-x-full'
            } transition-transform duration-300 ease-in-out`}
          >
            {/* Close button - moved to top of container */}
            <div className="flex justify-end p-2 border-b border-slate-700">
              <button 
                onClick={() => setIsSidebarOpen(false)}
                className="text-gray-300 hover:text-white p-2 rounded-md"
                aria-label="Close sidebar"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="flex-1 pt-2 pb-4 overflow-y-auto">
              {/* Profile section at the top */}
              {user ? (
                <div className="px-4">
                  <Link to="/profile" onClick={() => setIsSidebarOpen(false)}>
                    <div className="flex items-center p-4 mb-2 bg-slate-700 rounded-lg">
                      <div className="h-10 w-10 rounded-full bg-sky-500 flex items-center justify-center text-white font-semibold">
                        {user.username ? user.username.charAt(0).toUpperCase() : "U"}
                      </div>
                      <div className="ml-3">
                        <p className="text-base font-medium text-white">{user.username || "User"}</p>
                        <p className="text-sm text-gray-300">View Profile</p>
                      </div>
                    </div>
                  </Link>
                </div>
              ) : (
                <div className="flex items-center px-6">
                  <div className="h-9 w-9 bg-sky-500 rounded-lg flex items-center justify-center">
                    <img src="/assets/logo.svg" alt="Logo" className="h-6 w-6 text-white" />
                  </div>
                  <span className="ml-2 text-xl text-white font-bold">NotSoFancyWeather</span>
                </div>
              )}
              
              {/* Navigation Links */}
              <nav className="mt-5 px-4 space-y-2">
                {Object.entries(navItems).map(([path, name]) => (
                  <Link
                    key={path}
                    to={path}
                    className={`
                      group flex items-center px-4 py-3 rounded-md font-medium transition-all
                      ${isActive(path) 
                        ? "bg-sky-600 text-white" 
                        : "text-gray-300 hover:text-white hover:bg-slate-700"}
                    `}
                    onClick={() => setIsSidebarOpen(false)}
                  >
                    {name}
                  </Link>
                ))}
                
                {/* Only show profile and logout for logged in users */}
                {user && (
                  <>
                    <Link
                      to="/profile"
                      className={`
                        group flex items-center px-4 py-3 rounded-md font-medium transition-all
                        ${isActive("/profile") 
                          ? "bg-sky-600 text-white" 
                          : "text-gray-300 hover:text-white hover:bg-slate-700"}
                      `}
                      onClick={() => setIsSidebarOpen(false)}
                    >
                      Your Profile
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="w-full group flex items-center px-4 py-3 rounded-md font-medium transition-all text-gray-300 hover:text-white hover:bg-slate-700"
                    >
                      Sign out
                    </button>
                  </>
                )}
              </nav>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
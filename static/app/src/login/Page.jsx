import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useAuthGuard } from "../hooks/useAuthGuard";

export const LoginPage = () => {
    // Ensure only non-authenticated users can access this page
    useAuthGuard(false, '/');
    
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [rememberMe, setRememberMe] = useState(false);
    const [formError, setFormError] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    
    const { login, error: authError } = useAuth();
    const navigate = useNavigate();

    // Clear form error when inputs change
    useEffect(() => {
        if (formError) {
            setFormError("");
        }
    }, [username, password]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setFormError("");
        
        // Basic form validation
        if (!username.trim()) {
            setFormError("Username is required");
            return;
        }
        
        if (!password) {
            setFormError("Password is required");
            return;
        }
        
        try {
            setIsSubmitting(true);
            const success = await login(username, password);
            
            if (success) {
                // Redirect to home/dashboard page after successful login
                navigate("/");
            }
        } catch (err) {
            setFormError(err.message || "Login failed. Please try again.");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-b from-sky-600 to-sky-400 py-16 flex items-center justify-center">
            <div className="container max-w-md mx-auto px-6">
                <div className="bg-white rounded-xl shadow-xl overflow-hidden">
                    <div className="bg-gradient-to-r from-sky-700 to-sky-800 p-6">
                        <h1 className="text-3xl font-bold text-white text-center drop-shadow-md">
                            Welcome Back
                        </h1>
                        <p className="text-sky-100 text-center mt-2">
                            Enter your credentials to access your account
                        </p>
                    </div>
                    
                    {(formError || authError) && (
                        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mt-2" role="alert">
                            <p>{formError || authError}</p>
                        </div>
                    )}
                    
                    <form className="p-6 space-y-4" onSubmit={handleSubmit}>
                        <div className="mb-4">
                            <label htmlFor="username" className="block text-gray-700 text-sm font-medium mb-1">
                                Username
                            </label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                    </svg>
                                </div>
                                <input
                                    type="text"
                                    id="username"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    placeholder="johndoe"
                                    className="w-full pl-10 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
                                    disabled={isSubmitting}
                                    aria-label="Username"
                                    required
                                />
                            </div>
                        </div>
                        <div className="mb-4">
                            <label htmlFor="password" className="block text-gray-700 text-sm font-medium mb-1">
                                Password
                            </label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                    </svg>
                                </div>
                                <input
                                    type="password"
                                    id="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="••••••"
                                    className="w-full pl-10 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
                                    disabled={isSubmitting}
                                    aria-label="Password"
                                    required
                                />
                            </div>
                        </div>
                        <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center">
                                <input 
                                    id="remember" 
                                    type="checkbox" 
                                    checked={rememberMe}
                                    onChange={(e) => setRememberMe(e.target.checked)}
                                    className="h-4 w-4 text-sky-600 focus:ring-sky-500 border-gray-300 rounded" 
                                    aria-label="Remember me"
                                />
                                <label htmlFor="remember" className="ml-2 block text-sm text-gray-700">
                                    Remember me
                                </label>
                            </div>
                            <div className="text-sm">
                                <a href="#" className="font-medium text-sky-600 hover:text-sky-800">
                                    Forgot password?
                                </a>
                            </div>
                        </div>
                        <button 
                            type="submit" 
                            className="w-full py-3 px-4 bg-sky-600 text-white font-medium rounded-lg hover:bg-sky-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500 transition duration-200 shadow-md disabled:opacity-70"
                            disabled={isSubmitting}
                        >
                            {isSubmitting ? (
                                <span className="flex items-center justify-center">
                                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Logging in...
                                </span>
                            ) : (
                                "Login"
                            )}
                        </button>
                        <div className="text-sm text-center text-gray-600 mt-6">
                            Don't have an account yet? <Link to="/signup" className="font-medium text-sky-600 hover:text-sky-800">Sign up</Link>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}
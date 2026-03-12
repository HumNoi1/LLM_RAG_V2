    'use client';

    import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

    // ─── Types ────────────────────────────────────────────────────────────────────
    export interface User {
    id?: string;
    email: string;
    name?: string;
    teacherId?: string;
    }

    export interface AuthContextType {
    user: User | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    login: (email: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
    register: (email: string, password: string, name: string, teacherId: string) => Promise<void>;
    error: string | null;
    }

    // ─── Context ──────────────────────────────────────────────────────────────────
    const AuthContext = createContext<AuthContextType | undefined>(undefined);

    // ─── Provider ─────────────────────────────────────────────────────────────────
    export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Check if user is already logged in on mount
    useEffect(() => {
        const checkAuth = async () => {
        try {
            const token = typeof window !== 'undefined' ? localStorage.getItem('authToken') : null;
            if (token) {
            // In a real app, verify token with backend
            const userData = localStorage.getItem('user');
            if (userData) {
                setUser(JSON.parse(userData));
            }
            }
        } catch (err) {
            console.error('Auth check failed:', err);
        } finally {
            setIsLoading(false);
        }
        };

        checkAuth();
    }, []);

    const login = async (email: string, password: string) => {
        setIsLoading(true);
        setError(null);
        try {
        // TODO: Replace with actual API call
        // const response = await fetch('/api/auth/login', {
        //   method: 'POST',
        //   headers: { 'Content-Type': 'application/json' },
        //   body: JSON.stringify({ email, password }),
        // });
        // const data = await response.json();

        // Mock successful login
        const mockUser: User = {
            id: '1',
            email,
            name: 'อ.สมชาย ใจดี',
            teacherId: 'T123456',
        };

        setUser(mockUser);
        if (typeof window !== 'undefined') {
            localStorage.setItem('authToken', 'mock-token-123');
            localStorage.setItem('user', JSON.stringify(mockUser));
        }
        } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Login failed';
        setError(errorMessage);
        throw err;
        } finally {
        setIsLoading(false);
        }
    };

    const logout = async () => {
        setIsLoading(true);
        setError(null);
        try {
        // TODO: Replace with actual API call
        // await fetch('/api/auth/logout', { method: 'POST' });

        setUser(null);
        if (typeof window !== 'undefined') {
            localStorage.removeItem('authToken');
            localStorage.removeItem('user');
        }
        } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Logout failed';
        setError(errorMessage);
        throw err;
        } finally {
        setIsLoading(false);
        }
    };

    const register = async (email: string, password: string, name: string, teacherId: string) => {
        setIsLoading(true);
        setError(null);
        try {
        // TODO: Replace with actual API call
        // const response = await fetch('/api/auth/register', {
        //   method: 'POST',
        //   headers: { 'Content-Type': 'application/json' },
        //   body: JSON.stringify({ email, password, name, teacherId }),
        // });
        // const data = await response.json();

        // Mock successful registration
        const mockUser: User = {
            id: '2',
            email,
            name,
            teacherId,
        };

        setUser(mockUser);
        if (typeof window !== 'undefined') {
            localStorage.setItem('authToken', 'mock-token-456');
            localStorage.setItem('user', JSON.stringify(mockUser));
        }
        } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Registration failed';
        setError(errorMessage);
        throw err;
        } finally {
        setIsLoading(false);
        }
    };

    const value: AuthContextType = {
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
        register,
        error,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
    }

    // ─── Hook ────────────────────────────────────────────────────────────────────
    export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
    }

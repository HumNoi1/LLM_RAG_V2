    'use client';

    import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
    import api from '@/lib/api';

    // ─── Types ────────────────────────────────────────────────────────────────────
    export interface User {
    id?: string;
    email: string;
    full_name?: string;
    role?: string;
    }

    export interface AuthContextType {
    user: User | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    login: (email: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
    register: (email: string, password: string, full_name: string) => Promise<void>;
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
            // Try to fetch user profile from backend
            try {
                const res = await api.get('/auth/me');
                setUser(res.data);
                localStorage.setItem('user', JSON.stringify(res.data));
            } catch {
                // Token invalid, clear storage
                localStorage.removeItem('authToken');
                localStorage.removeItem('refreshToken');
                localStorage.removeItem('user');
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
        const loginRes = await api.post('/auth/login', { email, password });
        const { access_token, refresh_token } = loginRes.data;

        localStorage.setItem('authToken', access_token);
        localStorage.setItem('refreshToken', refresh_token);

        const meRes = await api.get('/auth/me', {
            headers: { Authorization: `Bearer ${access_token}` },
        });
        setUser(meRes.data);
        localStorage.setItem('user', JSON.stringify(meRes.data));
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
        setUser(null);
        if (typeof window !== 'undefined') {
            localStorage.removeItem('authToken');
            localStorage.removeItem('refreshToken');
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

    const register = async (email: string, password: string, full_name: string) => {
        setIsLoading(true);
        setError(null);
        try {
        const registerRes = await api.post('/auth/register', {
            email,
            password,
            full_name,
            role: 'teacher',
        });

        // Auto-login after registration
        const loginRes = await api.post('/auth/login', { email, password });
        const { access_token, refresh_token } = loginRes.data;

        localStorage.setItem('authToken', access_token);
        localStorage.setItem('refreshToken', refresh_token);

        setUser(registerRes.data);
        localStorage.setItem('user', JSON.stringify(registerRes.data));
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

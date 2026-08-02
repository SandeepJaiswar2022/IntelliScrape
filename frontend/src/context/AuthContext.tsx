import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { loginRequest, logoutRequest, refreshRequest, registerRequest } from "../lib/authApi";
import type { User } from "../types/auth";

interface AuthContextValue {
    user: User | null;
    accessToken: string | null;
    /**
     * True only during the initial silent-refresh attempt on app load.
     * Route guards (ProtectedRoute/AdminRoute) wait for this to become
     * false before deciding to redirect -- otherwise a logged-in user
     * would see a flash-redirect to /login on every page reload, before
     * the refresh had a chance to succeed.
     */
    isInitializing: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (email: string, password: string, fullName: string) => Promise<void>;
    logout: () => Promise<void>;
    /**
     * Clears local session state WITHOUT calling the backend. Used when
     * a request comes back 401 mid-session (the access token expired
     * naturally) -- at that point there is nothing meaningful left to
     * revoke by calling /auth/logout again; we just need the frontend to
     * stop believing it has a valid session, which sends the user back
     * to /login via the route guards on next render.
     */
    clearSession: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [accessToken, setAccessToken] = useState<string | null>(null);
    const [isInitializing, setIsInitializing] = useState(true);

    // On first mount, try to silently exchange the HttpOnly refresh
    // cookie (if any) for a fresh access token. This is what makes a
    // session survive a page reload despite the access token living
    // only in memory (never localStorage -- see lib/authApi.ts). A
    // failure here just means "nobody is logged in" -- not an error to
    // show anyone.
    useEffect(() => {
        let cancelled = false;

        async function restoreSession() {
            try {
                const response = await refreshRequest();
                if (!cancelled) {
                    setUser(response.user);
                    setAccessToken(response.access_token);
                }
            } catch {
                if (!cancelled) {
                    setUser(null);
                    setAccessToken(null);
                }
            } finally {
                if (!cancelled) {
                    setIsInitializing(false);
                }
            }
        }

        restoreSession();
        return () => {
            cancelled = true;
        };
    }, []);

    async function login(email: string, password: string) {
        const response = await loginRequest(email, password);
        setUser(response.user);
        setAccessToken(response.access_token);
    }

    async function register(email: string, password: string, fullName: string) {
        const response = await registerRequest(email, password, fullName);
        setUser(response.user);
        setAccessToken(response.access_token);
    }

    async function logout() {
        try {
            await logoutRequest();
        } finally {
            // Clear local state regardless of whether the backend call
            // succeeded -- a failed logout request shouldn't leave the user
            // stuck appearing logged in on their own screen.
            setUser(null);
            setAccessToken(null);
        }
    }

    function clearSession() {
        setUser(null);
        setAccessToken(null);
    }

    return (
        <AuthContext.Provider
            value={{ user, accessToken, isInitializing, login, register, logout, clearSession }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth(): AuthContextValue {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}
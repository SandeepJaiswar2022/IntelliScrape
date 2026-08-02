import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

/**
 * Wraps a route that requires ANY authenticated user (USER or ADMIN).
 * Waits for `isInitializing` to resolve before deciding -- see
 * AuthContext's docstring on that field for why.
 */
export function ProtectedRoute({ children }: { children: ReactNode }) {
    const { user, isInitializing } = useAuth();

    if (isInitializing) {
        return null; // brief, deliberately blank -- avoids a flash of "redirecting..." for the common case where the session restores successfully
    }

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    return <>{children}</>;
}

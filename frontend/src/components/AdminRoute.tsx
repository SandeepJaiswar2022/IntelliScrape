import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ROLE } from "../types/auth";

/**
 * Wraps a route that requires the ADMIN role specifically.
 *
 * This check is UI/UX only -- it prevents a non-admin from seeing the
 * admin dashboard's controls, but it is NOT what actually protects the
 * admin API. The real enforcement is server-side
 * (`require_admin` on POST /api/v1/admin/scrape), which is checked
 * fresh on every request regardless of what this component decides.
 * A user could disable JavaScript and never see this check at all --
 * the backend would still correctly reject them with a 403.
 */
export function AdminRoute({ children }: { children: ReactNode }) {
    const { user, isInitializing } = useAuth();

    if (isInitializing) {
        return null;
    }

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    if (user.role !== ROLE.ADMIN) {
        return <Navigate to="/unauthorized" replace />;
    }

    return <>{children}</>;
}
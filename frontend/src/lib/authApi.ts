import type { AccessTokenResponse, MessageResponse } from "../types/auth";
import { ApiError } from "./api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

/**
 * Every call here uses `credentials: "include"` -- this is what makes
 * the browser send/accept the HttpOnly refresh-token cookie on
 * requests to the backend, including when frontend and backend are on
 * different origins (e.g. Vercel talking to Render). Without this,
 * the cookie is silently never sent, and refresh/logout would appear
 * to work (no error) while doing nothing.
 */

export async function registerRequest(
    email: string,
    password: string,
    fullName: string
): Promise<AccessTokenResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password, full_name: fullName }),
    });

    if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new ApiError(extractErrorMessage(body, response.status), response.status);
    }

    return response.json() as Promise<AccessTokenResponse>;
}

export async function loginRequest(email: string, password: string): Promise<AccessTokenResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new ApiError(extractErrorMessage(body, response.status), response.status);
    }

    return response.json() as Promise<AccessTokenResponse>;
}

/**
 * Attempts to exchange the HttpOnly refresh cookie for a new access
 * token. Called once on app load (see AuthContext) to restore a
 * session after a page reload -- the access token itself only ever
 * lives in memory (never localStorage), so a reload always loses it;
 * this is how the session survives that without a full re-login.
 * A failure here (401, or no cookie at all) is the normal, expected
 * shape of "nobody is logged in" -- callers should not treat it as an
 * error to surface to the user.
 */
export async function refreshRequest(): Promise<AccessTokenResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
        method: "POST",
        credentials: "include",
    });

    if (!response.ok) {
        throw new ApiError("Not authenticated", response.status);
    }

    return response.json() as Promise<AccessTokenResponse>;
}

export async function logoutRequest(): Promise<MessageResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
        method: "POST",
        credentials: "include",
    });

    if (!response.ok) {
        throw new ApiError("Logout failed", response.status);
    }

    return response.json() as Promise<MessageResponse>;
}

/**
 * FastAPI's validation errors come back as either a single `detail`
 * string (our own HTTPException calls) or a list of per-field error
 * objects (Pydantic validation failures, e.g. weak password). This
 * normalizes both into one readable string instead of the frontend
 * ever showing "[object Object]".
 */
function extractErrorMessage(body: unknown, status: number): string {
    if (body && typeof body === "object" && "detail" in body) {
        const detail = (body as { detail: unknown }).detail;
        if (typeof detail === "string") return detail;
        if (Array.isArray(detail)) {
            return detail
                .map((err) => (typeof err === "object" && err && "msg" in err ? String(err.msg) : String(err)))
                .join(", ");
        }
    }
    return `Request failed (${status})`;
}
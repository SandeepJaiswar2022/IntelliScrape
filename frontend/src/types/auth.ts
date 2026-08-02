/**
 * Mirrors app/schemas/auth.py on the backend exactly -- keep these in
 * sync whenever the API response shape changes.
 */

export const ROLE = {
    USER: "USER",
    ADMIN: "ADMIN",
} as const;

export interface User {
    id: string;
    email: string;
    full_name: string;
    is_active: boolean;
    is_verified: boolean;
    role: string;
    created_at: string;
}

export interface AccessTokenResponse {
    access_token: string;
    token_type: string;
    expires_in_minutes: number;
    user: User;
}

export interface MessageResponse {
    message: string;
}
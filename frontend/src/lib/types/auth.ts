/**
 * Authentication related type definitions
 */

export interface GoogleAuthURL {
	auth_url: string;
	state: string;
}

export interface UserResponse {
	google_id: string;
	email: string;
	name: string;
	picture?: string;
	user_role: string;
	created_at: string;
	updated_at: string;
}

export interface AuthError {
	detail: string;
}

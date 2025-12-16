/**
 * Authentication HTTP API client for Payroll Frontend
 */

import type { GoogleAuthURL, UserResponse } from '$lib/types/auth';
import { BaseAPI } from './base';

class AuthAPI extends BaseAPI {
	/**
	 * Initiate Google OAuth login
	 * Automatically includes current frontend URL as redirect_frontend for proper OAuth callback
	 */
	async initiateGoogleLogin(): Promise<GoogleAuthURL> {
		// Get current origin for redirect_frontend (e.g., http://localhost:5175)
		const redirectFrontend = typeof window !== 'undefined' ? window.location.origin : undefined;

		const params: Record<string, string> = {};
		if (redirectFrontend) {
			params.redirect_frontend = redirectFrontend;
		}

		const response = await this.get<GoogleAuthURL>('/auth/login/google', params);
		return response;
	}

	/**
	 * Get current authenticated user
	 */
	async getCurrentUser(): Promise<UserResponse> {
		const response = await this.get<UserResponse>('/auth/me');
		return response;
	}

	/**
	 * Logout current user
	 */
	async logout(): Promise<void> {
		try {
			await this.post<void>('/auth/logout');
		} catch {
			// Ignore logout errors
		}
	}

	/**
	 * Refresh authentication token
	 */
	async refreshToken(): Promise<void> {
		await this.post<void>('/auth/refresh');
	}

	/**
	 * Check if user is authenticated
	 */
	async checkAuth(): Promise<UserResponse | null> {
		try {
			return await this.getCurrentUser();
		} catch {
			return null;
		}
	}
}

export const authAPI = new AuthAPI();

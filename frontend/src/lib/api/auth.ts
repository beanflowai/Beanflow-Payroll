/**
 * Authentication HTTP API client for Payroll Frontend
 * Used for backend API calls that require authentication
 */

import type { UserResponse } from '$lib/types/auth';
import { BaseAPI } from './base';

class AuthAPI extends BaseAPI {
	/**
	 * Get current authenticated user from backend
	 */
	async getCurrentUser(): Promise<UserResponse> {
		const response = await this.get<UserResponse>('/auth/me');
		return response;
	}

	/**
	 * Check if user is authenticated with backend
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

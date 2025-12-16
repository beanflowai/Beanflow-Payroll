/**
 * Authentication Store for Payroll Frontend
 * Uses Svelte 5 Runes and backend API for auth
 */

import { browser } from '$app/environment';
import { authAPI } from '$lib/api/auth';
import type { UserResponse } from '$lib/types/auth';

// Auth state using module-level state
let _user = $state<UserResponse | null>(null);
let _isLoading = $state(true);
let _isAuthenticated = $state(false);
let _error = $state<string | null>(null);

/**
 * Initialize auth state by checking current session
 */
export async function initializeAuth(): Promise<void> {
	if (!browser) return;

	_isLoading = true;
	_error = null;

	try {
		const user = await authAPI.checkAuth();

		if (user) {
			_user = user;
			_isAuthenticated = true;
		} else {
			_user = null;
			_isAuthenticated = false;
		}
	} catch (err) {
		_error = err instanceof Error ? err.message : 'Failed to initialize authentication';
		_user = null;
		_isAuthenticated = false;
	} finally {
		_isLoading = false;
	}
}

/**
 * Login with Google OAuth via backend API
 */
export async function login(): Promise<void> {
	if (!browser) return;

	_isLoading = true;
	_error = null;

	try {
		const { auth_url } = await authAPI.initiateGoogleLogin();
		// Redirect to Google OAuth
		window.location.href = auth_url;
	} catch (err) {
		_error = err instanceof Error ? err.message : 'Failed to login';
		_isLoading = false;
	}
}

/**
 * Logout current user
 */
export async function logout(): Promise<void> {
	if (!browser) return;

	_isLoading = true;
	_error = null;

	try {
		await authAPI.logout();
		_user = null;
		_isAuthenticated = false;
	} catch (err) {
		_error = err instanceof Error ? err.message : 'Failed to logout';
	} finally {
		_isLoading = false;
	}
}

/**
 * Clear authentication error
 */
export function clearError(): void {
	_error = null;
}

// Export reactive getters
export const authState = {
	get user() {
		return _user;
	},
	get isLoading() {
		return _isLoading;
	},
	get isAuthenticated() {
		return _isAuthenticated;
	},
	get error() {
		return _error;
	}
};

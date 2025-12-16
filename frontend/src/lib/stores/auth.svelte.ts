/**
 * Authentication Store for Payroll Frontend
 * Uses Svelte 5 Runes and Supabase Auth SDK
 */

import { browser } from '$app/environment';
import { supabase } from '$lib/api/supabase';
import type { User } from '@supabase/supabase-js';

// Auth state using module-level state
let _user = $state<User | null>(null);
let _isLoading = $state(true);
let _isAuthenticated = $state(false);
let _error = $state<string | null>(null);

/**
 * Initialize auth state by checking current session and listening for changes
 */
export async function initializeAuth(): Promise<void> {
	if (!browser) return;

	_isLoading = true;
	_error = null;

	try {
		// Get current session
		const {
			data: { session }
		} = await supabase.auth.getSession();

		if (session?.user) {
			_user = session.user;
			_isAuthenticated = true;
		} else {
			_user = null;
			_isAuthenticated = false;
		}

		// Listen for auth state changes
		supabase.auth.onAuthStateChange((_event, session) => {
			if (session?.user) {
				_user = session.user;
				_isAuthenticated = true;
			} else {
				_user = null;
				_isAuthenticated = false;
			}
			_isLoading = false;
		});
	} catch (err) {
		_error = err instanceof Error ? err.message : 'Failed to initialize authentication';
		_user = null;
		_isAuthenticated = false;
	} finally {
		_isLoading = false;
	}
}

/**
 * Login with Google OAuth via Supabase Auth
 */
export async function login(): Promise<void> {
	if (!browser) return;

	_isLoading = true;
	_error = null;

	try {
		const { error } = await supabase.auth.signInWithOAuth({
			provider: 'google',
			options: {
				redirectTo: `${window.location.origin}/auth/callback`
			}
		});

		if (error) {
			_error = error.message;
			_isLoading = false;
		}
		// If successful, browser will redirect to Google OAuth
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
		const { error } = await supabase.auth.signOut();
		if (error) {
			_error = error.message;
		} else {
			_user = null;
			_isAuthenticated = false;
		}
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

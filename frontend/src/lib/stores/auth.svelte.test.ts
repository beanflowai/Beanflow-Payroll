/**
 * Tests for auth store
 *
 * Note: These tests mock the browser environment and Supabase client
 * to test the auth store logic without requiring actual browser APIs.
 */

import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

// Mock $app/environment
vi.mock('$app/environment', () => ({
	browser: true
}));

// Mock company store
vi.mock('./company.svelte', () => ({
	clearCompanyContext: vi.fn()
}));

// Mock supabase
vi.mock('$lib/api/supabase', () => ({
	supabase: {
		auth: {
			getSession: vi.fn(),
			onAuthStateChange: vi.fn(),
			signInWithOAuth: vi.fn(),
			signOut: vi.fn()
		}
	}
}));

import { supabase } from '$lib/api/supabase';
import { clearCompanyContext } from './company.svelte';
import { initializeAuth, login, logout, clearError, authState } from './auth.svelte';

const mockSupabase = vi.mocked(supabase);
const mockClearCompanyContext = vi.mocked(clearCompanyContext);

// Mock window.location
const originalLocation = window.location;
beforeEach(() => {
	Object.defineProperty(window, 'location', {
		writable: true,
		value: { origin: 'http://localhost:5173' }
	});
});

afterEach(() => {
	Object.defineProperty(window, 'location', {
		writable: true,
		value: originalLocation
	});
});

describe('initializeAuth', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('initializes with existing session', async () => {
		const mockUser = { id: 'user-123', email: 'test@example.com' };
		mockSupabase.auth.getSession.mockResolvedValue({
			data: { session: { user: mockUser } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);
		mockSupabase.auth.onAuthStateChange.mockReturnValue({
			data: { subscription: { unsubscribe: vi.fn() } }
		} as unknown as ReturnType<typeof supabase.auth.onAuthStateChange>);

		await initializeAuth();

		expect(mockSupabase.auth.getSession).toHaveBeenCalled();
		expect(authState.isAuthenticated).toBe(true);
		expect(authState.user?.id).toBe('user-123');
	});

	it('initializes with no session', async () => {
		mockSupabase.auth.getSession.mockResolvedValue({
			data: { session: null },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);
		mockSupabase.auth.onAuthStateChange.mockReturnValue({
			data: { subscription: { unsubscribe: vi.fn() } }
		} as unknown as ReturnType<typeof supabase.auth.onAuthStateChange>);

		await initializeAuth();

		expect(authState.isAuthenticated).toBe(false);
		expect(authState.user).toBeNull();
	});

	it('handles error during initialization', async () => {
		mockSupabase.auth.getSession.mockRejectedValue(new Error('Auth service unavailable'));

		await initializeAuth();

		expect(authState.error).toBe('Auth service unavailable');
		expect(authState.isAuthenticated).toBe(false);
	});

	it('sets up auth state change listener', async () => {
		mockSupabase.auth.getSession.mockResolvedValue({
			data: { session: null },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);
		mockSupabase.auth.onAuthStateChange.mockReturnValue({
			data: { subscription: { unsubscribe: vi.fn() } }
		} as unknown as ReturnType<typeof supabase.auth.onAuthStateChange>);

		await initializeAuth();

		expect(mockSupabase.auth.onAuthStateChange).toHaveBeenCalled();
	});
});

describe('login', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('initiates OAuth login with Google', async () => {
		mockSupabase.auth.signInWithOAuth.mockResolvedValue({
			data: { url: 'https://google.com/oauth', provider: 'google' },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.signInWithOAuth>);

		await login();

		expect(mockSupabase.auth.signInWithOAuth).toHaveBeenCalledWith({
			provider: 'google',
			options: {
				redirectTo: 'http://localhost:5173/auth/callback'
			}
		});
	});

	it('handles OAuth error', async () => {
		mockSupabase.auth.signInWithOAuth.mockResolvedValue({
			data: { url: null, provider: 'google' },
			error: { message: 'OAuth failed' }
		} as unknown as ReturnType<typeof supabase.auth.signInWithOAuth>);

		await login();

		expect(authState.error).toBe('OAuth failed');
	});

	it('handles unexpected error', async () => {
		mockSupabase.auth.signInWithOAuth.mockRejectedValue(new Error('Network error'));

		await login();

		expect(authState.error).toBe('Network error');
	});
});

describe('logout', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('logs out successfully', async () => {
		mockSupabase.auth.signOut.mockResolvedValue({ error: null });

		await logout();

		expect(mockSupabase.auth.signOut).toHaveBeenCalled();
		expect(authState.isAuthenticated).toBe(false);
		expect(authState.user).toBeNull();
		expect(mockClearCompanyContext).toHaveBeenCalled();
	});

	it('handles logout error', async () => {
		mockSupabase.auth.signOut.mockResolvedValue({
			error: { message: 'Logout failed' }
		} as unknown as ReturnType<typeof supabase.auth.signOut>);

		await logout();

		expect(authState.error).toBe('Logout failed');
	});

	it('handles unexpected logout error', async () => {
		mockSupabase.auth.signOut.mockRejectedValue(new Error('Network error'));

		await logout();

		expect(authState.error).toBe('Network error');
	});
});

describe('clearError', () => {
	it('clears the error state', async () => {
		// Set up an error first
		mockSupabase.auth.signInWithOAuth.mockResolvedValue({
			data: { url: null, provider: 'google' },
			error: { message: 'Test error' }
		} as unknown as ReturnType<typeof supabase.auth.signInWithOAuth>);

		await login();
		expect(authState.error).toBe('Test error');

		clearError();
		expect(authState.error).toBeNull();
	});
});

describe('authState', () => {
	it('exposes user getter', () => {
		expect(authState).toHaveProperty('user');
	});

	it('exposes isLoading getter', () => {
		expect(authState).toHaveProperty('isLoading');
	});

	it('exposes isAuthenticated getter', () => {
		expect(authState).toHaveProperty('isAuthenticated');
	});

	it('exposes error getter', () => {
		expect(authState).toHaveProperty('error');
	});
});

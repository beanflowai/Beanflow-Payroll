/**
 * Tests for API client
 */

import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock supabase
vi.mock('./supabase', () => ({
	supabase: {
		auth: {
			getSession: vi.fn()
		}
	}
}));

// Mock company store
vi.mock('$lib/stores/company.svelte', () => ({
	companyState: {
		currentCompany: { id: 'test-company-id' }
	}
}));

import { supabase } from './supabase';
import { APIError, apiClient, api } from './client';

const mockSupabase = vi.mocked(supabase);

describe('APIError', () => {
	it('creates error with message and status', () => {
		const error = new APIError('Not found', 404);

		expect(error.message).toBe('Not found');
		expect(error.status).toBe(404);
		expect(error.name).toBe('APIError');
	});

	it('creates error with details', () => {
		const error = new APIError('Validation failed', 400, { field: 'email' });

		expect(error.details).toEqual({ field: 'email' });
	});
});

describe('apiClient', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockSupabase.auth.getSession.mockResolvedValue({
			data: { session: { access_token: 'test-token' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	it('makes request with auth token', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			text: () => Promise.resolve(JSON.stringify({ id: 1 }))
		});

		await apiClient('/test');

		expect(mockFetch).toHaveBeenCalledWith(
			expect.stringContaining('/api/v1/test'),
			expect.objectContaining({
				headers: expect.objectContaining({
					Authorization: 'Bearer test-token'
				})
			})
		);
	});

	it('makes request with company ID header', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			text: () => Promise.resolve(JSON.stringify({ id: 1 }))
		});

		await apiClient('/test');

		expect(mockFetch).toHaveBeenCalledWith(
			expect.any(String),
			expect.objectContaining({
				headers: expect.objectContaining({
					'X-Company-Id': 'test-company-id'
				})
			})
		);
	});

	it('handles successful JSON response', async () => {
		const responseData = { id: 1, name: 'Test' };
		mockFetch.mockResolvedValueOnce({
			ok: true,
			text: () => Promise.resolve(JSON.stringify(responseData))
		});

		const result = await apiClient<{ id: number; name: string }>('/test');

		expect(result).toEqual(responseData);
	});

	it('handles empty response', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			text: () => Promise.resolve('')
		});

		const result = await apiClient('/test');

		expect(result).toEqual({});
	});

	it('handles standardized success response', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			text: () => Promise.resolve(JSON.stringify({ success: true, data: { id: 1 } }))
		});

		const result = await apiClient<{ id: number }>('/test');

		expect(result).toEqual({ id: 1 });
	});

	it('handles standardized error response', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			text: () => Promise.resolve(JSON.stringify({ success: false, error: 'Something went wrong' })),
			status: 200
		});

		await expect(apiClient('/test')).rejects.toThrow('Something went wrong');
	});

	it('throws APIError on HTTP error', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: false,
			status: 404,
			statusText: 'Not Found',
			json: () => Promise.resolve({ error: 'Resource not found' })
		});

		try {
			await apiClient('/test');
			expect.fail('Should have thrown');
		} catch (err) {
			expect(err).toBeInstanceOf(APIError);
			expect((err as APIError).status).toBe(404);
			expect((err as APIError).message).toBe('Resource not found');
		}
	});

	it('handles non-JSON error response', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: false,
			status: 500,
			statusText: 'Internal Server Error',
			json: () => Promise.reject(new Error('Not JSON'))
		});

		try {
			await apiClient('/test');
			expect.fail('Should have thrown');
		} catch (err) {
			expect(err).toBeInstanceOf(APIError);
			expect((err as APIError).status).toBe(500);
			expect((err as APIError).message).toContain('500');
		}
	});

	it('works without auth token', async () => {
		mockSupabase.auth.getSession.mockResolvedValueOnce({
			data: { session: null },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);

		mockFetch.mockResolvedValueOnce({
			ok: true,
			text: () => Promise.resolve(JSON.stringify({ id: 1 }))
		});

		await apiClient('/test');

		const headers = mockFetch.mock.calls[0][1].headers;
		expect(headers).not.toHaveProperty('Authorization');
	});
});

describe('api.get', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockSupabase.auth.getSession.mockResolvedValue({
			data: { session: { access_token: 'test-token' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);
	});

	it('makes GET request', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			text: () => Promise.resolve(JSON.stringify([]))
		});

		await api.get('/items');

		expect(mockFetch).toHaveBeenCalledWith(
			expect.stringContaining('/api/v1/items'),
			expect.objectContaining({ method: 'GET' })
		);
	});

	it('includes query parameters', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			text: () => Promise.resolve(JSON.stringify([]))
		});

		await api.get('/items', { page: '1', limit: '10' });

		expect(mockFetch).toHaveBeenCalledWith(
			expect.stringContaining('/items?page=1&limit=10'),
			expect.any(Object)
		);
	});
});

describe('api.post', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockSupabase.auth.getSession.mockResolvedValue({
			data: { session: { access_token: 'test-token' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);
	});

	it('makes POST request with body', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			text: () => Promise.resolve(JSON.stringify({ id: 1 }))
		});

		await api.post('/items', { name: 'Test' });

		expect(mockFetch).toHaveBeenCalledWith(
			expect.stringContaining('/api/v1/items'),
			expect.objectContaining({
				method: 'POST',
				body: JSON.stringify({ name: 'Test' })
			})
		);
	});

	it('handles POST without body', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			text: () => Promise.resolve(JSON.stringify({}))
		});

		await api.post('/items');

		expect(mockFetch).toHaveBeenCalledWith(
			expect.any(String),
			expect.objectContaining({
				method: 'POST',
				body: undefined
			})
		);
	});
});

describe('api.put', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockSupabase.auth.getSession.mockResolvedValue({
			data: { session: { access_token: 'test-token' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);
	});

	it('makes PUT request with body', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			text: () => Promise.resolve(JSON.stringify({ id: 1 }))
		});

		await api.put('/items/1', { name: 'Updated' });

		expect(mockFetch).toHaveBeenCalledWith(
			expect.stringContaining('/api/v1/items/1'),
			expect.objectContaining({
				method: 'PUT',
				body: JSON.stringify({ name: 'Updated' })
			})
		);
	});
});

describe('api.patch', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockSupabase.auth.getSession.mockResolvedValue({
			data: { session: { access_token: 'test-token' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);
	});

	it('makes PATCH request with body', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			text: () => Promise.resolve(JSON.stringify({ id: 1 }))
		});

		await api.patch('/items/1', { name: 'Patched' });

		expect(mockFetch).toHaveBeenCalledWith(
			expect.stringContaining('/api/v1/items/1'),
			expect.objectContaining({
				method: 'PATCH',
				body: JSON.stringify({ name: 'Patched' })
			})
		);
	});
});

describe('api.delete', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockSupabase.auth.getSession.mockResolvedValue({
			data: { session: { access_token: 'test-token' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);
	});

	it('makes DELETE request', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			text: () => Promise.resolve('')
		});

		await api.delete('/items/1');

		expect(mockFetch).toHaveBeenCalledWith(
			expect.stringContaining('/api/v1/items/1'),
			expect.objectContaining({ method: 'DELETE' })
		);
	});
});

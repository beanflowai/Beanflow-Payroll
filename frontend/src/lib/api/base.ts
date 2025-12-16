/**
 * Base API client class for Payroll Frontend
 */

import { API_BASE_URL } from '$lib/config';
import { supabase } from './supabase';

export interface APIError {
	error: string;
	details?: string;
	status_code?: number;
}

export interface APIResponse<T> {
	success: boolean;
	data?: T;
	error?: string;
	details?: string;
}

export class APIRequestError extends Error {
	status: number;
	detail?: any;

	constructor(message: string, status: number, detail?: any) {
		super(message);
		this.name = 'APIRequestError';
		this.status = status;
		this.detail = detail;
	}
}

export class BaseAPI {
	protected async processResponse<T>(response: Response, url: string): Promise<T> {
		if (!response.ok) {
			let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
			let errorData: any = null;
			try {
				errorData = await response.json();
				const detail = (errorData as APIError).error || errorData?.detail?.userMessage;
				errorMessage = detail || errorMessage;
			} catch {
				// Ignore JSON parse errors
			}

			throw new APIRequestError(errorMessage, response.status, errorData?.detail ?? errorData);
		}

		const apiResponse: APIResponse<T> = await response.json();

		if (apiResponse.success === false) {
			const errorMessage = apiResponse.error || 'API request failed';
			throw new Error(errorMessage);
		}

		return (apiResponse.data !== undefined ? apiResponse.data : apiResponse) as T;
	}

	/**
	 * Get authorization headers from Supabase session
	 */
	private async getAuthHeaders(): Promise<Record<string, string>> {
		const {
			data: { session }
		} = await supabase.auth.getSession();
		if (session?.access_token) {
			return { Authorization: `Bearer ${session.access_token}` };
		}
		return {};
	}

	protected async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
		const url = `${API_BASE_URL}${endpoint}`;

		const authHeaders = await this.getAuthHeaders();
		const isFormData = options.body instanceof FormData;
		const headers: HeadersInit = isFormData
			? { ...authHeaders, ...options.headers }
			: {
					'Content-Type': 'application/json',
					...authHeaders,
					...options.headers
				};

		const response = await fetch(url, {
			...options,
			headers,
			credentials: 'include'
		});

		return await this.processResponse<T>(response, url);
	}

	protected async get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
		const queryString = params ? '?' + new URLSearchParams(params).toString() : '';
		return this.request<T>(`${endpoint}${queryString}`, { method: 'GET' });
	}

	protected async post<T>(endpoint: string, body?: any): Promise<T> {
		return this.request<T>(endpoint, {
			method: 'POST',
			body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined
		});
	}
}

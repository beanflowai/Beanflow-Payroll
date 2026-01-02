/**
 * Base API Client for Payroll Frontend
 * Connects to the shared BeanFlow backend
 */

import { supabase } from './supabase';
import { companyState } from '$lib/stores/company.svelte';

// API base URL from environment
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Safely get the current company ID without throwing.
 * Returns null if no company is selected.
 */
function getCompanyIdSafe(): string | null {
	return companyState.currentCompany?.id ?? null;
}

/**
 * API Error class for standardized error handling
 */
export class APIError extends Error {
	status: number;
	details?: unknown;

	constructor(message: string, status: number, details?: unknown) {
		super(message);
		this.name = 'APIError';
		this.status = status;
		this.details = details;
	}
}

/**
 * Get the current auth token from Supabase
 */
async function getAuthToken(): Promise<string | null> {
	const {
		data: { session }
	} = await supabase.auth.getSession();
	return session?.access_token ?? null;
}

/**
 * Base API client function
 */
export async function apiClient<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
	const token = await getAuthToken();
	const companyId = getCompanyIdSafe();

	const headers: HeadersInit = {
		'Content-Type': 'application/json',
		...options.headers
	};

	if (token) {
		(headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
	}

	if (companyId) {
		(headers as Record<string, string>)['X-Company-Id'] = companyId;
	}

	const response = await fetch(`${API_BASE_URL}/api/v1${endpoint}`, {
		...options,
		headers,
		credentials: 'include'
	});

	if (!response.ok) {
		let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
		let errorDetails: unknown = null;

		try {
			const errorData = await response.json();
			errorMessage = errorData.error || errorData.detail || errorMessage;
			errorDetails = errorData;
		} catch {
			// Response is not JSON
		}

		throw new APIError(errorMessage, response.status, errorDetails);
	}

	// Handle empty responses
	const text = await response.text();
	if (!text) {
		return {} as T;
	}

	const data = JSON.parse(text);

	// Handle backend's standardized response format { success, data, message }
	if (data.success !== undefined) {
		if (!data.success) {
			throw new APIError(data.error || 'API request failed', response.status, data);
		}
		return data.data as T;
	}

	return data as T;
}

/**
 * HTTP method helpers
 */
export const api = {
	get: <T>(endpoint: string, params?: Record<string, string>) => {
		const queryString = params ? '?' + new URLSearchParams(params).toString() : '';
		return apiClient<T>(`${endpoint}${queryString}`, { method: 'GET' });
	},

	post: <T>(endpoint: string, body?: unknown) => {
		return apiClient<T>(endpoint, {
			method: 'POST',
			body: body ? JSON.stringify(body) : undefined
		});
	},

	put: <T>(endpoint: string, body?: unknown) => {
		return apiClient<T>(endpoint, {
			method: 'PUT',
			body: body ? JSON.stringify(body) : undefined
		});
	},

	patch: <T>(endpoint: string, body?: unknown) => {
		return apiClient<T>(endpoint, {
			method: 'PATCH',
			body: body ? JSON.stringify(body) : undefined
		});
	},

	delete: <T>(endpoint: string) => {
		return apiClient<T>(endpoint, { method: 'DELETE' });
	}
};

/**
 * Payroll-specific API endpoints
 * These will be implemented when the backend endpoints are ready
 */
export const payrollApi = {
	// Employees
	listEmployees: () => api.get<Employee[]>('/payroll/employees'),
	getEmployee: (id: string) => api.get<Employee>(`/payroll/employees/${id}`),
	createEmployee: (data: CreateEmployeeRequest) => api.post<Employee>('/payroll/employees', data),
	updateEmployee: (id: string, data: UpdateEmployeeRequest) =>
		api.patch<Employee>(`/payroll/employees/${id}`, data),
	deleteEmployee: (id: string) => api.delete<void>(`/payroll/employees/${id}`),

	// Payroll Runs
	getPayrollRun: (id: string) => api.get<PayrollRun>(`/payroll/runs/${id}`),
	createPayrollRun: (data: CreatePayrollRunRequest) => api.post<PayrollRun>('/payroll/runs', data),
	submitPayrollRun: (id: string) => api.post<PayrollRun>(`/payroll/runs/${id}/submit`),

	// Reports
	getRemittanceReport: (params: ReportParams) =>
		api.get<RemittanceReport>('/payroll/reports/remittance', params as Record<string, string>),
	getYTDReport: () => api.get<YTDReport>('/payroll/reports/ytd'),

	// Company
	getCompanySettings: () => api.get<CompanySettings>('/payroll/company'),
	updateCompanySettings: (data: UpdateCompanySettingsRequest) =>
		api.patch<CompanySettings>('/payroll/company', data)
};

// Type definitions (placeholder - will be moved to types/ when backend is ready)
export interface Employee {
	id: string;
	firstName: string;
	lastName: string;
	email: string;
	position: string;
	department: string;
	salary: number;
	payType: 'salary' | 'hourly';
	startDate: string;
	status: 'active' | 'inactive' | 'terminated';
}

export interface CreateEmployeeRequest {
	firstName: string;
	lastName: string;
	email: string;
	position: string;
	department: string;
	salary: number;
	payType: 'salary' | 'hourly';
	startDate: string;
}

export interface UpdateEmployeeRequest extends Partial<CreateEmployeeRequest> {
	status?: 'active' | 'inactive' | 'terminated';
}

export interface PayrollRun {
	id: string;
	payPeriodStart: string;
	payPeriodEnd: string;
	payDate: string;
	status: 'draft' | 'pending' | 'processing' | 'completed' | 'cancelled';
	employeeCount: number;
	grossPay: number;
	totalDeductions: number;
	netPay: number;
	createdAt: string;
}

export interface CreatePayrollRunRequest {
	payPeriodStart: string;
	payPeriodEnd: string;
	payDate: string;
}

export interface ReportParams {
	startDate?: string;
	endDate?: string;
	year?: string;
	month?: string;
}

export interface RemittanceReport {
	period: string;
	federalTax: number;
	provincialTax: number;
	cpp: number;
	ei: number;
	total: number;
}

export interface YTDReport {
	year: number;
	grossPay: number;
	federalTax: number;
	provincialTax: number;
	cpp: number;
	ei: number;
	netPay: number;
	payrollRunCount: number;
}

export interface CompanySettings {
	id: string;
	name: string;
	businessNumber: string;
	payrollAccountNumber: string;
	province: string;
	payFrequency: 'weekly' | 'bi-weekly' | 'semi-monthly' | 'monthly';
	nextPayDate: string;
	autoCalculateDeductions: boolean;
	sendPaystubEmails: boolean;
}

export interface UpdateCompanySettingsRequest extends Partial<Omit<CompanySettings, 'id'>> {}

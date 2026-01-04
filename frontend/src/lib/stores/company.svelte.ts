/**
 * Company Store for Multi-Company Support
 * Uses Svelte 5 Runes pattern (same as auth.svelte.ts)
 */

import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import type { CompanyProfile } from '$lib/types/company';
import {
	listCompanies,
	createCompany,
	type CompanyCreateInput
} from '$lib/services/companyService';

const STORAGE_KEY = 'beanflow_current_company_id';

// Company state using module-level state
let _currentCompany = $state<CompanyProfile | null>(null);
let _companies = $state<CompanyProfile[]>([]);
let _isLoading = $state(false);
let _error = $state<string | null>(null);

/**
 * Initialize company context
 * - Load all companies for the user
 * - Restore last selected company from localStorage
 * - If no stored selection, select first company
 */
export async function initializeCompanyContext(): Promise<void> {
	if (!browser) return;

	_isLoading = true;
	_error = null;

	try {
		// Load all companies for this user
		const result = await listCompanies();

		if (result.error) {
			_error = result.error;
			return;
		}

		_companies = result.data;

		// If no companies, user needs to create one
		if (_companies.length === 0) {
			_currentCompany = null;
			return;
		}

		// Try to restore last selected company from localStorage
		const storedCompanyId = localStorage.getItem(STORAGE_KEY);
		if (storedCompanyId) {
			const found = _companies.find((c) => c.id === storedCompanyId);
			if (found) {
				_currentCompany = found;
				return;
			}
		}

		// Default to first company
		_currentCompany = _companies[0];
		localStorage.setItem(STORAGE_KEY, _currentCompany.id);
	} catch (err) {
		_error = err instanceof Error ? err.message : 'Failed to initialize company context';
	} finally {
		_isLoading = false;
	}
}

/**
 * Switch to a different company
 * - Update current company state
 * - Save selection to localStorage
 * - Navigate to dashboard
 */
export async function switchCompany(companyId: string): Promise<void> {
	if (!browser) return;

	const company = _companies.find((c) => c.id === companyId);
	if (!company) {
		_error = 'Company not found';
		return;
	}

	_currentCompany = company;
	localStorage.setItem(STORAGE_KEY, companyId);

	// Navigate to dashboard when switching companies
	await goto('/dashboard');
}

/**
 * Add a new company and switch to it
 */
export async function addCompany(
	input: CompanyCreateInput
): Promise<{ success: boolean; error?: string }> {
	if (!browser) return { success: false, error: 'Not in browser' };

	_isLoading = true;
	_error = null;

	try {
		const result = await createCompany(input);

		if (result.error) {
			_error = result.error;
			return { success: false, error: result.error };
		}

		if (!result.data) {
			_error = 'Failed to create company';
			return { success: false, error: 'Failed to create company' };
		}

		// Add to companies list
		_companies = [..._companies, result.data];

		// Switch to the new company
		_currentCompany = result.data;
		localStorage.setItem(STORAGE_KEY, result.data.id);

		return { success: true };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to add company';
		_error = message;
		return { success: false, error: message };
	} finally {
		_isLoading = false;
	}
}

/**
 * Refresh companies list (e.g., after company update)
 */
export async function refreshCompanies(): Promise<void> {
	if (!browser) return;

	try {
		const result = await listCompanies();

		if (result.error) {
			_error = result.error;
			return;
		}

		_companies = result.data;

		// Update current company
		if (_currentCompany) {
			// Current company exists - check if it still exists in the list
			const updated = _companies.find((c) => c.id === _currentCompany!.id);
			if (updated) {
				_currentCompany = updated;
			} else if (_companies.length > 0) {
				// Current company was deleted, switch to first
				_currentCompany = _companies[0];
				localStorage.setItem(STORAGE_KEY, _currentCompany.id);
			} else {
				_currentCompany = null;
				localStorage.removeItem(STORAGE_KEY);
			}
		} else if (_companies.length > 0) {
			// No current company but companies exist - select the first one
			// This handles the case when first company is created
			_currentCompany = _companies[0];
			localStorage.setItem(STORAGE_KEY, _currentCompany.id);
		}
	} catch (err) {
		_error = err instanceof Error ? err.message : 'Failed to refresh companies';
	}
}

/**
 * Clear company context (called on logout)
 */
export function clearCompanyContext(): void {
	_currentCompany = null;
	_companies = [];
	_isLoading = false;
	_error = null;
	if (browser) {
		localStorage.removeItem(STORAGE_KEY);
	}
}

/**
 * Clear error
 */
export function clearCompanyError(): void {
	_error = null;
}

/**
 * Get current company ID (for use in services)
 * @throws Error if no company is selected
 */
export function getCurrentCompanyId(): string {
	if (!_currentCompany) {
		throw new Error('No company selected');
	}
	return _currentCompany.id;
}

// Export reactive getters
export const companyState = {
	get currentCompany() {
		return _currentCompany;
	},
	get companies() {
		return _companies;
	},
	get isLoading() {
		return _isLoading;
	},
	get error() {
		return _error;
	},
	get hasCompanies() {
		return _companies.length > 0;
	}
};

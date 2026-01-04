/**
 * Tests for company store
 *
 * Note: These tests mock the browser environment and services
 * to test the company store logic without requiring actual browser APIs.
 */

import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

// Mock $app/environment
vi.mock('$app/environment', () => ({
	browser: true
}));

// Mock $app/navigation
vi.mock('$app/navigation', () => ({
	goto: vi.fn()
}));

// Mock companyService
vi.mock('$lib/services/companyService', () => ({
	listCompanies: vi.fn(),
	createCompany: vi.fn()
}));

import { goto } from '$app/navigation';
import { listCompanies, createCompany } from '$lib/services/companyService';
import {
	initializeCompanyContext,
	switchCompany,
	addCompany,
	refreshCompanies,
	clearCompanyContext,
	clearCompanyError,
	getCurrentCompanyId,
	companyState
} from './company.svelte';

const mockListCompanies = vi.mocked(listCompanies);
const mockCreateCompany = vi.mocked(createCompany);
const mockGoto = vi.mocked(goto);

// Sample company data
const sampleCompanies = [
	{
		id: 'company-1',
		userId: 'user-123',
		companyName: 'Acme Corp',
		businessNumber: '123456789',
		payrollAccountNumber: '123456789RP0001',
		province: 'ON' as const,
		remitterType: 'regular' as const,
		autoCalculateDeductions: true,
		sendPaystubEmails: false,
		createdAt: '2025-01-01T00:00:00Z',
		updatedAt: '2025-01-01T00:00:00Z'
	},
	{
		id: 'company-2',
		userId: 'user-123',
		companyName: 'Beta Inc',
		businessNumber: '987654321',
		payrollAccountNumber: '987654321RP0001',
		province: 'BC' as const,
		remitterType: 'regular' as const,
		autoCalculateDeductions: true,
		sendPaystubEmails: true,
		createdAt: '2025-01-02T00:00:00Z',
		updatedAt: '2025-01-02T00:00:00Z'
	}
];

// Mock localStorage
const localStorageMock = (() => {
	let store: Record<string, string> = {};
	return {
		getItem: vi.fn((key: string) => store[key] || null),
		setItem: vi.fn((key: string, value: string) => {
			store[key] = value;
		}),
		removeItem: vi.fn((key: string) => {
			delete store[key];
		}),
		clear: vi.fn(() => {
			store = {};
		})
	};
})();

beforeEach(() => {
	Object.defineProperty(window, 'localStorage', {
		writable: true,
		value: localStorageMock
	});
	localStorageMock.clear();
});

afterEach(() => {
	vi.clearAllMocks();
});

describe('initializeCompanyContext', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		clearCompanyContext();
	});

	it('loads companies and selects first one', async () => {
		mockListCompanies.mockResolvedValue({
			data: sampleCompanies,
			count: 2,
			error: null
		});

		await initializeCompanyContext();

		expect(mockListCompanies).toHaveBeenCalled();
		expect(companyState.companies).toHaveLength(2);
		expect(companyState.currentCompany?.id).toBe('company-1');
	});

	it('restores last selected company from localStorage', async () => {
		localStorageMock.getItem.mockReturnValue('company-2');
		mockListCompanies.mockResolvedValue({
			data: sampleCompanies,
			count: 2,
			error: null
		});

		await initializeCompanyContext();

		expect(companyState.currentCompany?.id).toBe('company-2');
	});

	it('handles no companies', async () => {
		mockListCompanies.mockResolvedValue({
			data: [],
			count: 0,
			error: null
		});

		await initializeCompanyContext();

		expect(companyState.currentCompany).toBeNull();
		expect(companyState.hasCompanies).toBe(false);
	});

	it('handles list error', async () => {
		mockListCompanies.mockResolvedValue({
			data: [],
			count: 0,
			error: 'Database error'
		});

		await initializeCompanyContext();

		expect(companyState.error).toBe('Database error');
	});

	it('handles exception', async () => {
		mockListCompanies.mockRejectedValue(new Error('Network error'));

		await initializeCompanyContext();

		expect(companyState.error).toBe('Network error');
	});
});

describe('switchCompany', () => {
	beforeEach(async () => {
		vi.clearAllMocks();
		mockListCompanies.mockResolvedValue({
			data: sampleCompanies,
			count: 2,
			error: null
		});
		await initializeCompanyContext();
	});

	it('switches to different company', async () => {
		await switchCompany('company-2');

		expect(companyState.currentCompany?.id).toBe('company-2');
		expect(localStorageMock.setItem).toHaveBeenCalledWith('beanflow_current_company_id', 'company-2');
		expect(mockGoto).toHaveBeenCalledWith('/dashboard');
	});

	it('handles company not found', async () => {
		await switchCompany('non-existent');

		expect(companyState.error).toBe('Company not found');
	});
});

describe('addCompany', () => {
	beforeEach(async () => {
		vi.clearAllMocks();
		mockListCompanies.mockResolvedValue({
			data: sampleCompanies,
			count: 2,
			error: null
		});
		await initializeCompanyContext();
	});

	it('creates and switches to new company', async () => {
		const newCompany = {
			id: 'company-3',
			userId: 'user-123',
			companyName: 'Gamma LLC',
			businessNumber: '111222333',
			payrollAccountNumber: '111222333RP0001',
			province: 'AB' as const,
			remitterType: 'regular' as const,
			autoCalculateDeductions: true,
			sendPaystubEmails: false,
			createdAt: '2025-01-03T00:00:00Z',
			updatedAt: '2025-01-03T00:00:00Z'
		};

		mockCreateCompany.mockResolvedValue({
			data: newCompany,
			error: null
		});

		const result = await addCompany({
			company_name: 'Gamma LLC',
			business_number: '111222333',
			payroll_account_number: '111222333RP0001',
			province: 'AB'
		});

		expect(result.success).toBe(true);
		expect(companyState.companies).toHaveLength(3);
		expect(companyState.currentCompany?.id).toBe('company-3');
	});

	it('handles create error', async () => {
		mockCreateCompany.mockResolvedValue({
			data: null,
			error: 'Duplicate company name'
		});

		const result = await addCompany({
			company_name: 'Acme Corp',
			business_number: '123456789',
			payroll_account_number: '123456789RP0001',
			province: 'ON'
		});

		expect(result.success).toBe(false);
		expect(result.error).toBe('Duplicate company name');
	});

	it('handles null data from create', async () => {
		mockCreateCompany.mockResolvedValue({
			data: null,
			error: null
		});

		const result = await addCompany({
			company_name: 'Test',
			business_number: '111',
			payroll_account_number: '111RP0001',
			province: 'ON'
		});

		expect(result.success).toBe(false);
		expect(result.error).toBe('Failed to create company');
	});

	it('handles exception', async () => {
		mockCreateCompany.mockRejectedValue(new Error('Network error'));

		const result = await addCompany({
			company_name: 'Test',
			business_number: '111',
			payroll_account_number: '111RP0001',
			province: 'ON'
		});

		expect(result.success).toBe(false);
		expect(result.error).toBe('Network error');
	});
});

describe('refreshCompanies', () => {
	beforeEach(async () => {
		vi.clearAllMocks();
		clearCompanyContext();
		localStorageMock.clear();
		// Reset the mock to return fresh data with company-1 first
		localStorageMock.getItem.mockReturnValue(null);
		mockListCompanies.mockResolvedValue({
			data: sampleCompanies,
			count: 2,
			error: null
		});
		await initializeCompanyContext();
	});

	it('refreshes companies list and updates current company info', async () => {
		// Current company should exist after initialization
		const currentId = companyState.currentCompany?.id;
		expect(currentId).toBeDefined();

		// Find which company we have and update that one
		const updatedCompanies = sampleCompanies.map((c) =>
			c.id === currentId ? { ...c, companyName: c.companyName + ' Updated' } : c
		);

		mockListCompanies.mockResolvedValue({
			data: updatedCompanies,
			count: 2,
			error: null
		});

		await refreshCompanies();

		// Current company should have been updated
		expect(companyState.currentCompany?.companyName).toContain('Updated');
	});

	it('handles current company deleted', async () => {
		mockListCompanies.mockResolvedValue({
			data: [sampleCompanies[1]], // Only company-2 remains
			count: 1,
			error: null
		});

		await refreshCompanies();

		expect(companyState.currentCompany?.id).toBe('company-2');
	});

	it('handles all companies deleted', async () => {
		mockListCompanies.mockResolvedValue({
			data: [],
			count: 0,
			error: null
		});

		await refreshCompanies();

		expect(companyState.currentCompany).toBeNull();
		expect(localStorageMock.removeItem).toHaveBeenCalledWith('beanflow_current_company_id');
	});

	it('handles error', async () => {
		mockListCompanies.mockResolvedValue({
			data: [],
			count: 0,
			error: 'Database error'
		});

		await refreshCompanies();

		expect(companyState.error).toBe('Database error');
	});

	it('handles exception', async () => {
		mockListCompanies.mockRejectedValue(new Error('Network error'));

		await refreshCompanies();

		expect(companyState.error).toBe('Network error');
	});

	it('selects first company when no current company but companies exist', async () => {
		// Clear current company
		clearCompanyContext();

		mockListCompanies.mockResolvedValue({
			data: sampleCompanies,
			count: 2,
			error: null
		});

		await refreshCompanies();

		expect(companyState.currentCompany?.id).toBe('company-1');
	});
});

describe('clearCompanyContext', () => {
	beforeEach(async () => {
		mockListCompanies.mockResolvedValue({
			data: sampleCompanies,
			count: 2,
			error: null
		});
		await initializeCompanyContext();
	});

	it('clears all company state', () => {
		clearCompanyContext();

		expect(companyState.currentCompany).toBeNull();
		expect(companyState.companies).toEqual([]);
		expect(companyState.isLoading).toBe(false);
		expect(companyState.error).toBeNull();
		expect(localStorageMock.removeItem).toHaveBeenCalledWith('beanflow_current_company_id');
	});
});

describe('clearCompanyError', () => {
	it('clears the error state', async () => {
		mockListCompanies.mockResolvedValue({
			data: [],
			count: 0,
			error: 'Test error'
		});

		await initializeCompanyContext();
		expect(companyState.error).toBe('Test error');

		clearCompanyError();
		expect(companyState.error).toBeNull();
	});
});

describe('getCurrentCompanyId', () => {
	beforeEach(async () => {
		vi.clearAllMocks();
		clearCompanyContext();
		localStorageMock.clear();
		localStorageMock.getItem.mockReturnValue(null);
		mockListCompanies.mockResolvedValue({
			data: sampleCompanies,
			count: 2,
			error: null
		});
		await initializeCompanyContext();
	});

	it('returns current company ID', () => {
		const id = getCurrentCompanyId();
		// The current company should be one of the sample companies
		expect(['company-1', 'company-2']).toContain(id);
	});

	it('throws when no company selected', () => {
		clearCompanyContext();

		expect(() => getCurrentCompanyId()).toThrow('No company selected');
	});
});

describe('companyState', () => {
	it('exposes currentCompany getter', () => {
		expect(companyState).toHaveProperty('currentCompany');
	});

	it('exposes companies getter', () => {
		expect(companyState).toHaveProperty('companies');
	});

	it('exposes isLoading getter', () => {
		expect(companyState).toHaveProperty('isLoading');
	});

	it('exposes error getter', () => {
		expect(companyState).toHaveProperty('error');
	});

	it('exposes hasCompanies getter', () => {
		expect(companyState).toHaveProperty('hasCompanies');
	});
});

/**
 * Tests for companyService
 */

import { describe, expect, it, vi, beforeEach } from 'vitest';

// Mock the supabase client
vi.mock('$lib/api/supabase', () => ({
	supabase: {
		from: vi.fn(),
		storage: {
			from: vi.fn()
		}
	}
}));

// Mock the auth store
vi.mock('$lib/stores/auth.svelte', () => ({
	authState: {
		user: { id: 'test-user-id' }
	}
}));

import { supabase } from '$lib/api/supabase';
import {
	dbCompanyToUi,
	listCompanies,
	getCompany,
	createCompany,
	updateCompany,
	deleteCompany,
	getCompanyCount,
	getOrCreateDefaultCompany,
	uploadCompanyLogo
} from './companyService';
import type { DbCompany } from './companyService';

const mockSupabase = vi.mocked(supabase);

// Helper to create a mock query builder
function createMockQueryBuilder(response: { data: unknown; error: unknown; count?: number }) {
	const builder = {
		select: vi.fn().mockReturnThis(),
		insert: vi.fn().mockReturnThis(),
		update: vi.fn().mockReturnThis(),
		delete: vi.fn().mockReturnThis(),
		eq: vi.fn().mockReturnThis(),
		ilike: vi.fn().mockReturnThis(),
		order: vi.fn().mockReturnThis(),
		range: vi.fn().mockReturnThis(),
		single: vi.fn().mockResolvedValue(response),
		execute: vi.fn().mockResolvedValue(response)
	};

	// For range calls
	builder.range.mockImplementation(() => ({
		...builder,
		then: (resolve: (value: unknown) => void) =>
			resolve({ ...response, count: response.count ?? 0 })
	}));

	return builder;
}

// Sample DB company data
const sampleDbCompany: DbCompany = {
	id: 'company-123',
	user_id: 'test-user-id',
	company_name: 'Test Company Inc.',
	business_number: '123456789',
	payroll_account_number: '123456789RP0001',
	province: 'ON',
	remitter_type: 'regular',
	auto_calculate_deductions: true,
	send_paystub_emails: false,
	bookkeeping_ledger_id: null,
	bookkeeping_ledger_name: null,
	bookkeeping_connected_at: null,
	logo_url: null,
	created_at: '2024-01-01T00:00:00Z',
	updated_at: '2024-01-01T00:00:00Z'
};

describe('dbCompanyToUi', () => {
	it('converts DB company to UI format', () => {
		const result = dbCompanyToUi(sampleDbCompany);

		expect(result.id).toBe('company-123');
		expect(result.userId).toBe('test-user-id');
		expect(result.companyName).toBe('Test Company Inc.');
		expect(result.businessNumber).toBe('123456789');
		expect(result.payrollAccountNumber).toBe('123456789RP0001');
		expect(result.province).toBe('ON');
		expect(result.remitterType).toBe('regular');
		expect(result.autoCalculateDeductions).toBe(true);
		expect(result.sendPaystubEmails).toBe(false);
	});
});

describe('listCompanies', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('lists companies with default options', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [sampleDbCompany],
			error: null,
			count: 1
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await listCompanies();

		expect(mockSupabase.from).toHaveBeenCalledWith('companies');
		expect(result.error).toBeNull();
		expect(result.data).toHaveLength(1);
		expect(result.data[0].companyName).toBe('Test Company Inc.');
		expect(result.count).toBe(1);
	});

	it('filters by province when provided', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [],
			error: null,
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await listCompanies({ province: 'BC' });

		expect(mockBuilder.eq).toHaveBeenCalledWith('province', 'BC');
	});

	it('searches by company name when provided', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [],
			error: null,
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await listCompanies({ search: 'Test' });

		expect(mockBuilder.ilike).toHaveBeenCalledWith('company_name', '%Test%');
	});

	it('returns error on failure', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Database error' },
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await listCompanies();

		expect(result.error).toBe('Database error');
		expect(result.data).toEqual([]);
	});
});

describe('getCompany', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('gets a single company by ID', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: sampleDbCompany,
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getCompany('company-123');

		expect(mockSupabase.from).toHaveBeenCalledWith('companies');
		expect(mockBuilder.eq).toHaveBeenCalledWith('id', 'company-123');
		expect(result.error).toBeNull();
		expect(result.data?.id).toBe('company-123');
	});

	it('returns error when company not found', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Not found' }
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getCompany('non-existent');

		expect(result.error).toBe('Not found');
		expect(result.data).toBeNull();
	});
});

describe('createCompany', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('creates a new company', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: sampleDbCompany,
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await createCompany({
			company_name: 'Test Company Inc.',
			business_number: '123456789',
			payroll_account_number: '123456789RP0001',
			province: 'ON'
		});

		expect(mockSupabase.from).toHaveBeenCalledWith('companies');
		expect(mockBuilder.insert).toHaveBeenCalled();
		expect(result.error).toBeNull();
		expect(result.data?.companyName).toBe('Test Company Inc.');
	});

	it('uses default values for optional fields', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: sampleDbCompany,
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await createCompany({
			company_name: 'Test',
			business_number: '123',
			payroll_account_number: '123RP0001',
			province: 'ON'
		});

		expect(mockBuilder.insert).toHaveBeenCalledWith(
			expect.objectContaining({
				remitter_type: 'regular',
				auto_calculate_deductions: true,
				send_paystub_emails: false
			})
		);
	});

	it('returns error on create failure', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Duplicate company' }
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await createCompany({
			company_name: 'Test',
			business_number: '123',
			payroll_account_number: '123RP0001',
			province: 'ON'
		});

		expect(result.error).toBe('Duplicate company');
		expect(result.data).toBeNull();
	});
});

describe('updateCompany', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('updates a company', async () => {
		const updatedCompany = { ...sampleDbCompany, company_name: 'Updated Company' };
		const mockBuilder = createMockQueryBuilder({
			data: updatedCompany,
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await updateCompany('company-123', { company_name: 'Updated Company' });

		expect(mockSupabase.from).toHaveBeenCalledWith('companies');
		expect(mockBuilder.update).toHaveBeenCalled();
		expect(result.error).toBeNull();
		expect(result.data?.companyName).toBe('Updated Company');
	});

	it('only updates provided fields', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: sampleDbCompany,
			error: null
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		await updateCompany('company-123', { company_name: 'New Name' });

		expect(mockBuilder.update).toHaveBeenCalledWith({ company_name: 'New Name' });
	});

	it('returns error on update failure', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Update failed' }
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await updateCompany('company-123', { company_name: 'New Name' });

		expect(result.error).toBe('Update failed');
		expect(result.data).toBeNull();
	});
});

describe('deleteCompany', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('deletes a company', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: null
		});
		mockBuilder.eq.mockImplementation(() => ({
			...mockBuilder,
			then: (resolve: (value: unknown) => void) => resolve({ error: null })
		}));
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await deleteCompany('company-123');

		expect(mockSupabase.from).toHaveBeenCalledWith('companies');
		expect(mockBuilder.delete).toHaveBeenCalled();
		expect(result.error).toBeNull();
	});

	it('returns error on delete failure', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Cannot delete' }
		});
		mockBuilder.eq.mockImplementation(() => ({
			...mockBuilder,
			then: (resolve: (value: unknown) => void) => resolve({ error: { message: 'Cannot delete' } })
		}));
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await deleteCompany('company-123');

		expect(result.error).toBe('Cannot delete');
	});
});

describe('getCompanyCount', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('gets company count', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: null,
			count: 5
		});
		mockBuilder.eq.mockImplementation(() => ({
			...mockBuilder,
			then: (resolve: (value: unknown) => void) => resolve({ count: 5, error: null })
		}));
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const count = await getCompanyCount();

		expect(count).toBe(5);
	});

	it('returns 0 on error', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Error' },
			count: 0
		});
		mockBuilder.eq.mockImplementation(() => ({
			...mockBuilder,
			then: (resolve: (value: unknown) => void) =>
				resolve({ count: null, error: { message: 'Error' } })
		}));
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const count = await getCompanyCount();

		expect(count).toBe(0);
	});
});

describe('getOrCreateDefaultCompany', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('returns existing company if one exists', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [sampleDbCompany],
			error: null,
			count: 1
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getOrCreateDefaultCompany();

		expect(result.error).toBeNull();
		expect(result.data?.id).toBe('company-123');
	});

	it('returns null data if no company exists', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: [],
			error: null,
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getOrCreateDefaultCompany();

		expect(result.error).toBeNull();
		expect(result.data).toBeNull();
	});

	it('returns error if list fails', async () => {
		const mockBuilder = createMockQueryBuilder({
			data: null,
			error: { message: 'Database error' },
			count: 0
		});
		mockSupabase.from.mockReturnValue(mockBuilder as unknown as ReturnType<typeof supabase.from>);

		const result = await getOrCreateDefaultCompany();

		expect(result.error).toBe('Database error');
	});
});

describe('uploadCompanyLogo', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('rejects non-image files', async () => {
		const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

		const result = await uploadCompanyLogo(file, 'company-123');

		expect(result.error).toContain('image file');
		expect(result.publicUrl).toBeNull();
	});

	it('rejects files larger than 2MB', async () => {
		// Create a large file (simulated)
		const largeContent = new ArrayBuffer(3 * 1024 * 1024);
		const file = new File([largeContent], 'large.png', { type: 'image/png' });

		const result = await uploadCompanyLogo(file, 'company-123');

		expect(result.error).toContain('2MB');
		expect(result.publicUrl).toBeNull();
	});

	it('uploads image successfully', async () => {
		const file = new File(['test'], 'logo.png', { type: 'image/png' });

		const mockStorageFrom = vi.fn().mockReturnValue({
			upload: vi.fn().mockResolvedValue({ error: null }),
			getPublicUrl: vi.fn().mockReturnValue({
				data: { publicUrl: 'https://storage.example.com/assets/company-logos/logo.png' }
			})
		});
		mockSupabase.storage.from = mockStorageFrom;

		const result = await uploadCompanyLogo(file, 'company-123');

		expect(result.error).toBeNull();
		expect(result.publicUrl).toContain('https://storage.example.com');
	});

	it('handles upload errors', async () => {
		const file = new File(['test'], 'logo.png', { type: 'image/png' });

		const mockStorageFrom = vi.fn().mockReturnValue({
			upload: vi.fn().mockResolvedValue({ error: { message: 'Upload failed' } }),
			getPublicUrl: vi.fn()
		});
		mockSupabase.storage.from = mockStorageFrom;

		const result = await uploadCompanyLogo(file, 'company-123');

		expect(result.error).toContain('Upload failed');
		expect(result.publicUrl).toBeNull();
	});
});

/**
 * Tests for t4Service
 */

import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock URL methods
global.URL.createObjectURL = vi.fn(() => 'blob:test-url');
global.URL.revokeObjectURL = vi.fn();

// Mock document methods
const mockLink = {
	href: '',
	download: '',
	click: vi.fn()
};
vi.spyOn(document, 'createElement').mockReturnValue(mockLink as unknown as HTMLAnchorElement);
vi.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as unknown as Node);
vi.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as unknown as Node);

// Mock supabase
vi.mock('$lib/api/supabase', () => ({
	supabase: {
		auth: {
			getSession: vi.fn()
		}
	}
}));

import { supabase } from '$lib/api/supabase';
import {
	listT4Slips,
	generateT4Slips,
	downloadT4Slip,
	generateT4Summary,
	getT4Summary,
	downloadT4SummaryPdf,
	downloadT4Xml,
	validateT4ForCRA,
	recordT4Submission
} from './t4Service';

const mockSupabase = vi.mocked(supabase);

describe('listT4Slips', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockSupabase.auth.getSession.mockResolvedValue({
			data: { session: { access_token: 'test-token' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);
	});

	it('returns error when not authenticated', async () => {
		mockSupabase.auth.getSession.mockResolvedValueOnce({
			data: { session: null },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);

		const result = await listT4Slips('company-123', 2025);

		expect(result.error).toBe('Not authenticated');
		expect(result.data).toBeNull();
	});

	it('lists T4 slips successfully', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			json: () =>
				Promise.resolve({
					tax_year: 2025,
					total_count: 2,
					slips: [
						{
							id: 'slip-1',
							employee_id: 'emp-1',
							employee_name: 'John Doe',
							sin_masked: '***-***-123',
							box_14_employment_income: 50000,
							box_22_income_tax_deducted: 8000,
							status: 'generated',
							pdf_available: true
						}
					]
				})
		});

		const result = await listT4Slips('company-123', 2025);

		expect(result.error).toBeNull();
		expect(result.data?.taxYear).toBe(2025);
		expect(result.data?.slips).toHaveLength(1);
		expect(result.data?.slips[0].employeeName).toBe('John Doe');
	});

	it('handles API error', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: false,
			status: 500,
			json: () => Promise.resolve({ detail: 'Server error' })
		});

		const result = await listT4Slips('company-123', 2025);

		expect(result.error).toBe('Server error');
	});

	it('handles network error', async () => {
		mockFetch.mockRejectedValueOnce(new Error('Network failed'));

		const result = await listT4Slips('company-123', 2025);

		expect(result.error).toBe('Network failed');
	});
});

describe('generateT4Slips', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockSupabase.auth.getSession.mockResolvedValue({
			data: { session: { access_token: 'test-token' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);
	});

	it('returns error when not authenticated', async () => {
		mockSupabase.auth.getSession.mockResolvedValueOnce({
			data: { session: null },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);

		const result = await generateT4Slips('company-123', 2025);

		expect(result.error).toBe('Not authenticated');
	});

	it('generates T4 slips successfully', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			json: () =>
				Promise.resolve({
					success: true,
					tax_year: 2025,
					slips_generated: 5,
					slips_skipped: 0,
					errors: []
				})
		});

		const result = await generateT4Slips('company-123', 2025);

		expect(result.error).toBeNull();
		expect(result.data?.success).toBe(true);
		expect(result.data?.slipsGenerated).toBe(5);
	});

	it('generates T4 slips with options', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			json: () =>
				Promise.resolve({
					success: true,
					tax_year: 2025,
					slips_generated: 2,
					slips_skipped: 0,
					errors: []
				})
		});

		await generateT4Slips('company-123', 2025, {
			employeeIds: ['emp-1', 'emp-2'],
			regenerate: true
		});

		expect(mockFetch).toHaveBeenCalledWith(
			expect.stringContaining('/generate'),
			expect.objectContaining({
				method: 'POST',
				body: JSON.stringify({
					tax_year: 2025,
					employee_ids: ['emp-1', 'emp-2'],
					regenerate: true
				})
			})
		);
	});

	it('handles generation errors', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			json: () =>
				Promise.resolve({
					success: true,
					tax_year: 2025,
					slips_generated: 1,
					slips_skipped: 1,
					errors: [{ employee_id: 'emp-2', message: 'Missing SIN' }]
				})
		});

		const result = await generateT4Slips('company-123', 2025);

		expect(result.data?.errors).toHaveLength(1);
		expect(result.data?.errors[0].employeeId).toBe('emp-2');
	});
});

describe('downloadT4Slip', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockSupabase.auth.getSession.mockResolvedValue({
			data: { session: { access_token: 'test-token' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);
	});

	it('returns error when not authenticated', async () => {
		mockSupabase.auth.getSession.mockResolvedValueOnce({
			data: { session: null },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);

		const result = await downloadT4Slip('company-123', 2025, 'emp-1');

		expect(result.error).toBe('Not authenticated');
	});

	it('downloads T4 slip successfully', async () => {
		const mockBlob = new Blob(['pdf content'], { type: 'application/pdf' });
		mockFetch.mockResolvedValueOnce({
			ok: true,
			headers: new Headers({ 'Content-Disposition': 'filename=T4_2025_emp1.pdf' }),
			blob: () => Promise.resolve(mockBlob)
		});

		const result = await downloadT4Slip('company-123', 2025, 'emp-1');

		expect(result.error).toBeNull();
		expect(mockLink.click).toHaveBeenCalled();
	});

	it('handles download failure', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: false,
			status: 404,
			text: () => Promise.resolve('Not found')
		});

		const result = await downloadT4Slip('company-123', 2025, 'emp-1');

		expect(result.error).toContain('404');
	});
});

describe('generateT4Summary', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockSupabase.auth.getSession.mockResolvedValue({
			data: { session: { access_token: 'test-token' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);
	});

	it('returns error when not authenticated', async () => {
		mockSupabase.auth.getSession.mockResolvedValueOnce({
			data: { session: null },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);

		const result = await generateT4Summary('company-123', 2025);

		expect(result.error).toBe('Not authenticated');
	});

	it('generates T4 summary successfully', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			json: () =>
				Promise.resolve({
					success: true,
					summary: {
						company_id: 'company-123',
						tax_year: 2025,
						employer_name: 'Test Company',
						employer_account_number: '123456789RP0001',
						total_number_of_t4_slips: 10,
						total_employment_income: 500000,
						total_cpp_contributions: 30000,
						total_cpp2_contributions: 5000,
						total_ei_premiums: 10000,
						total_income_tax_deducted: 100000,
						total_union_dues: 2000,
						total_cpp_employer: 30000,
						total_ei_employer: 14000,
						remittance_difference: 0,
						status: 'generated'
					}
				})
		});

		const result = await generateT4Summary('company-123', 2025);

		expect(result.error).toBeNull();
		expect(result.data?.success).toBe(true);
		expect(result.data?.summary?.taxYear).toBe(2025);
	});
});

describe('getT4Summary', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockSupabase.auth.getSession.mockResolvedValue({
			data: { session: { access_token: 'test-token' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);
	});

	it('returns null for 404 (no summary exists)', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: false,
			status: 404
		});

		const result = await getT4Summary('company-123', 2025);

		expect(result.error).toBeNull();
		expect(result.data).toBeNull();
	});

	it('returns summary when exists', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			json: () =>
				Promise.resolve({
					success: true,
					summary: {
						company_id: 'company-123',
						tax_year: 2025,
						employer_name: 'Test Company',
						employer_account_number: '123456789RP0001',
						total_number_of_t4_slips: 5,
						total_employment_income: 250000,
						total_cpp_contributions: 15000,
						total_cpp2_contributions: 2500,
						total_ei_premiums: 5000,
						total_income_tax_deducted: 50000,
						total_union_dues: 1000,
						total_cpp_employer: 15000,
						total_ei_employer: 7000,
						remittance_difference: 0,
						status: 'generated'
					}
				})
		});

		const result = await getT4Summary('company-123', 2025);

		expect(result.error).toBeNull();
		expect(result.data?.totalNumberOfT4Slips).toBe(5);
	});
});

describe('downloadT4SummaryPdf', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockSupabase.auth.getSession.mockResolvedValue({
			data: { session: { access_token: 'test-token' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);
	});

	it('downloads summary PDF successfully', async () => {
		const mockBlob = new Blob(['pdf content'], { type: 'application/pdf' });
		mockFetch.mockResolvedValueOnce({
			ok: true,
			headers: new Headers({}),
			blob: () => Promise.resolve(mockBlob)
		});

		const result = await downloadT4SummaryPdf('company-123', 2025);

		expect(result.error).toBeNull();
	});
});

describe('downloadT4Xml', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockSupabase.auth.getSession.mockResolvedValue({
			data: { session: { access_token: 'test-token' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);
	});

	it('downloads XML successfully', async () => {
		const mockBlob = new Blob(['<xml>content</xml>'], { type: 'application/xml' });
		mockFetch.mockResolvedValueOnce({
			ok: true,
			headers: new Headers({}),
			blob: () => Promise.resolve(mockBlob)
		});

		const result = await downloadT4Xml('company-123', 2025);

		expect(result.error).toBeNull();
	});
});

describe('validateT4ForCRA', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockSupabase.auth.getSession.mockResolvedValue({
			data: { session: { access_token: 'test-token' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);
	});

	it('validates XML successfully', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			json: () =>
				Promise.resolve({
					success: true,
					validation: {
						is_valid: true,
						errors: [],
						warnings: [],
						cra_portal_url: 'https://www.canada.ca/t4web'
					}
				})
		});

		const result = await validateT4ForCRA('company-123', 2025);

		expect(result.error).toBeNull();
		expect(result.data?.isValid).toBe(true);
		expect(result.data?.craPortalUrl).toContain('canada.ca');
	});

	it('returns validation errors', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			json: () =>
				Promise.resolve({
					success: true,
					validation: {
						is_valid: false,
						errors: [{ code: 'MISSING_SIN', message: 'SIN is required', field: 'sin' }],
						warnings: [{ code: 'REVIEW', message: 'Please review amounts' }],
						cra_portal_url: 'https://www.canada.ca/t4web'
					}
				})
		});

		const result = await validateT4ForCRA('company-123', 2025);

		expect(result.data?.isValid).toBe(false);
		expect(result.data?.errors).toHaveLength(1);
		expect(result.data?.warnings).toHaveLength(1);
	});
});

describe('recordT4Submission', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockSupabase.auth.getSession.mockResolvedValue({
			data: { session: { access_token: 'test-token' } },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);
	});

	it('records submission successfully', async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			json: () =>
				Promise.resolve({
					success: true,
					summary: {
						company_id: 'company-123',
						tax_year: 2025,
						employer_name: 'Test Company',
						employer_account_number: '123456789RP0001',
						total_number_of_t4_slips: 5,
						total_employment_income: 250000,
						total_cpp_contributions: 15000,
						total_cpp2_contributions: 2500,
						total_ei_premiums: 5000,
						total_income_tax_deducted: 50000,
						total_union_dues: 1000,
						total_cpp_employer: 15000,
						total_ei_employer: 7000,
						remittance_difference: 0,
						status: 'submitted',
						cra_confirmation_number: 'CRA-123456',
						submitted_at: '2025-02-28T10:00:00Z',
						submitted_by: 'user@example.com'
					}
				})
		});

		const result = await recordT4Submission('company-123', 2025, {
			confirmationNumber: 'CRA-123456',
			submissionNotes: 'Submitted via web portal'
		});

		expect(result.error).toBeNull();
		expect(result.data?.craConfirmationNumber).toBe('CRA-123456');
	});

	it('returns error when not authenticated', async () => {
		mockSupabase.auth.getSession.mockResolvedValueOnce({
			data: { session: null },
			error: null
		} as unknown as ReturnType<typeof supabase.auth.getSession>);

		const result = await recordT4Submission('company-123', 2025, {
			confirmationNumber: 'CRA-123456'
		});

		expect(result.error).toBe('Not authenticated');
	});
});

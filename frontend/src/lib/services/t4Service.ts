/**
 * T4 Service - Backend API operations for T4 year-end processing
 *
 * Handles T4 slip generation, listing, and downloads for CRA year-end reporting.
 */

import { supabase } from '$lib/api/supabase';
import type {
	T4SlipListResponse,
	T4SlipSummary,
	T4GenerationRequest,
	T4GenerationResponse,
	T4SummaryData,
	T4SummaryResponse
} from '$lib/types/t4';

// API base URL from environment
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// =============================================================================
// Type Conversion (snake_case from API to camelCase for UI)
// =============================================================================

interface ApiT4SlipSummary {
	id: string;
	employee_id: string;
	employee_name: string;
	sin_masked: string;
	box_14_employment_income: number;
	box_22_income_tax_deducted: number;
	status: string;
	pdf_available: boolean;
}

interface ApiT4SlipListResponse {
	tax_year: number;
	total_count: number;
	slips: ApiT4SlipSummary[];
}

interface ApiT4GenerationResponse {
	success: boolean;
	tax_year: number;
	slips_generated: number;
	slips_skipped: number;
	errors: Array<{ employee_id?: string; message: string }>;
	message?: string;
}

interface ApiT4Summary {
	company_id: string;
	tax_year: number;
	employer_name: string;
	employer_account_number: string;
	employer_address_line1?: string;
	employer_city?: string;
	employer_province?: string;
	employer_postal_code?: string;
	total_number_of_t4_slips: number;
	total_employment_income: number;
	total_cpp_contributions: number;
	total_cpp2_contributions: number;
	total_ei_premiums: number;
	total_income_tax_deducted: number;
	total_union_dues: number;
	total_cpp_employer: number;
	total_ei_employer: number;
	remittance_difference: number;
	status: string;
	pdf_storage_key?: string;
	xml_storage_key?: string;
	generated_at?: string;
}

interface ApiT4SummaryResponse {
	success: boolean;
	summary?: ApiT4Summary;
	message?: string;
}

function apiSlipToUi(apiSlip: ApiT4SlipSummary): T4SlipSummary {
	return {
		id: apiSlip.id,
		employeeId: apiSlip.employee_id,
		employeeName: apiSlip.employee_name,
		sinMasked: apiSlip.sin_masked,
		box14EmploymentIncome: apiSlip.box_14_employment_income,
		box22IncomeTaxDeducted: apiSlip.box_22_income_tax_deducted,
		status: apiSlip.status as T4SlipSummary['status'],
		pdfAvailable: apiSlip.pdf_available
	};
}

function apiSummaryToUi(apiSummary: ApiT4Summary): T4SummaryData {
	return {
		companyId: apiSummary.company_id,
		taxYear: apiSummary.tax_year,
		employerName: apiSummary.employer_name,
		employerAccountNumber: apiSummary.employer_account_number,
		employerAddressLine1: apiSummary.employer_address_line1,
		employerCity: apiSummary.employer_city,
		employerProvince: apiSummary.employer_province,
		employerPostalCode: apiSummary.employer_postal_code,
		totalNumberOfT4Slips: apiSummary.total_number_of_t4_slips,
		totalEmploymentIncome: apiSummary.total_employment_income,
		totalCppContributions: apiSummary.total_cpp_contributions,
		totalCpp2Contributions: apiSummary.total_cpp2_contributions,
		totalEiPremiums: apiSummary.total_ei_premiums,
		totalIncomeTaxDeducted: apiSummary.total_income_tax_deducted,
		totalUnionDues: apiSummary.total_union_dues,
		totalCppEmployer: apiSummary.total_cpp_employer,
		totalEiEmployer: apiSummary.total_ei_employer,
		remittanceDifference: apiSummary.remittance_difference,
		status: apiSummary.status as T4SummaryData['status'],
		pdfStorageKey: apiSummary.pdf_storage_key,
		xmlStorageKey: apiSummary.xml_storage_key,
		generatedAt: apiSummary.generated_at
	};
}

// =============================================================================
// Service Result Types
// =============================================================================

export interface T4ServiceResult<T> {
	data: T | null;
	error: string | null;
}

// =============================================================================
// T4 Slip Operations
// =============================================================================

/**
 * List T4 slips for a company and tax year
 */
export async function listT4Slips(
	companyId: string,
	taxYear: number
): Promise<T4ServiceResult<T4SlipListResponse>> {
	try {
		const {
			data: { session }
		} = await supabase.auth.getSession();
		if (!session?.access_token) {
			return { data: null, error: 'Not authenticated' };
		}

		const url = `${API_BASE_URL}/api/v1/t4/slips/${companyId}/${taxYear}`;
		const response = await fetch(url, {
			method: 'GET',
			headers: {
				Authorization: `Bearer ${session.access_token}`
			}
		});

		if (!response.ok) {
			const errorData = await response.json().catch(() => ({}));
			const errorMessage = errorData.detail || `HTTP ${response.status}`;
			return { data: null, error: errorMessage };
		}

		const data: ApiT4SlipListResponse = await response.json();

		const result: T4SlipListResponse = {
			taxYear: data.tax_year,
			totalCount: data.total_count,
			slips: data.slips.map(apiSlipToUi)
		};

		return { data: result, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to list T4 slips';
		console.error('Failed to list T4 slips:', err);
		return { data: null, error: message };
	}
}

/**
 * Generate T4 slips for a company and tax year
 */
export async function generateT4Slips(
	companyId: string,
	taxYear: number,
	options?: { employeeIds?: string[]; regenerate?: boolean }
): Promise<T4ServiceResult<T4GenerationResponse>> {
	try {
		const {
			data: { session }
		} = await supabase.auth.getSession();
		if (!session?.access_token) {
			return { data: null, error: 'Not authenticated' };
		}

		const url = `${API_BASE_URL}/api/v1/t4/slips/${companyId}/${taxYear}/generate`;
		const response = await fetch(url, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${session.access_token}`
			},
			body: JSON.stringify({
				tax_year: taxYear,
				employee_ids: options?.employeeIds,
				regenerate: options?.regenerate ?? false
			})
		});

		if (!response.ok) {
			const errorData = await response.json().catch(() => ({}));
			const errorMessage = errorData.detail || `HTTP ${response.status}`;
			return { data: null, error: errorMessage };
		}

		const data: ApiT4GenerationResponse = await response.json();

		const result: T4GenerationResponse = {
			success: data.success,
			taxYear: data.tax_year,
			slipsGenerated: data.slips_generated,
			slipsSkipped: data.slips_skipped,
			errors: (data.errors || []).map((e) => ({
				employeeId: e.employee_id,
				message: e.message
			})),
			message: data.message
		};

		return { data: result, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to generate T4 slips';
		console.error('Failed to generate T4 slips:', err);
		return { data: null, error: message };
	}
}

/**
 * Download T4 slip PDF for a specific employee
 * Uses fetch with auth headers and triggers browser download
 */
export async function downloadT4Slip(
	companyId: string,
	taxYear: number,
	employeeId: string
): Promise<{ error: string | null }> {
	try {
		const {
			data: { session }
		} = await supabase.auth.getSession();
		if (!session?.access_token) {
			return { error: 'Not authenticated' };
		}

		const url = `${API_BASE_URL}/api/v1/t4/slips/${companyId}/${taxYear}/${employeeId}/download`;
		const response = await fetch(url, {
			method: 'GET',
			headers: {
				Authorization: `Bearer ${session.access_token}`
			}
		});

		if (!response.ok) {
			const errorText = await response.text();
			console.error('T4 slip download failed:', response.status, errorText);
			return { error: `Download failed: ${response.status}` };
		}

		// Get filename from Content-Disposition header or use default
		const contentDisposition = response.headers.get('Content-Disposition');
		let filename = `T4_${taxYear}_${employeeId}.pdf`;
		if (contentDisposition) {
			const match = contentDisposition.match(/filename=(.+)/);
			if (match) {
				filename = match[1].replace(/['"]/g, '');
			}
		}

		// Create blob and trigger download
		const blob = await response.blob();
		const blobUrl = URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = blobUrl;
		link.download = filename;
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
		URL.revokeObjectURL(blobUrl);

		return { error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to download T4 slip';
		console.error('T4 slip download error:', err);
		return { error: message };
	}
}

// =============================================================================
// T4 Summary Operations
// =============================================================================

/**
 * Generate T4 Summary for a company and tax year
 */
export async function generateT4Summary(
	companyId: string,
	taxYear: number
): Promise<T4ServiceResult<T4SummaryResponse>> {
	try {
		const {
			data: { session }
		} = await supabase.auth.getSession();
		if (!session?.access_token) {
			return { data: null, error: 'Not authenticated' };
		}

		const url = `${API_BASE_URL}/api/v1/t4/summary/${companyId}/${taxYear}/generate`;
		const response = await fetch(url, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${session.access_token}`
			}
		});

		if (!response.ok) {
			const errorData = await response.json().catch(() => ({}));
			const errorMessage = errorData.detail || `HTTP ${response.status}`;
			return { data: null, error: errorMessage };
		}

		const data: ApiT4SummaryResponse = await response.json();

		const result: T4SummaryResponse = {
			success: data.success,
			summary: data.summary ? apiSummaryToUi(data.summary) : undefined,
			message: data.message
		};

		return { data: result, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to generate T4 Summary';
		console.error('Failed to generate T4 Summary:', err);
		return { data: null, error: message };
	}
}

/**
 * Get existing T4 Summary for a company and tax year
 */
export async function getT4Summary(
	companyId: string,
	taxYear: number
): Promise<T4ServiceResult<T4SummaryData | null>> {
	try {
		const {
			data: { session }
		} = await supabase.auth.getSession();
		if (!session?.access_token) {
			return { data: null, error: 'Not authenticated' };
		}

		const url = `${API_BASE_URL}/api/v1/t4/summary/${companyId}/${taxYear}`;
		const response = await fetch(url, {
			method: 'GET',
			headers: {
				Authorization: `Bearer ${session.access_token}`
			}
		});

		// 404 means no summary exists yet - not an error
		if (response.status === 404) {
			return { data: null, error: null };
		}

		if (!response.ok) {
			const errorData = await response.json().catch(() => ({}));
			const errorMessage = errorData.detail || `HTTP ${response.status}`;
			return { data: null, error: errorMessage };
		}

		const data: ApiT4SummaryResponse = await response.json();

		if (!data.success || !data.summary) {
			return { data: null, error: null };
		}

		return { data: apiSummaryToUi(data.summary), error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to get T4 Summary';
		console.error('Failed to get T4 Summary:', err);
		return { data: null, error: message };
	}
}

/**
 * Download T4 Summary PDF
 */
export async function downloadT4SummaryPdf(
	companyId: string,
	taxYear: number
): Promise<{ error: string | null }> {
	try {
		const {
			data: { session }
		} = await supabase.auth.getSession();
		if (!session?.access_token) {
			return { error: 'Not authenticated' };
		}

		const url = `${API_BASE_URL}/api/v1/t4/summary/${companyId}/${taxYear}/download-pdf`;
		const response = await fetch(url, {
			method: 'GET',
			headers: {
				Authorization: `Bearer ${session.access_token}`
			}
		});

		if (!response.ok) {
			const errorText = await response.text();
			console.error('T4 Summary PDF download failed:', response.status, errorText);
			return { error: `Download failed: ${response.status}` };
		}

		// Get filename from Content-Disposition header or use default
		const contentDisposition = response.headers.get('Content-Disposition');
		let filename = `T4_Summary_${taxYear}.pdf`;
		if (contentDisposition) {
			const match = contentDisposition.match(/filename=(.+)/);
			if (match) {
				filename = match[1].replace(/['"]/g, '');
			}
		}

		// Create blob and trigger download
		const blob = await response.blob();
		const blobUrl = URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = blobUrl;
		link.download = filename;
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
		URL.revokeObjectURL(blobUrl);

		return { error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to download T4 Summary PDF';
		console.error('T4 Summary PDF download error:', err);
		return { error: message };
	}
}

/**
 * Download T4 XML for CRA submission
 */
export async function downloadT4Xml(
	companyId: string,
	taxYear: number
): Promise<{ error: string | null }> {
	try {
		const {
			data: { session }
		} = await supabase.auth.getSession();
		if (!session?.access_token) {
			return { error: 'Not authenticated' };
		}

		const url = `${API_BASE_URL}/api/v1/t4/summary/${companyId}/${taxYear}/download-xml`;
		const response = await fetch(url, {
			method: 'GET',
			headers: {
				Authorization: `Bearer ${session.access_token}`
			}
		});

		if (!response.ok) {
			const errorText = await response.text();
			console.error('T4 XML download failed:', response.status, errorText);
			return { error: `Download failed: ${response.status}` };
		}

		// Get filename from Content-Disposition header or use default
		const contentDisposition = response.headers.get('Content-Disposition');
		let filename = `T4_${taxYear}_CRA.xml`;
		if (contentDisposition) {
			const match = contentDisposition.match(/filename=(.+)/);
			if (match) {
				filename = match[1].replace(/['"]/g, '');
			}
		}

		// Create blob and trigger download
		const blob = await response.blob();
		const blobUrl = URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = blobUrl;
		link.download = filename;
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
		URL.revokeObjectURL(blobUrl);

		return { error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to download T4 XML';
		console.error('T4 XML download error:', err);
		return { error: message };
	}
}

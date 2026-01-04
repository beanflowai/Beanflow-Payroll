/**
 * Employee Portal Service
 *
 * Provides API functions for the Employee Self-Service Portal.
 * Fetches employee's own profile and paystub data.
 *
 * Architecture:
 * - Simple queries: Direct Supabase access (profile, paystub list, t4 list)
 * - Complex operations: Backend API (paystub detail with YTD, leave balance, PDF download)
 */

import { api } from '$lib/api/client';
import { supabase } from '$lib/api/supabase';
import type {
	PaystubSummary,
	PaystubDetail,
	PaystubYTD,
	EmployeePortalProfile,
	LeaveHistoryEntry,
	TaxDocument
} from '$lib/types/employee-portal';

// ============================================================================
// Types
// ============================================================================

export interface EmployeePortalProfileResponse {
	id: string;
	firstName: string;
	lastName: string;
	email: string;
	provinceOfEmployment: string;
	payFrequency: string;
	hireDate: string | null;
	vacationBalance: number;
	sickDaysRemaining: number;
}

export interface PaystubListResponse {
	paystubs: PaystubSummary[];
	ytdSummary: PaystubYTD;
}

export interface LeaveBalanceResponse {
	vacationHours: number;
	vacationDollars: number;
	vacationAccrualRate: number;
	vacationYtdAccrued: number;
	vacationYtdUsed: number;
	sickHoursRemaining: number;
	sickHoursAllowance: number;
	sickHoursUsedThisYear: number;
	leaveHistory: LeaveHistoryEntry[];
}

/** Embedded payroll run from Supabase !inner join */
interface EmbeddedPayrollRun {
	pay_date: string;
	period_start: string;
	period_end: string;
	status: string;
}

/** Payroll record with embedded run for Supabase queries */
interface PayrollRecordWithRun {
	id: string;
	total_gross: number | null;
	total_deductions: number | null;
	net_pay: number | null;
	ytd_gross: number | null;
	ytd_cpp: number | null;
	ytd_ei: number | null;
	ytd_federal_tax: number | null;
	ytd_provincial_tax: number | null;
	// Supabase returns embedded relations as arrays (even with !inner)
	payroll_runs: EmbeddedPayrollRun | EmbeddedPayrollRun[];
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Get the current employee's profile.
 * Uses email matching from authenticated user.
 * Direct Supabase query for simple profile data.
 *
 * @param companyId - Optional company ID to scope to a specific company
 * @returns Employee profile or throws error if not found
 */
export async function getCurrentEmployee(
	companyId?: string
): Promise<EmployeePortalProfileResponse> {
	const {
		data: { user }
	} = await supabase.auth.getUser();

	if (!user?.email) {
		throw new Error('Not authenticated');
	}

	// Build query
	let query = supabase
		.from('employees')
		.select('*')
		.eq('email', user.email)
		.not('portal_invited_at', 'is', null); // Must have been invited

	// If companyId provided, scope to that company
	if (companyId) {
		query = query.eq('company_id', companyId);
	} else {
		// Otherwise, prioritize the most recently invited company
		query = query.order('portal_invited_at', { ascending: false });
	}

	const { data, error } = await query.limit(1).single();

	if (error || !data) {
		throw new Error(`No employee record found for email: ${user.email}`);
	}

	return {
		id: data.id,
		firstName: data.first_name || '',
		lastName: data.last_name || '',
		email: data.email || '',
		provinceOfEmployment: data.province_of_employment || '',
		payFrequency: data.pay_frequency || '',
		hireDate: data.hire_date,
		vacationBalance: data.vacation_balance || 0,
		sickDaysRemaining: 0 // Note: Full sick leave calculation requires API call to getMyLeaveBalance
	};
}

/**
 * Mask a bank account number to show only last 4 digits: ****4567
 * Reserved for future use when bank account info is displayed.
 */
function _maskAccountNumber(account: string | null): string {
	if (!account) return '****';
	const digits = account.replace(/\D/g, '');
	if (digits.length < 4) return '****';
	const last4 = digits.slice(-4);
	return `****${last4}`;
}

/**
 * Get available years based on employee's hire date.
 * Returns years from hire date to current year in descending order.
 *
 * @param companyId - Optional company ID to scope to a specific company
 *                   (important for employees with records in multiple companies)
 * @returns Array of years
 */
export async function getAvailableYears(companyId?: string): Promise<number[]> {
	try {
		const employee = await getCurrentEmployee(companyId);
		const currentYear = new Date().getFullYear();
		let startYear = currentYear;

		if (employee.hireDate) {
			startYear = new Date(employee.hireDate).getFullYear();
		}

		const years: number[] = [];
		for (let year = currentYear; year >= startYear; year--) {
			years.push(year);
		}
		return years;
	} catch {
		return [new Date().getFullYear()];
	}
}

/**
 * Get the current employee's complete profile for the portal.
 * Uses backend API to get decrypted SIN for employee self-verification.
 *
 * @param companyId - Optional company ID to scope to a specific company
 * @returns Complete employee portal profile
 */
export async function getMyProfile(companyId?: string): Promise<EmployeePortalProfile> {
	const params: Record<string, string> = {};
	if (companyId) {
		params.company_id = companyId;
	}
	return api.get<EmployeePortalProfile>('/employee-portal/profile', params);
}

/**
 * Get the current employee's paystubs for a given year.
 * Direct Supabase query for paystub list.
 *
 * @param year - Year to filter paystubs (default: current year)
 * @param limit - Maximum number of paystubs to return (default: 20)
 * @param companyId - Optional company ID to scope to a specific company
 * @returns List of paystubs and YTD summary
 */
export async function getMyPaystubs(
	year: number = new Date().getFullYear(),
	limit: number = 20,
	companyId?: string
): Promise<PaystubListResponse> {
	const employee = await getCurrentEmployee(companyId);
	const yearStart = `${year}-01-01`;
	const yearEnd = `${year + 1}-01-01`;

	// Note: PostgREST doesn't support ordering by embedded resource fields,
	// so we fetch ALL records for the year, sort client-side, then apply limit.
	// This ensures YTD summary comes from the actual latest paystub.
	// Max records per year is ~26 (bi-weekly) so fetching all is reasonable.
	const { data, error } = await supabase
		.from('payroll_records')
		.select(
			`
			id,
			total_gross,
			total_deductions,
			net_pay,
			ytd_gross,
			ytd_cpp,
			ytd_ei,
			ytd_federal_tax,
			ytd_provincial_tax,
			payroll_runs!inner (
				pay_date,
				period_start,
				period_end,
				status
			)
		`
		)
		.eq('employee_id', employee.id)
		.eq('payroll_runs.status', 'approved')
		.gte('payroll_runs.pay_date', yearStart)
		.lt('payroll_runs.pay_date', yearEnd);

	if (error) {
		throw new Error(`Failed to fetch paystubs: ${error.message}`);
	}

	// Helper to get first embedded run (handles both array and single object)
	const getEmbeddedRun = (
		runs: EmbeddedPayrollRun | EmbeddedPayrollRun[] | null
	): EmbeddedPayrollRun | null => {
		if (!runs) return null;
		return Array.isArray(runs) ? runs[0] || null : runs;
	};

	// Cast to proper type and sort by pay_date descending
	const allRecords = (data || []) as unknown as PayrollRecordWithRun[];
	allRecords.sort((a, b) => {
		const runA = getEmbeddedRun(a.payroll_runs);
		const runB = getEmbeddedRun(b.payroll_runs);
		const dateA = runA?.pay_date || '';
		const dateB = runB?.pay_date || '';
		return dateB.localeCompare(dateA);
	});

	// Get YTD from the most recent record BEFORE applying limit
	let ytdSummary: PaystubYTD = { grossEarnings: 0, cppPaid: 0, eiPaid: 0, taxPaid: 0 };
	if (allRecords.length > 0) {
		const latest = allRecords[0];
		ytdSummary = {
			grossEarnings: latest.ytd_gross || 0,
			cppPaid: latest.ytd_cpp || 0,
			eiPaid: latest.ytd_ei || 0,
			taxPaid: (latest.ytd_federal_tax || 0) + (latest.ytd_provincial_tax || 0)
		};
	}

	// Apply limit after sorting to get the most recent records
	const records = allRecords.slice(0, limit);

	const paystubs: PaystubSummary[] = records.map((record) => {
		const run = getEmbeddedRun(record.payroll_runs);
		return {
			id: record.id,
			payDate: run?.pay_date || '',
			payPeriodStart: run?.period_start || '',
			payPeriodEnd: run?.period_end || '',
			grossPay: record.total_gross || 0,
			totalDeductions: record.total_deductions || 0,
			netPay: record.net_pay || 0
		};
	});

	return { paystubs, ytdSummary };
}

/**
 * Get detailed paystub for a specific payroll record.
 *
 * @param recordId - Payroll record ID
 * @returns Detailed paystub information
 */
export async function getPaystubDetail(recordId: string): Promise<PaystubDetail> {
	return api.get<PaystubDetail>(`/employee-portal/paystubs/${recordId}`);
}

/**
 * Check if the current user has an associated employee record.
 * Returns true if employee exists, false otherwise.
 */
export async function hasEmployeeRecord(): Promise<boolean> {
	try {
		await getCurrentEmployee();
		return true;
	} catch {
		return false;
	}
}

/**
 * Get the current employee's leave balance (vacation and sick leave).
 *
 * @param year - Year to get balance for (default: current year)
 * @param companyId - Optional company ID to scope to a specific company
 * @returns Leave balance with vacation, sick leave details and history
 */
export async function getMyLeaveBalance(
	year: number = new Date().getFullYear(),
	companyId?: string
): Promise<LeaveBalanceResponse> {
	const params: Record<string, string> = { year: String(year) };
	if (companyId) {
		params.company_id = companyId;
	}
	return api.get<LeaveBalanceResponse>('/employee-portal/leave-balance', params);
}

// ============================================================================
// T4 Tax Documents
// ============================================================================

export interface T4ListResponse {
	taxDocuments: TaxDocument[];
}

/**
 * Get the current employee's T4 tax documents.
 * Direct Supabase query for T4 document list.
 *
 * @param companyId - Optional company ID to scope to a specific company
 * @returns List of T4 documents available for download
 */
export async function getMyT4Documents(companyId?: string): Promise<T4ListResponse> {
	const employee = await getCurrentEmployee(companyId);

	const { data, error } = await supabase
		.from('t4_slips')
		.select('id, tax_year, employee_id, status, pdf_generated_at')
		.eq('employee_id', employee.id)
		.in('status', ['generated', 'filed', 'amended'])
		.order('tax_year', { ascending: false });

	if (error) {
		throw new Error(`Failed to fetch T4 documents: ${error.message}`);
	}

	const taxDocuments: TaxDocument[] = (data || []).map((slip) => ({
		id: slip.id,
		type: 'T4' as const,
		year: slip.tax_year,
		generatedAt: slip.pdf_generated_at || '',
		downloadUrl: '' // Will be generated on-demand via downloadMyT4
	}));

	return { taxDocuments };
}

/**
 * Download T4 slip PDF for a specific tax year.
 *
 * @param taxYear - Tax year to download
 * @param companyId - Optional company ID to scope to a specific company
 * @returns Blob URL for the PDF
 */
export async function downloadMyT4(
	taxYear: number,
	companyId?: string
): Promise<{ error: string | null }> {
	const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

	try {
		const {
			data: { session }
		} = await supabase.auth.getSession();
		if (!session?.access_token) {
			return { error: 'Not authenticated' };
		}

		let url = `${API_BASE_URL}/api/v1/employee-portal/t4/${taxYear}/download`;
		if (companyId) {
			url += `?company_id=${companyId}`;
		}
		const response = await fetch(url, {
			method: 'GET',
			headers: {
				Authorization: `Bearer ${session.access_token}`
			}
		});

		if (!response.ok) {
			const errorText = await response.text();
			console.error('T4 download failed:', response.status, errorText);
			return { error: `Download failed: ${response.status}` };
		}

		// Get filename from Content-Disposition header or use default
		const contentDisposition = response.headers.get('Content-Disposition');
		let filename = `T4_${taxYear}.pdf`;
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
		const message = err instanceof Error ? err.message : 'Failed to download T4';
		console.error('T4 download error:', err);
		return { error: message };
	}
}

// ============================================================================
// Profile Change Request Types
// ============================================================================

export interface ProfileChangeRequest {
	id: string;
	employeeId: string;
	employeeName: string;
	changeType: 'tax_info' | 'bank_info';
	status: 'pending' | 'approved' | 'rejected';
	currentValues: Record<string, unknown>;
	requestedValues: Record<string, unknown>;
	submittedAt: string;
	attachments?: string[];
	reviewedAt?: string;
	reviewedBy?: string;
	rejectionReason?: string;
}

export interface ProfileChangeListResponse {
	items: ProfileChangeRequest[];
	total: number;
}

export interface PersonalInfoFormData {
	phone?: string;
	address: {
		street?: string;
		city?: string;
		province?: string;
		postalCode?: string;
	};
	emergencyContact: {
		name?: string;
		relationship?: string;
		phone?: string;
	};
}

export interface TaxInfoFormData {
	federalAdditionalClaims?: number;
	provincialAdditionalClaims?: number;
}

export interface PortalInviteResponse {
	success: boolean;
	message: string;
	portalStatus: string;
}

// ============================================================================
// Employee Self-Service Functions
// ============================================================================

/**
 * Update employee's personal information.
 * This is auto-approved and directly updates the employees table.
 *
 * @param data - Personal info form data
 * @returns Success response
 */
export async function updatePersonalInfo(
	data: PersonalInfoFormData
): Promise<{ success: boolean; message: string }> {
	return api.put<{ success: boolean; message: string }>('/employee-portal/profile/personal', {
		phone: data.phone,
		addressStreet: data.address?.street,
		addressCity: data.address?.city,
		addressProvince: data.address?.province,
		addressPostalCode: data.address?.postalCode,
		emergencyName: data.emergencyContact?.name,
		emergencyRelationship: data.emergencyContact?.relationship,
		emergencyPhone: data.emergencyContact?.phone
	});
}

/**
 * Submit a tax info change request for employer approval.
 *
 * @param data - Tax info form data
 * @returns Created change request
 */
export async function submitTaxChange(data: TaxInfoFormData): Promise<ProfileChangeRequest> {
	return api.put<ProfileChangeRequest>('/employee-portal/profile/tax', {
		federalAdditionalClaims: data.federalAdditionalClaims,
		provincialAdditionalClaims: data.provincialAdditionalClaims
	});
}

// ============================================================================
// Employer Portal Management Functions
// ============================================================================

/**
 * Invite an employee to the employee portal.
 *
 * @param employeeId - Employee ID to invite
 * @param sendEmail - Whether to send invitation email (default: true)
 * @returns Invite response with portal status
 */
export async function inviteToPortal(
	employeeId: string,
	sendEmail: boolean = true
): Promise<PortalInviteResponse> {
	return api.post<PortalInviteResponse>(`/employees/${employeeId}/portal/invite`, {
		sendEmail
	});
}

/**
 * Get pending profile change requests for employer review.
 *
 * @param status - Filter by status (default: 'pending')
 * @returns List of profile change requests
 */
export async function getPendingProfileChanges(
	status: string = 'pending'
): Promise<ProfileChangeListResponse> {
	return api.get<ProfileChangeListResponse>('/profile-changes', { status });
}

/**
 * Approve a profile change request.
 *
 * @param changeId - Change request ID to approve
 * @returns Updated change request
 */
export async function approveProfileChange(changeId: string): Promise<ProfileChangeRequest> {
	return api.put<ProfileChangeRequest>(`/profile-changes/${changeId}/approve`);
}

/**
 * Reject a profile change request.
 *
 * @param changeId - Change request ID to reject
 * @param reason - Optional rejection reason
 * @returns Updated change request
 */
export async function rejectProfileChange(
	changeId: string,
	reason?: string
): Promise<ProfileChangeRequest> {
	return api.put<ProfileChangeRequest>(`/profile-changes/${changeId}/reject`, {
		rejectionReason: reason
	});
}

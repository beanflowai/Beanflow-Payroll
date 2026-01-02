/**
 * Employee Portal Service
 *
 * Provides API functions for the Employee Self-Service Portal.
 * Fetches employee's own profile and paystub data.
 */

import { api } from '$lib/api/client';
import type {
	PaystubSummary,
	PaystubDetail,
	PaystubYTD,
	EmployeePortalProfile,
	EmployeeLeaveBalance,
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

// ============================================================================
// API Functions
// ============================================================================

/**
 * Get the current employee's profile.
 * Uses email matching from authenticated user.
 *
 * @returns Employee profile or throws error if not found
 */
export async function getCurrentEmployee(): Promise<EmployeePortalProfileResponse> {
	return api.get<EmployeePortalProfileResponse>('/employee-portal/me');
}

/**
 * Get the current employee's paystubs for a given year.
 *
 * @param year - Year to filter paystubs (default: current year)
 * @param limit - Maximum number of paystubs to return (default: 20)
 * @returns List of paystubs and YTD summary
 */
export async function getMyPaystubs(
	year: number = new Date().getFullYear(),
	limit: number = 20
): Promise<PaystubListResponse> {
	return api.get<PaystubListResponse>('/employee-portal/paystubs', {
		year: String(year),
		limit: String(limit)
	});
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
 * @returns Leave balance with vacation, sick leave details and history
 */
export async function getMyLeaveBalance(
	year: number = new Date().getFullYear()
): Promise<LeaveBalanceResponse> {
	return api.get<LeaveBalanceResponse>('/employee-portal/leave-balance', {
		year: String(year)
	});
}

// ============================================================================
// T4 Tax Documents
// ============================================================================

export interface T4ListResponse {
	taxDocuments: TaxDocument[];
}

/**
 * Get the current employee's T4 tax documents.
 *
 * @returns List of T4 documents available for download
 */
export async function getMyT4Documents(): Promise<T4ListResponse> {
	return api.get<T4ListResponse>('/employee-portal/t4');
}

/**
 * Download T4 slip PDF for a specific tax year.
 *
 * @param taxYear - Tax year to download
 * @returns Blob URL for the PDF
 */
export async function downloadMyT4(taxYear: number): Promise<{ error: string | null }> {
	const { supabase } = await import('$lib/api/supabase');
	const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

	try {
		const {
			data: { session }
		} = await supabase.auth.getSession();
		if (!session?.access_token) {
			return { error: 'Not authenticated' };
		}

		const url = `${API_BASE_URL}/api/v1/employee-portal/t4/${taxYear}/download`;
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

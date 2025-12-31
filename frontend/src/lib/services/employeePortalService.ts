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
	LeaveHistoryEntry
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

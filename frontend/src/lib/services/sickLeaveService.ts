/**
 * Sick Leave Configuration Service
 *
 * Fetches sick leave configurations from the API.
 * Supports year and pay_date parameters for mid-year version selection.
 *
 * Reference: docs/08_holidays_vacation.md Task 8.7
 */

import { api } from '$lib/api/client';
import type { SickLeaveConfig, SickLeaveBalance } from '$lib/types/sick-leave';

// Cache for sick leave configs to avoid repeated API calls
const configCache = new Map<string, { data: SickLeaveConfig[]; timestamp: number }>();
const singleConfigCache = new Map<string, { data: SickLeaveConfig; timestamp: number }>();
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes cache

/**
 * Get all sick leave configurations from the API.
 *
 * @param year - Configuration year (default: 2025)
 * @param payDate - Optional pay date for edition selection
 * @returns Array of sick leave configurations
 */
export async function getSickLeaveConfigs(
	year: number = 2025,
	payDate?: Date
): Promise<SickLeaveConfig[]> {
	const cacheKey = `all-${year}-${payDate?.toISOString().split('T')[0] ?? 'default'}`;

	// Check cache
	const cached = configCache.get(cacheKey);
	if (cached && Date.now() - cached.timestamp < CACHE_TTL_MS) {
		return cached.data;
	}

	const params: Record<string, string> = { year: String(year) };
	if (payDate) {
		params['pay_date'] = payDate.toISOString().split('T')[0];
	}

	const data = await api.get<SickLeaveConfig[]>('/payroll/sick-leave/configs', params);

	// Update cache
	configCache.set(cacheKey, { data, timestamp: Date.now() });

	return data;
}

/**
 * Get sick leave configuration for a specific province.
 *
 * @param provinceCode - Province code (e.g., 'BC', 'ON', 'Federal')
 * @param year - Configuration year (default: 2025)
 * @param payDate - Optional pay date for edition selection
 * @returns Sick leave configuration or undefined if not found
 */
export async function getSickLeaveConfig(
	provinceCode: string,
	year: number = 2025,
	payDate?: Date
): Promise<SickLeaveConfig | undefined> {
	const cacheKey = `${provinceCode}-${year}-${payDate?.toISOString().split('T')[0] ?? 'default'}`;

	// Check cache
	const cached = singleConfigCache.get(cacheKey);
	if (cached && Date.now() - cached.timestamp < CACHE_TTL_MS) {
		return cached.data;
	}

	try {
		const params: Record<string, string> = { year: String(year) };
		if (payDate) {
			params['pay_date'] = payDate.toISOString().split('T')[0];
		}

		const data = await api.get<SickLeaveConfig>(
			`/payroll/sick-leave/configs/${provinceCode}`,
			params
		);

		// Update cache
		singleConfigCache.set(cacheKey, { data, timestamp: Date.now() });

		return data;
	} catch (error) {
		console.warn(`Failed to fetch sick leave config for ${provinceCode}:`, error);
		return undefined;
	}
}

/**
 * Check if province has statutory paid sick leave.
 *
 * @param provinceCode - Province code
 * @param year - Configuration year
 * @param payDate - Optional pay date
 * @returns True if province has paid sick leave
 */
export async function hasPaidSickLeave(
	provinceCode: string,
	year: number = 2025,
	payDate?: Date
): Promise<boolean> {
	const config = await getSickLeaveConfig(provinceCode, year, payDate);
	return config ? config.paidDaysPerYear > 0 : false;
}

/**
 * Get provinces with paid sick leave.
 *
 * @param year - Configuration year
 * @param payDate - Optional pay date
 * @returns Array of province codes with paid sick leave
 */
export async function getProvincesWithPaidSickLeave(
	year: number = 2025,
	payDate?: Date
): Promise<string[]> {
	const configs = await getSickLeaveConfigs(year, payDate);
	return configs.filter((c) => c.paidDaysPerYear > 0).map((c) => c.provinceCode);
}

/**
 * Normalize sick leave balance response to handle both snake_case and camelCase.
 * This handles potential API serialization differences.
 */
function normalizeSickLeaveBalance(data: Record<string, unknown>): SickLeaveBalance {
	return {
		employeeId: (data.employeeId ?? data.employee_id) as string,
		year: data.year as number,
		paidDaysEntitled: (data.paidDaysEntitled ?? data.paid_days_entitled ?? 0) as number,
		unpaidDaysEntitled: (data.unpaidDaysEntitled ?? data.unpaid_days_entitled ?? 0) as number,
		paidDaysUsed: (data.paidDaysUsed ?? data.paid_days_used ?? 0) as number,
		unpaidDaysUsed: (data.unpaidDaysUsed ?? data.unpaid_days_used ?? 0) as number,
		paidDaysRemaining: (data.paidDaysRemaining ?? data.paid_days_remaining ?? 0) as number,
		unpaidDaysRemaining: (data.unpaidDaysRemaining ?? data.unpaid_days_remaining ?? 0) as number,
		carriedOverDays: (data.carriedOverDays ?? data.carried_over_days ?? 0) as number,
		isEligible: (data.isEligible ?? data.is_eligible ?? false) as boolean,
		eligibilityDate: (data.eligibilityDate ?? data.eligibility_date) as string | undefined,
		accruedDaysYtd: (data.accruedDaysYtd ?? data.accrued_days_ytd ?? 0) as number,
		lastAccrualDate: (data.lastAccrualDate ?? data.last_accrual_date) as string | undefined
	};
}

/**
 * Get employee sick leave balance.
 *
 * @param employeeId - Employee UUID
 * @param year - Year to get balance for
 * @returns Sick leave balance or undefined if not found
 */
export async function getEmployeeSickLeaveBalance(
	employeeId: string,
	year: number
): Promise<SickLeaveBalance | undefined> {
	try {
		const data = await api.get<Record<string, unknown>>(
			`/payroll/employees/${employeeId}/sick-leave/${year}`
		);
		return normalizeSickLeaveBalance(data);
	} catch (error) {
		console.warn(`Failed to fetch sick leave balance for employee ${employeeId}:`, error);
		return undefined;
	}
}

/**
 * Clear the sick leave config cache.
 * Useful when user changes years or for testing.
 */
export function clearSickLeaveCache(): void {
	configCache.clear();
	singleConfigCache.clear();
}

/**
 * Sick Leave Types
 *
 * Types for sick leave configuration and balance tracking.
 * Matches backend sick_leave_service.py data models.
 *
 * NOTE: Configurations are now fetched from API via sickLeaveService.ts
 * instead of hardcoded values.
 *
 * Reference: docs/08_holidays_vacation.md Task 8.7
 */

// =============================================================================
// SICK LEAVE CONFIGURATION
// =============================================================================

/**
 * Accrual method for sick leave entitlement
 * - immediate: Full entitlement from eligibility date (BC, most provinces)
 * - monthly: Gradual accrual over time (Federal)
 */
export type SickLeaveAccrualMethod = 'immediate' | 'monthly';

/**
 * Province-level sick leave configuration
 */
export interface SickLeaveConfig {
	provinceCode: string;
	paidDaysPerYear: number;
	unpaidDaysPerYear: number;
	waitingPeriodDays: number;
	allowsCarryover: boolean;
	maxCarryoverDays: number;
	accrualMethod: SickLeaveAccrualMethod;
	initialDaysAfterQualifying: number; // For monthly accrual (Federal: 3)
	daysPerMonthAfterInitial: number; // For monthly accrual (Federal: 1)
	effectiveDate?: string;
	notes?: string;
}

// =============================================================================
// SICK LEAVE BALANCE
// =============================================================================

/**
 * Employee's sick leave balance for a year
 */
export interface SickLeaveBalance {
	employeeId: string;
	year: number;

	// Entitlement
	paidDaysEntitled: number;
	unpaidDaysEntitled: number;

	// Usage
	paidDaysUsed: number;
	unpaidDaysUsed: number;

	// Computed
	paidDaysRemaining: number;
	unpaidDaysRemaining: number;

	// Carryover (Federal only)
	carriedOverDays: number;

	// Eligibility
	isEligible: boolean;
	eligibilityDate?: string;

	// Accrual tracking (for monthly accrual)
	accruedDaysYtd: number;
	lastAccrualDate?: string;
}

/**
 * Database representation of sick leave balance
 */
export interface SickLeaveBalanceDB {
	id: string;
	employee_id: string;
	year: number;
	paid_days_entitled: number;
	unpaid_days_entitled: number;
	paid_days_used: number;
	unpaid_days_used: number;
	carried_over_days: number;
	eligibility_date: string | null;
	is_eligible: boolean;
	accrued_days_ytd: number;
	last_accrual_date: string | null;
	created_at: string;
	updated_at: string;
}

/**
 * Convert database format to frontend format
 */
export function mapSickLeaveBalanceFromDB(db: SickLeaveBalanceDB): SickLeaveBalance {
	return {
		employeeId: db.employee_id,
		year: db.year,
		paidDaysEntitled: db.paid_days_entitled,
		unpaidDaysEntitled: db.unpaid_days_entitled,
		paidDaysUsed: db.paid_days_used,
		unpaidDaysUsed: db.unpaid_days_used,
		paidDaysRemaining: db.paid_days_entitled + db.carried_over_days - db.paid_days_used,
		unpaidDaysRemaining: db.unpaid_days_entitled - db.unpaid_days_used,
		carriedOverDays: db.carried_over_days,
		isEligible: db.is_eligible,
		eligibilityDate: db.eligibility_date ?? undefined,
		accruedDaysYtd: db.accrued_days_ytd,
		lastAccrualDate: db.last_accrual_date ?? undefined
	};
}

// =============================================================================
// SICK PAY CALCULATION
// =============================================================================

/**
 * Result of sick pay calculation
 */
export interface SickPayResult {
	eligible: boolean;
	daysUsed: number;
	paidDays: number;
	unpaidDays: number;
	amount: number;
	averageDayPay: number;
	balanceAfter: number;
	reason?: string;
}

/**
 * Average day's pay calculation result
 */
export interface AverageDayPayResult {
	amount: number;
	calculationMethod: 'bc_30_day_avg' | 'federal_20_day_avg' | 'employer_provided';
	wagesIncluded: number;
	daysCounted: number;
}

// =============================================================================
// SICK LEAVE USAGE HISTORY
// =============================================================================

/**
 * Sick leave usage history entry
 */
export interface SickLeaveUsageEntry {
	id: string;
	employeeId: string;
	balanceId: string;
	payrollRecordId?: string;
	usageDate: string;
	hoursTaken: number;
	daysTaken: number;
	isPaid: boolean;
	averageDayPay: number;
	sickPayAmount: number;
	calculationMethod: string;
	notes?: string;
	createdAt: string;
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Calculate eligibility date based on hire date and waiting period.
 * This is a pure utility function that doesn't require API access.
 *
 * @param hireDate - Employee hire date (ISO string)
 * @param waitingPeriodDays - Waiting period in days
 * @returns Eligibility date (ISO string)
 */
export function calculateEligibilityDate(hireDate: string, waitingPeriodDays: number): string {
	if (waitingPeriodDays === 0) {
		return hireDate; // Immediately eligible
	}

	const hire = new Date(hireDate);
	hire.setDate(hire.getDate() + waitingPeriodDays);
	return hire.toISOString().split('T')[0];
}

/**
 * Check if employee is eligible for sick leave based on dates.
 * This is a pure utility function that doesn't require API access.
 *
 * @param eligibilityDate - Pre-calculated eligibility date
 * @param referenceDate - Date to check against (defaults to today)
 * @returns True if eligible
 */
export function isEligibleOnDate(
	eligibilityDate: string,
	referenceDate: string = new Date().toISOString().split('T')[0]
): boolean {
	return referenceDate >= eligibilityDate;
}

/**
 * Format sick leave balance display
 */
export function formatSickLeaveBalance(balance: SickLeaveBalance): string {
	const remaining = balance.paidDaysRemaining;
	const total = balance.paidDaysEntitled + balance.carriedOverDays;
	return `${remaining}/${total} days`;
}

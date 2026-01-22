/**
 * Payroll Draft Filter Utilities
 *
 * Core filtering logic for employee records in payroll draft view.
 * Supports cross-pay-group filtering while preserving group structure.
 */

import type {
	PayrollRecord,
	PayrollRunPayGroup,
	PayrollDraftFilters
} from '$lib/types/payroll';

/**
 * Check if a single payroll record matches the given filters
 *
 * @param record - The payroll record to check
 * @param filters - Current filter settings
 * @param payGroupId - The pay group ID this record belongs to
 * @param holidayProvinces - List of provinces that have holidays in the current period
 * @returns true if the record matches all active filters
 */
export function recordMatchesFilters(
	record: PayrollRecord,
	filters: PayrollDraftFilters,
	payGroupId: string,
	holidayProvinces: string[]
): boolean {
	// Search query (employee name - case-insensitive)
	if (filters.searchQuery) {
		const query = filters.searchQuery.toLowerCase();
		if (!record.employeeName.toLowerCase().includes(query)) {
			return false;
		}
	}

	// Pay group filter
	if (filters.payGroupId !== 'all' && payGroupId !== filters.payGroupId) {
		return false;
	}

	// No hours entered (hourly employees only)
	if (filters.showNoHoursEntered) {
		if (record.compensationType !== 'hourly') return false;
		const hours = record.regularHoursWorked ?? 0;
		if (hours > 0) return false;
	}

	// Zero earnings
	if (filters.showZeroEarnings && record.totalGross !== 0) {
		return false;
	}

	// Needs holiday pay (employee's province has holidays)
	if (filters.showNeedsHolidayPay) {
		if (!holidayProvinces.includes(record.employeeProvince)) return false;
	}

	return true;
}

/**
 * Filter payroll run pay groups based on the given filters
 *
 * Returns a new array of pay groups with filtered records.
 * Preserves the original group structure (groups with no matching records
 * will have empty records arrays).
 *
 * @param payGroups - Original pay groups from payroll run
 * @param filters - Current filter settings
 * @returns Filtered pay groups (new array, original not mutated)
 */
export function filterPayrollRun(
	payGroups: PayrollRunPayGroup[],
	filters: PayrollDraftFilters
): PayrollRunPayGroup[] {
	// Collect all unique provinces that have holidays across all pay groups
	const allHolidayProvinces = new Set<string>();
	payGroups.forEach((pg) => {
		pg.holidays?.forEach((h) => allHolidayProvinces.add(h.province));
	});

	const holidayProvinces = Array.from(allHolidayProvinces);

	// Map pay groups to filtered versions
	return payGroups.map((pg) => ({
		...pg,
		records: pg.records.filter((record) =>
			recordMatchesFilters(record, filters, pg.payGroupId, holidayProvinces)
		)
	}));
}

/**
 * Calculate filter statistics
 *
 * @param originalGroups - Original pay groups before filtering
 * @param filteredGroups - Pay groups after filtering
 * @returns Object with total and filtered employee counts
 */
export function calculateFilterStats(
	originalGroups: PayrollRunPayGroup[],
	filteredGroups: PayrollRunPayGroup[]
): { total: number; filtered: number } {
	const total = originalGroups.reduce((sum, pg) => sum + pg.records.length, 0);
	const filtered = filteredGroups.reduce((sum, pg) => sum + pg.records.length, 0);
	return { total, filtered };
}

/**
 * Get unique pay group info for filter dropdown
 *
 * @param payGroups - Pay groups from payroll run
 * @returns Array of pay group options for the filter dropdown
 */
export function getPayGroupFilterOptions(
	payGroups: PayrollRunPayGroup[]
): Array<{ payGroupId: string; payGroupName: string }> {
	return payGroups.map((pg) => ({
		payGroupId: pg.payGroupId,
		payGroupName: pg.payGroupName
	}));
}

/**
 * Get unique provinces from payroll records
 *
 * @param payGroups - Pay groups from payroll run
 * @returns Array of unique province codes
 */
export function getUniqueProvinces(payGroups: PayrollRunPayGroup[]): string[] {
	const provinces = new Set<string>();
	payGroups.forEach((pg) => {
		pg.records.forEach((record) => {
			provinces.add(record.employeeProvince);
		});
	});
	return Array.from(provinces).sort();
}

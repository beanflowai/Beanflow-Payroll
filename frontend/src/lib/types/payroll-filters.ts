/**
 * Payroll History Filters Types
 * Type definitions for payroll history page filters
 */

import type { DateRange } from '$lib/utils/dateUtils';

export interface PayrollHistoryFilters {
	status: string;
	payGroupId: string; // 第一级：Pay Group
	employeeId: string; // 第二级：Employee
	dateRange?: DateRange;
}

export const DEFAULT_PAYROLL_HISTORY_FILTERS: PayrollHistoryFilters = {
	status: 'all',
	payGroupId: 'all',
	employeeId: 'all',
	dateRange: undefined
};

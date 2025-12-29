/**
 * Payroll Service
 * Data access layer for payroll operations
 *
 * Hybrid Implementation:
 * - Simple CRUD: Direct Supabase queries
 * - Complex calculations: Backend API calls
 */

// Re-export all types
export type {
	PayrollServiceResult,
	PayrollDashboardStats,
	PayrollRunListOptions,
	PayrollRunListResult,
	EmployeeCompensationType,
	EmployeeForPayroll,
	EmployeeHoursInput,
	PayGroupWithEmployees,
	BeforeRunData,
	EmployeeCalculationRequest,
	BatchCalculationRequest,
	CalculationResult,
	BatchCalculationResponse
} from './types';

// Re-export dashboard functions
export {
	checkPayrollPageStatus,
	getUpcomingPeriods,
	getUpcomingPayDates,  // @deprecated - use getUpcomingPeriods
	getPayrollDashboardStats,
	getRecentCompletedRuns
} from './dashboard';

// Re-export payroll run functions
export {
	getPayrollRunByPayDate,
	getPayrollRunByPeriodEnd,
	getPayrollRunById,
	createPayrollRunForDate,
	updatePayrollRunStatus,
	approvePayrollRun,
	cancelPayrollRun,
	listPayrollRuns,
	updatePayrollRecord,
	recalculatePayrollRun,
	finalizePayrollRun,
	revertToDraft,
	checkHasModifiedRecords,
	syncEmployeesToRun,
	createOrGetPayrollRun,
	createOrGetPayrollRunByPeriodEnd,
	addEmployeeToRun,
	removeEmployeeFromRun,
	deletePayrollRun,
	getPaystubDownloadUrl,
	sendPaystubs,
	type SyncEmployeesResult,
	type CreateOrGetRunResult,
	type PayrollRunListOptionsExt
} from './payroll-runs';

// Re-export pay group functions
export {
	getPayGroupsForPeriodEnd,
	getPayGroupsWithEmployeesForPeriodEnd,
	getPayGroupsForPayDate,  // @deprecated - use getPayGroupsForPeriodEnd
	getPayGroupsWithEmployeesForPayDate  // @deprecated - use getPayGroupsWithEmployeesForPeriodEnd
} from './pay-groups';

// Re-export calculation functions
export {
	startPayrollRun
} from './calculation';

// Re-export helper functions
export {
	getCurrentUserId,
	ensureAuthenticated,
	getCurrentLedgerId,
	getProvincialBpa
} from './helpers';

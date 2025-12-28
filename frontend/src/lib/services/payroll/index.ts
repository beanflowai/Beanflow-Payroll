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
	getUpcomingPayDates,
	getPayrollDashboardStats,
	getRecentCompletedRuns
} from './dashboard';

// Re-export payroll run functions
export {
	getPayrollRunByPayDate,
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
	addEmployeeToRun,
	removeEmployeeFromRun,
	deletePayrollRun,
	type SyncEmployeesResult,
	type CreateOrGetRunResult,
	type PayrollRunListOptionsExt
} from './payroll-runs';

// Re-export pay group functions
export {
	getPayGroupsForPayDate,
	getPayGroupsWithEmployeesForPayDate
} from './pay-groups';

// Re-export calculation functions
export {
	startPayrollRun
} from './calculation';

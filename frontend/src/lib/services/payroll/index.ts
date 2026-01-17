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
	PayrollRunListOptionsExt,
	PayrollRunListResult,
	EmployeeCompensationType,
	EmployeeForPayroll,
	EmployeeHoursInput,
	PayGroupWithEmployees,
	BeforeRunData,
	EmployeeCalculationRequest,
	BatchCalculationRequest,
	CalculationResult,
	BatchCalculationResponse,
	PayrollRecordListOptions,
	PayrollRecordListResult,
	PayrollRecordWithPeriod
} from './types';

// Re-export dashboard functions
export {
	checkPayrollPageStatus,
	getUpcomingPeriods,
	getUpcomingPayDates, // @deprecated - use getUpcomingPeriods
	getPayrollDashboardStats,
	getRecentCompletedRuns
} from './dashboard';

// Re-export payroll run query functions
export {
	getPayrollRunByPayDate,
	getPayrollRunByPeriodEnd,
	getPayrollRunById,
	listPayrollRuns,
	listPayrollRecordsForEmployee,
	updatePayDate
} from './run-queries';

// Re-export payroll run status functions
export {
	updatePayrollRunStatus,
	approvePayrollRun,
	cancelPayrollRun,
	finalizePayrollRun,
	revertToDraft
} from './run-status';

// Re-export payroll run record functions
export { updatePayrollRecord, recalculatePayrollRun, checkHasModifiedRecords } from './run-records';

// Re-export payroll run employee functions
export {
	syncEmployeesToRun,
	addEmployeeToRun,
	removeEmployeeFromRun,
	type SyncEmployeesResult
} from './run-employees';

// Re-export payroll run lifecycle functions
export {
	createOrGetPayrollRun,
	createOrGetPayrollRunByPeriodEnd,
	createPayrollRunForDate,
	deletePayrollRun,
	type CreateOrGetRunResult
} from './run-lifecycle';

// Re-export paystub functions
export { getPaystubDownloadUrl, sendPaystubs } from './run-paystubs';

// Re-export pay group functions
export {
	getPayGroupsForPeriodEnd,
	getPayGroupsWithEmployeesForPeriodEnd,
	getPayGroupsForPayDate, // @deprecated - use getPayGroupsForPeriodEnd
	getPayGroupsWithEmployeesForPayDate // @deprecated - use getPayGroupsWithEmployeesForPeriodEnd
} from './pay-groups';

// Re-export calculation functions
export { startPayrollRun } from './calculation';

// Re-export helper functions
export {
	getCurrentUserId,
	ensureAuthenticated,
	getCurrentCompanyId,
	getProvincialBpa
} from './helpers';

/**
 * Payroll Run Employee Operations
 * Functions for managing employees within a payroll run
 */

import { api } from '$lib/api/client';
import { getCurrentUserId } from './helpers';
import type { PayrollServiceResult } from './types';

// ===========================================
// Sync Employees to Draft Run
// ===========================================

/**
 * Basic run info returned from sync API (without records)
 */
interface SyncRunInfo {
	id: string;
	payDate: string;
	status: string;
	totalEmployees: number;
	totalGross: number;
	totalNetPay: number;
}

/**
 * Response from sync employees API
 */
export interface SyncEmployeesResult {
	addedCount: number;
	addedEmployees: Array<{ employee_id: string; employee_name: string }>;
	run: SyncRunInfo;
}

/**
 * Sync new employees to a draft payroll run
 * When employees are added to pay groups after a run is created,
 * this function adds them to the existing run.
 *
 * Only works on draft runs. Non-draft runs return empty result.
 */
export async function syncEmployeesToRun(
	runId: string
): Promise<PayrollServiceResult<SyncEmployeesResult>> {
	try {
		getCurrentUserId();

		// Call backend sync-employees endpoint
		const response = await api.post<{
			addedCount: number;
			addedEmployees: Array<{ employee_id: string; employee_name: string }>;
			run: {
				id: string;
				payDate: string;
				status: string;
				totalEmployees: number;
				totalGross: number;
				totalNetPay: number;
			};
		}>(`/payroll/runs/${runId}/sync-employees`, {});

		return {
			data: {
				addedCount: response.addedCount,
				addedEmployees: response.addedEmployees,
				run: response.run
			},
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to sync employees';
		console.error('syncEmployeesToRun error:', message);
		return { data: null, error: message };
	}
}

// ===========================================
// Add/Remove Employees from Draft Run
// ===========================================

/**
 * Add an employee to a draft payroll run.
 * Creates a payroll record for the employee with initial calculations.
 */
export async function addEmployeeToRun(
	runId: string,
	employeeId: string
): Promise<PayrollServiceResult<{ employeeId: string; employeeName: string }>> {
	try {
		getCurrentUserId();

		const response = await api.post<{
			employeeId: string;
			employeeName: string;
		}>(`/payroll/runs/${runId}/employees`, { employeeId });

		return {
			data: {
				employeeId: response.employeeId,
				employeeName: response.employeeName
			},
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to add employee';
		console.error('addEmployeeToRun error:', message);
		return { data: null, error: message };
	}
}

/**
 * Remove an employee from a draft payroll run.
 * Deletes the payroll record for the employee.
 */
export async function removeEmployeeFromRun(
	runId: string,
	employeeId: string
): Promise<PayrollServiceResult<{ removed: boolean; employeeId: string }>> {
	try {
		getCurrentUserId();

		const response = await api.delete<{
			removed: boolean;
			employeeId: string;
		}>(`/payroll/runs/${runId}/employees/${employeeId}`);

		return {
			data: {
				removed: response.removed,
				employeeId: response.employeeId
			},
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to remove employee';
		console.error('removeEmployeeFromRun error:', message);
		return { data: null, error: message };
	}
}

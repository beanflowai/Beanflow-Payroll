/**
 * Payroll Run Lifecycle Operations
 * Functions for creating and deleting payroll runs
 */

import { api } from '$lib/api/client';
import type { PayrollRunWithGroups } from '$lib/types/payroll';
import { getCurrentUserId } from './helpers';
import { getPayrollRunByPayDate, getPayrollRunById } from './run-queries';
import type { PayrollServiceResult } from './types';

// ===========================================
// Create or Get Draft Run (Merged Flow)
// ===========================================

/**
 * Response from create-or-get payroll run API
 */
export interface CreateOrGetRunResult {
	created: boolean;
	recordsCount: number;
	synced?: boolean;
	addedCount?: number;
}

/**
 * Create or get a draft payroll run for a specific pay date.
 * If a run already exists, returns it. If not, creates a new draft run
 * with payroll records for all eligible employees.
 *
 * This is the main entry point for the merged Before Run + Draft flow.
 */
export async function createOrGetPayrollRun(
	payDate: string
): Promise<PayrollServiceResult<PayrollRunWithGroups & CreateOrGetRunResult>> {
	try {
		getCurrentUserId();

		// Call backend create-or-get endpoint
		const response = await api.post<{
			run: {
				id: string;
				payDate: string;
				status: string;
				totalEmployees: number;
				totalGross: number;
				totalCppEmployee: number;
				totalCppEmployer: number;
				totalEiEmployee: number;
				totalEiEmployer: number;
				totalFederalTax: number;
				totalProvincialTax: number;
				totalNetPay: number;
				totalEmployerCost: number;
			};
			created: boolean;
			recordsCount: number;
			synced?: boolean;
			addedCount?: number;
		}>('/payroll/runs/create-or-get', { payDate });

		// Get the full payroll run data with records
		const runResult = await getPayrollRunByPayDate(payDate);
		if (runResult.error || !runResult.data) {
			return { data: null, error: runResult.error ?? 'Failed to load payroll run' };
		}

		return {
			data: {
				...runResult.data,
				created: response.created,
				recordsCount: response.recordsCount,
				synced: response.synced,
				addedCount: response.addedCount
			},
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to create or get payroll run';
		console.error('createOrGetPayrollRun error:', message);
		return { data: null, error: message };
	}
}

/**
 * Create or get a draft payroll run for a specific period end.
 * Uses period_end as the primary identifier (pay_date is auto-calculated).
 *
 * This is the new entry point using period_end instead of pay_date.
 *
 * @param periodEnd - The period end date (YYYY-MM-DD)
 * @param payDate - Optional pay date override
 * @param payGroupIds - Optional pay group IDs to include (ensures correct groups when multiple exist)
 */
export async function createOrGetPayrollRunByPeriodEnd(
	periodEnd: string,
	payDate?: string,
	payGroupIds?: string[]
): Promise<PayrollServiceResult<PayrollRunWithGroups & CreateOrGetRunResult>> {
	try {
		getCurrentUserId();

		// Call backend create-or-get endpoint with periodEnd and optional payGroupIds
		const response = await api.post<{
			run: {
				id: string;
				periodEnd: string;
				payDate: string;
				status: string;
				totalEmployees: number;
				totalGross: number;
				totalCppEmployee: number;
				totalCppEmployer: number;
				totalEiEmployee: number;
				totalEiEmployer: number;
				totalFederalTax: number;
				totalProvincialTax: number;
				totalNetPay: number;
				totalEmployerCost: number;
			};
			created: boolean;
			recordsCount: number;
			synced?: boolean;
			addedCount?: number;
		}>('/payroll/runs/create-or-get', { periodEnd, payDate, payGroupIds });

		// Get the full payroll run data using the run ID returned by backend
		// This ensures we get the correct run when multiple runs exist for the same period_end
		const runResult = await getPayrollRunById(response.run.id);
		if (runResult.error || !runResult.data) {
			return { data: null, error: runResult.error ?? 'Failed to load payroll run' };
		}

		return {
			data: {
				...runResult.data,
				created: response.created,
				recordsCount: response.recordsCount,
				synced: response.synced,
				addedCount: response.addedCount
			},
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to create or get payroll run';
		console.error('createOrGetPayrollRunByPeriodEnd error:', message);
		return { data: null, error: message };
	}
}

// ===========================================
// Create Payroll Run (Deprecated)
// ===========================================

/**
 * Create a new payroll run for a specific date
 *
 * @deprecated Use createOrGetPayrollRun instead - it handles both create and get cases
 * and properly sets company_id via backend API.
 */
export async function createPayrollRunForDate(
	payDate: string,
	_periodStart: string,
	_periodEnd: string
): Promise<PayrollServiceResult<PayrollRunWithGroups>> {
	// Delegate to createOrGetPayrollRun which uses the backend API
	// Period start/end are calculated by backend based on pay groups
	const result = await createOrGetPayrollRun(payDate);
	if (result.error || !result.data) {
		return { data: null, error: result.error ?? 'Failed to create payroll run' };
	}
	// Return just the PayrollRunWithGroups portion (without created/recordsCount metadata)
	const {
		created: _created,
		recordsCount: _recordsCount,
		synced: _synced,
		addedCount: _addedCount,
		...runData
	} = result.data;
	return { data: runData, error: null };
}

// ===========================================
// Delete Draft Run
// ===========================================

/**
 * Delete a draft payroll run.
 * Only works on runs in 'draft' status. Deletes all associated records.
 */
export async function deletePayrollRun(
	runId: string
): Promise<PayrollServiceResult<{ deleted: boolean; runId: string }>> {
	try {
		getCurrentUserId();

		const response = await api.delete<{
			deleted: boolean;
			runId: string;
		}>(`/payroll/runs/${runId}`);

		return {
			data: {
				deleted: response.deleted,
				runId: response.runId
			},
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to delete payroll run';
		console.error('deletePayrollRun error:', message);
		return { data: null, error: message };
	}
}

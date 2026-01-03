/**
 * Payroll Run Record Operations
 * Functions for managing individual payroll records within a run
 */

import { supabase } from '$lib/api/supabase';
import { api } from '$lib/api/client';
import type { PayrollRunWithGroups, EmployeePayrollInput } from '$lib/types/payroll';
import { getCurrentUserId } from './helpers';
import { getPayrollRunById } from './run-queries';
import type { PayrollServiceResult } from './types';

// ===========================================
// Update Payroll Record
// ===========================================

/**
 * Update a single payroll record in a draft payroll run
 * Calls backend PATCH endpoint to update input_data and set is_modified=true
 */
export async function updatePayrollRecord(
	runId: string,
	recordId: string,
	updates: Partial<EmployeePayrollInput>
): Promise<PayrollServiceResult<PayrollRunWithGroups>> {
	try {
		getCurrentUserId();

		// Build request body matching backend UpdatePayrollRecordRequest
		const requestBody: Record<string, unknown> = {};

		if (updates.regularHours !== undefined) {
			requestBody.regularHours = updates.regularHours;
		}
		if (updates.overtimeHours !== undefined) {
			requestBody.overtimeHours = updates.overtimeHours;
		}
		if (updates.leaveEntries !== undefined) {
			requestBody.leaveEntries = updates.leaveEntries.map((entry) => ({
				type: entry.type,
				hours: entry.hours
			}));
		}
		if (updates.holidayWorkEntries !== undefined) {
			requestBody.holidayWorkEntries = updates.holidayWorkEntries.map((entry) => ({
				holidayDate: entry.holidayDate,
				holidayName: entry.holidayName,
				hoursWorked: entry.hoursWorked
			}));
		}
		if (updates.adjustments !== undefined) {
			requestBody.adjustments = updates.adjustments.map((adj) => ({
				type: adj.type,
				amount: adj.amount,
				description: adj.description,
				taxable: adj.taxable
			}));
		}
		if (updates.overrides !== undefined) {
			requestBody.overrides = {
				regularPay: updates.overrides.regularPay ?? null,
				overtimePay: updates.overrides.overtimePay ?? null,
				holidayPay: updates.overrides.holidayPay ?? null
			};
		}

		// Call backend API
		await api.patch(`/payroll/runs/${runId}/records/${recordId}`, requestBody);

		// Return updated payroll run data
		return getPayrollRunById(runId);
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to update payroll record';
		return { data: null, error: message };
	}
}

// ===========================================
// Recalculate Payroll Run
// ===========================================

/**
 * Recalculate all payroll records in a draft payroll run
 * Calls backend POST endpoint to recalculate all records using their input_data
 */
export async function recalculatePayrollRun(
	runId: string
): Promise<PayrollServiceResult<PayrollRunWithGroups>> {
	try {
		getCurrentUserId();

		// Call backend recalculate endpoint
		await api.post(`/payroll/runs/${runId}/recalculate`, {});

		// Return updated payroll run with recalculated values
		return getPayrollRunById(runId);
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to recalculate payroll run';
		console.error('recalculatePayrollRun error:', message);
		return { data: null, error: message };
	}
}

// ===========================================
// Check Modified Records
// ===========================================

/**
 * Check if a payroll run has modified records that need recalculation
 * Queries the database for any records with is_modified=true
 */
export async function checkHasModifiedRecords(
	runId: string
): Promise<PayrollServiceResult<boolean>> {
	try {
		const userId = getCurrentUserId();

		// Query for any records with is_modified = true (RLS handles access control)
		const { data, error } = await supabase
			.from('payroll_records')
			.select('id')
			.eq('payroll_run_id', runId)
			.eq('user_id', userId)
			.eq('is_modified', true)
			.limit(1);

		if (error) {
			console.error('Failed to check modified records:', error);
			return { data: null, error: error.message };
		}

		// Returns true if any records are modified
		return { data: data !== null && data.length > 0, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to check modified records';
		return { data: null, error: message };
	}
}

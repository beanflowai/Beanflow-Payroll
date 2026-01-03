/**
 * Payroll Run Status Management
 * Functions for updating payroll run status
 */

import { supabase } from '$lib/api/supabase';
import { api } from '$lib/api/client';
import type { PayrollRunWithGroups, PayrollRunStatus } from '$lib/types/payroll';
import { getCurrentUserId, getCurrentCompanyId } from './helpers';
import { getPayrollRunByPayDate, getPayrollRunById } from './run-queries';
import type { PayrollServiceResult } from './types';

// ===========================================
// Update Payroll Run Status
// ===========================================

/**
 * Update payroll run status
 */
export async function updatePayrollRunStatus(
	runId: string,
	status: PayrollRunStatus
): Promise<PayrollServiceResult<PayrollRunWithGroups>> {
	try {
		const userId = getCurrentUserId();
		const companyId = getCurrentCompanyId();

		const updateData: Record<string, unknown> = { status };

		// Add approval info if approving
		if (status === 'approved') {
			updateData.approved_by = userId;
			updateData.approved_at = new Date().toISOString();
		}

		const { data: runData, error: runError } = await supabase
			.from('payroll_runs')
			.update(updateData)
			.eq('user_id', userId)
			.eq('company_id', companyId)
			.eq('id', runId)
			.select()
			.single();

		if (runError) {
			console.error('Failed to update payroll run status:', runError);
			return { data: null, error: runError.message };
		}

		// Return the updated run
		return getPayrollRunByPayDate(runData.pay_date);
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to update payroll run status';
		return { data: null, error: message };
	}
}

/**
 * Approve a payroll run and send paystubs
 * Calls the backend API which:
 * 1. Generates paystub PDFs
 * 2. Updates status to approved
 * 3. Advances next_pay_date for affected pay groups
 */
export async function approvePayrollRun(
	runId: string
): Promise<PayrollServiceResult<PayrollRunWithGroups>> {
	try {
		getCurrentUserId();

		// Call backend approve endpoint
		await api.post<{
			id: string;
			payDate: string;
			status: string;
			totalEmployees: number;
			totalGross: number;
			totalNetPay: number;
			paystubsGenerated: number;
			paystubErrors: string[] | null;
		}>(`/payroll/runs/${runId}/approve`, {});

		// Return the updated run with full details
		return getPayrollRunById(runId);
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to approve payroll run';
		console.error('approvePayrollRun error:', message);
		return { data: null, error: message };
	}
}

/**
 * Cancel a payroll run
 */
export async function cancelPayrollRun(
	runId: string
): Promise<PayrollServiceResult<PayrollRunWithGroups>> {
	return updatePayrollRunStatus(runId, 'cancelled');
}

/**
 * Finalize a draft payroll run (change status to pending_approval)
 */
export async function finalizePayrollRun(
	runId: string
): Promise<PayrollServiceResult<PayrollRunWithGroups>> {
	return updatePayrollRunStatus(runId, 'pending_approval');
}

/**
 * Revert a pending_approval payroll run back to draft status
 * Allows user to make further edits after finalizing
 */
export async function revertToDraft(
	runId: string
): Promise<PayrollServiceResult<PayrollRunWithGroups>> {
	try {
		const userId = getCurrentUserId();
		const companyId = getCurrentCompanyId();

		// Verify run is in pending_approval status (filter by user_id and company_id)
		const { data: runData, error: runError } = await supabase
			.from('payroll_runs')
			.select('status')
			.eq('id', runId)
			.eq('user_id', userId)
			.eq('company_id', companyId)
			.single();

		if (runError) {
			return { data: null, error: runError.message };
		}

		if (runData.status !== 'pending_approval') {
			return {
				data: null,
				error: `Cannot revert: payroll run is in '${runData.status}' status, not 'pending_approval'`
			};
		}

		// Update status back to draft
		return updatePayrollRunStatus(runId, 'draft');
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to revert payroll run';
		return { data: null, error: message };
	}
}

/**
 * Payroll Runs Service
 * CRUD operations for payroll runs
 */

import { supabase } from '$lib/api/supabase';
import type {
	PayrollRunWithGroups,
	PayrollRunPayGroup,
	PayrollRunStatus,
	DbPayrollRun,
	DbPayrollRecordWithEmployee
} from '$lib/types/payroll';
import { dbPayrollRecordToUi } from '$lib/types/payroll';
import { getCurrentUserId, getCurrentLedgerId } from './helpers';
import type { PayrollServiceResult, PayrollRunListOptions, PayrollRunListResult } from './types';

// ===========================================
// Get Payroll Run
// ===========================================

/**
 * Get a payroll run by pay date
 */
export async function getPayrollRunByPayDate(
	payDate: string
): Promise<PayrollServiceResult<PayrollRunWithGroups>> {
	try {
		const userId = getCurrentUserId();
		const ledgerId = getCurrentLedgerId();

		// Query payroll run for this date
		const { data: runData, error: runError } = await supabase
			.from('payroll_runs')
			.select('*')
			.eq('user_id', userId)
			.eq('ledger_id', ledgerId)
			.eq('pay_date', payDate)
			.maybeSingle();

		if (runError) {
			console.error('Failed to get payroll run:', runError);
			return { data: null, error: runError.message };
		}

		if (!runData) {
			return { data: null, error: null };
		}

		// Get payroll records with employee and pay group info
		const { data: recordsData, error: recordsError } = await supabase
			.from('payroll_records')
			.select(`
				*,
				employees!inner (
					id,
					first_name,
					last_name,
					province_of_employment,
					pay_group_id,
					email,
					pay_groups (
						id,
						name,
						pay_frequency,
						employment_type
					)
				)
			`)
			.eq('payroll_run_id', runData.id);

		if (recordsError) {
			console.error('Failed to get payroll records:', recordsError);
			return { data: null, error: recordsError.message };
		}

		// Group records by pay group
		const payGroupMap = new Map<string, PayrollRunPayGroup>();

		for (const record of (recordsData as DbPayrollRecordWithEmployee[]) ?? []) {
			const payGroup = record.employees.pay_groups;
			const payGroupId = payGroup?.id ?? 'unknown';
			const payGroupName = payGroup?.name ?? 'Unknown Pay Group';

			const existing = payGroupMap.get(payGroupId);
			const uiRecord = dbPayrollRecordToUi(record);

			if (existing) {
				existing.records.push(uiRecord);
				existing.totalEmployees += 1;
				existing.totalGross += uiRecord.totalGross;
				existing.totalDeductions += uiRecord.totalDeductions;
				existing.totalNetPay += uiRecord.netPay;
				existing.totalEmployerCost += uiRecord.totalEmployerCost;
			} else {
				payGroupMap.set(payGroupId, {
					payGroupId,
					payGroupName,
					payFrequency: (payGroup?.pay_frequency ?? 'bi_weekly') as 'weekly' | 'bi_weekly' | 'semi_monthly' | 'monthly',
					employmentType: (payGroup?.employment_type ?? 'full_time') as 'full_time' | 'part_time',
					periodStart: runData.period_start,
					periodEnd: runData.period_end,
					totalEmployees: 1,
					totalGross: uiRecord.totalGross,
					totalDeductions: uiRecord.totalDeductions,
					totalNetPay: uiRecord.netPay,
					totalEmployerCost: uiRecord.totalEmployerCost,
					records: [uiRecord]
				});
			}
		}

		const dbRun = runData as DbPayrollRun;
		const result: PayrollRunWithGroups = {
			id: dbRun.id,
			payDate: dbRun.pay_date,
			status: dbRun.status,
			payGroups: Array.from(payGroupMap.values()),
			totalEmployees: dbRun.total_employees,
			totalGross: Number(dbRun.total_gross),
			totalCppEmployee: Number(dbRun.total_cpp_employee),
			totalCppEmployer: Number(dbRun.total_cpp_employer),
			totalEiEmployee: Number(dbRun.total_ei_employee),
			totalEiEmployer: Number(dbRun.total_ei_employer),
			totalFederalTax: Number(dbRun.total_federal_tax),
			totalProvincialTax: Number(dbRun.total_provincial_tax),
			totalDeductions: Number(dbRun.total_cpp_employee) + Number(dbRun.total_ei_employee) + Number(dbRun.total_federal_tax) + Number(dbRun.total_provincial_tax),
			totalNetPay: Number(dbRun.total_net_pay),
			totalEmployerCost: Number(dbRun.total_employer_cost),
			holidays: [] // Would load from a holidays table
		};

		return { data: result, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to get payroll run';
		console.error('getPayrollRunByPayDate error:', message);
		return { data: null, error: message };
	}
}

/**
 * Get a payroll run by ID
 */
export async function getPayrollRunById(
	runId: string
): Promise<PayrollServiceResult<PayrollRunWithGroups>> {
	try {
		const userId = getCurrentUserId();
		const ledgerId = getCurrentLedgerId();

		// Query payroll run by ID
		const { data: runData, error: runError } = await supabase
			.from('payroll_runs')
			.select('*')
			.eq('user_id', userId)
			.eq('ledger_id', ledgerId)
			.eq('id', runId)
			.maybeSingle();

		if (runError) {
			console.error('Failed to get payroll run:', runError);
			return { data: null, error: runError.message };
		}

		if (!runData) {
			return { data: null, error: null };
		}

		// Use getPayrollRunByPayDate to get full data
		return getPayrollRunByPayDate(runData.pay_date);
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to get payroll run';
		return { data: null, error: message };
	}
}

// ===========================================
// Create Payroll Run
// ===========================================

/**
 * Create a new payroll run for a specific date
 */
export async function createPayrollRunForDate(
	payDate: string,
	periodStart: string,
	periodEnd: string
): Promise<PayrollServiceResult<PayrollRunWithGroups>> {
	try {
		const userId = getCurrentUserId();
		const ledgerId = getCurrentLedgerId();

		// Create the payroll run
		const { data: runData, error: runError } = await supabase
			.from('payroll_runs')
			.insert({
				user_id: userId,
				ledger_id: ledgerId,
				period_start: periodStart,
				period_end: periodEnd,
				pay_date: payDate,
				status: 'draft'
			})
			.select()
			.single();

		if (runError) {
			console.error('Failed to create payroll run:', runError);
			return { data: null, error: runError.message };
		}

		// Return the created run
		return getPayrollRunByPayDate(payDate);
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to create payroll run';
		return { data: null, error: message };
	}
}

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
		const ledgerId = getCurrentLedgerId();

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
			.eq('ledger_id', ledgerId)
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
 */
export async function approvePayrollRun(
	runId: string
): Promise<PayrollServiceResult<PayrollRunWithGroups>> {
	return updatePayrollRunStatus(runId, 'approved');
}

/**
 * Cancel a payroll run
 */
export async function cancelPayrollRun(
	runId: string
): Promise<PayrollServiceResult<PayrollRunWithGroups>> {
	return updatePayrollRunStatus(runId, 'cancelled');
}

// ===========================================
// List Payroll Runs
// ===========================================

/**
 * List payroll runs with pagination
 */
export async function listPayrollRuns(
	options: PayrollRunListOptions = {}
): Promise<PayrollRunListResult> {
	const { status, limit = 20, offset = 0 } = options;

	try {
		const userId = getCurrentUserId();
		const ledgerId = getCurrentLedgerId();

		let query = supabase
			.from('payroll_runs')
			.select('*', { count: 'exact' })
			.eq('user_id', userId)
			.eq('ledger_id', ledgerId);

		if (status) {
			query = query.eq('status', status);
		}

		const { data, error, count } = await query
			.order('pay_date', { ascending: false })
			.range(offset, offset + limit - 1);

		if (error) {
			console.error('Failed to list payroll runs:', error);
			return { data: [], count: 0, error: error.message };
		}

		// Convert to PayrollRunWithGroups (simplified without records)
		const runs: PayrollRunWithGroups[] = (data as DbPayrollRun[]).map(dbRun => ({
			id: dbRun.id,
			payDate: dbRun.pay_date,
			status: dbRun.status,
			payGroups: [], // Would need separate query to get pay groups
			totalEmployees: dbRun.total_employees,
			totalGross: Number(dbRun.total_gross),
			totalCppEmployee: Number(dbRun.total_cpp_employee),
			totalCppEmployer: Number(dbRun.total_cpp_employer),
			totalEiEmployee: Number(dbRun.total_ei_employee),
			totalEiEmployer: Number(dbRun.total_ei_employer),
			totalFederalTax: Number(dbRun.total_federal_tax),
			totalProvincialTax: Number(dbRun.total_provincial_tax),
			totalDeductions: Number(dbRun.total_cpp_employee) + Number(dbRun.total_ei_employee) + Number(dbRun.total_federal_tax) + Number(dbRun.total_provincial_tax),
			totalNetPay: Number(dbRun.total_net_pay),
			totalEmployerCost: Number(dbRun.total_employer_cost)
		}));

		return { data: runs, count: count ?? 0, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to list payroll runs';
		return { data: [], count: 0, error: message };
	}
}

// ===========================================
// Draft Payroll Run Operations
// ===========================================

/**
 * Update a single payroll record in a draft payroll run
 * TODO: Implement actual database update
 */
export async function updatePayrollRecord(
	runId: string,
	recordId: string,
	updates: Record<string, unknown>
): Promise<PayrollServiceResult<PayrollRunWithGroups>> {
	try {
		getCurrentUserId();
		// TODO: Implement actual record update logic
		// For now, return error indicating not implemented
		console.warn('updatePayrollRecord not yet implemented', { runId, recordId, updates });
		return { data: null, error: 'updatePayrollRecord not yet implemented' };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to update payroll record';
		return { data: null, error: message };
	}
}

/**
 * Recalculate all payroll records in a draft payroll run
 * TODO: Implement actual recalculation via backend API
 */
export async function recalculatePayrollRun(
	runId: string
): Promise<PayrollServiceResult<PayrollRunWithGroups>> {
	try {
		getCurrentUserId();
		// TODO: Implement actual recalculation logic
		console.warn('recalculatePayrollRun not yet implemented', { runId });
		return { data: null, error: 'recalculatePayrollRun not yet implemented' };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to recalculate payroll run';
		return { data: null, error: message };
	}
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
 * Check if a payroll run has modified records that need recalculation
 * TODO: Implement actual check logic
 */
export async function checkHasModifiedRecords(
	runId: string
): Promise<PayrollServiceResult<boolean>> {
	try {
		getCurrentUserId();
		// TODO: Implement actual check logic
		// For now, always return false
		console.warn('checkHasModifiedRecords not yet implemented', { runId });
		return { data: false, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to check modified records';
		return { data: null, error: message };
	}
}

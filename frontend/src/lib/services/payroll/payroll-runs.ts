/**
 * Payroll Runs Service
 * CRUD operations for payroll runs
 */

import { supabase } from '$lib/api/supabase';
import { api } from '$lib/api/client';
import type {
	PayrollRunWithGroups,
	PayrollRunPayGroup,
	PayrollRunStatus,
	DbPayrollRun,
	DbPayrollRecordWithEmployee,
	EmployeePayrollInput
} from '$lib/types/payroll';
import { dbPayrollRecordToUi } from '$lib/types/payroll';
import {
	DEFAULT_EARNINGS_CONFIG,
	DEFAULT_TAXABLE_BENEFITS_CONFIG,
	DEFAULT_DEDUCTIONS_CONFIG,
	type EarningsConfig,
	type TaxableBenefitsConfig,
	type DeductionsConfig
} from '$lib/types/pay-group';
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
					hourly_rate,
					annual_salary,
					pay_groups (
						id,
						name,
						pay_frequency,
						employment_type,
						earnings_config,
						taxable_benefits_config,
						deductions_config
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
					records: [uiRecord],
					earningsConfig: (payGroup?.earnings_config as EarningsConfig | undefined) ?? DEFAULT_EARNINGS_CONFIG,
					taxableBenefitsConfig: (payGroup?.taxable_benefits_config as TaxableBenefitsConfig | undefined) ?? DEFAULT_TAXABLE_BENEFITS_CONFIG,
					deductionsConfig: (payGroup?.deductions_config as DeductionsConfig | undefined) ?? DEFAULT_DEDUCTIONS_CONFIG
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
		const ledgerId = getCurrentLedgerId();

		// Verify run is in pending_approval status
		const { data: runData, error: runError } = await supabase
			.from('payroll_runs')
			.select('status')
			.eq('id', runId)
			.eq('user_id', userId)
			.eq('ledger_id', ledgerId)
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

/**
 * Check if a payroll run has modified records that need recalculation
 * Queries the database for any records with is_modified=true
 */
export async function checkHasModifiedRecords(
	runId: string
): Promise<PayrollServiceResult<boolean>> {
	try {
		const userId = getCurrentUserId();
		const ledgerId = getCurrentLedgerId();

		// Query for any records with is_modified = true
		const { data, error } = await supabase
			.from('payroll_records')
			.select('id')
			.eq('payroll_run_id', runId)
			.eq('user_id', userId)
			.eq('ledger_id', ledgerId)
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

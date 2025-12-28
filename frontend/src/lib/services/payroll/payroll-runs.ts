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
	DEFAULT_GROUP_BENEFITS,
	type EarningsConfig,
	type TaxableBenefitsConfig,
	type DeductionsConfig,
	type GroupBenefits
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
						deductions_config,
						group_benefits
					)
				)
			`)
			.eq('payroll_run_id', runData.id);

		if (recordsError) {
			console.error('Failed to get payroll records:', recordsError);
			return { data: null, error: recordsError.message };
		}

		// Group records by pay group (use snapshot fields for historical accuracy)
		const payGroupMap = new Map<string, PayrollRunPayGroup>();

		for (const record of (recordsData as DbPayrollRecordWithEmployee[]) ?? []) {
			const payGroup = record.employees.pay_groups;
			// Use snapshot fields for grouping to preserve historical pay group assignment
			// Fallback to joined data for records created before snapshots were added
			const payGroupId = record.pay_group_id_snapshot ?? payGroup?.id ?? 'unknown';
			const payGroupName = record.pay_group_name_snapshot ?? payGroup?.name ?? 'Unknown Pay Group';

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
					deductionsConfig: (payGroup?.deductions_config as DeductionsConfig | undefined) ?? DEFAULT_DEDUCTIONS_CONFIG,
					groupBenefits: (payGroup?.group_benefits as GroupBenefits | undefined) ?? DEFAULT_GROUP_BENEFITS
				});
			}
		}

		const dbRun = runData as DbPayrollRun;
		const totalGross = Number(dbRun.total_gross);
		const totalNetPay = Number(dbRun.total_net_pay);
		const totalCppEmployee = Number(dbRun.total_cpp_employee);
		const totalCppEmployer = Number(dbRun.total_cpp_employer);
		const totalEiEmployee = Number(dbRun.total_ei_employee);
		const totalEiEmployer = Number(dbRun.total_ei_employer);
		const totalFederalTax = Number(dbRun.total_federal_tax);
		const totalProvincialTax = Number(dbRun.total_provincial_tax);
		const totalEmployerCost = Number(dbRun.total_employer_cost);

		const result: PayrollRunWithGroups = {
			id: dbRun.id,
			payDate: dbRun.pay_date,
			status: dbRun.status,
			payGroups: Array.from(payGroupMap.values()),
			totalEmployees: dbRun.total_employees,
			totalGross,
			totalCppEmployee,
			totalCppEmployer,
			totalEiEmployee,
			totalEiEmployer,
			totalFederalTax,
			totalProvincialTax,
			// Fixed: totalDeductions = totalGross - totalNetPay
			totalDeductions: totalGross - totalNetPay,
			totalNetPay,
			totalEmployerCost,
			// New: totalPayrollCost = totalGross + totalEmployerCost
			totalPayrollCost: totalGross + totalEmployerCost,
			// New: totalRemittance = all CPP/EI (employee + employer) + taxes
			totalRemittance: totalCppEmployee + totalCppEmployer + totalEiEmployee + totalEiEmployer + totalFederalTax + totalProvincialTax,
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
 * Extended options for listing payroll runs
 */
export interface PayrollRunListOptionsExt extends PayrollRunListOptions {
	excludeStatuses?: string[];
}

/**
 * Payroll run list item from API
 */
interface ApiPayrollRunListItem {
	id: string;
	payDate: string;
	periodStart: string;
	periodEnd: string;
	status: string;
	totalEmployees: number;
	totalGross: number;
	totalNetPay: number;
	totalEmployerCost: number;
}

/**
 * List payroll runs with pagination via backend API
 */
export async function listPayrollRuns(
	options: PayrollRunListOptionsExt = {}
): Promise<PayrollRunListResult> {
	const { status, excludeStatuses, limit = 20, offset = 0 } = options;

	try {
		getCurrentUserId();

		// Build query params
		const params = new URLSearchParams();
		if (status) {
			params.append('run_status', status);
		}
		if (excludeStatuses && excludeStatuses.length > 0) {
			params.append('excludeStatus', excludeStatuses.join(','));
		}
		params.append('limit', String(limit));
		params.append('offset', String(offset));

		// Call backend API
		const response = await api.get<{
			runs: ApiPayrollRunListItem[];
			total: number;
		}>(`/payroll/runs?${params.toString()}`);

		// Convert API response to PayrollRunWithGroups
		const runs: PayrollRunWithGroups[] = response.runs.map(run => {
			const totalGross = run.totalGross;
			const totalNetPay = run.totalNetPay;
			const totalEmployerCost = run.totalEmployerCost;

			return {
				id: run.id,
				payDate: run.payDate,
				status: run.status as PayrollRunStatus,
				payGroups: [],
				totalEmployees: run.totalEmployees,
				totalGross,
				totalCppEmployee: 0,
				totalCppEmployer: 0,
				totalEiEmployee: 0,
				totalEiEmployer: 0,
				totalFederalTax: 0,
				totalProvincialTax: 0,
				totalDeductions: totalGross - totalNetPay,
				totalNetPay,
				totalEmployerCost,
				totalPayrollCost: totalGross + totalEmployerCost,
				totalRemittance: 0
			};
		});

		return { data: runs, count: response.total, error: null };
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
// Create or Get Draft Run (Merged Flow)
// ===========================================

/**
 * Response from create-or-get payroll run API
 */
export interface CreateOrGetRunResult {
	created: boolean;
	recordsCount: number;
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
				recordsCount: response.recordsCount
			},
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to create or get payroll run';
		console.error('createOrGetPayrollRun error:', message);
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

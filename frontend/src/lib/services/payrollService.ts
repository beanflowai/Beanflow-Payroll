/**
 * Payroll Service - Data access layer for payroll operations
 *
 * Supabase Implementation - Direct database queries only
 */

import { supabase } from '$lib/api/supabase';
import { authState } from '$lib/stores/auth.svelte';
import type {
	UpcomingPayDate,
	PayrollRunWithGroups,
	PayrollRunPayGroup,
	PayrollRunStatus,
	PayrollPageStatus,
	DbPayrollRun,
	DbPayrollRecordWithEmployee
} from '$lib/types/payroll';
import { dbPayrollRecordToUi } from '$lib/types/payroll';

// ===========================================
// Helper Functions
// ===========================================

function getCurrentUserId(): string {
	const user = authState.user;
	if (!user) throw new Error('User not authenticated');
	return user.id;
}

function getCurrentLedgerId(): string {
	const user = authState.user;
	if (!user) throw new Error('User not authenticated');
	return user.id; // Using user ID as ledger_id for simplicity
}

// ===========================================
// Service Result Types
// ===========================================

export interface PayrollServiceResult<T> {
	data: T | null;
	error: string | null;
}

// ===========================================
// Page Status Check
// ===========================================

/**
 * Check the status of the payroll page to determine what to display:
 * - no_pay_groups: User needs to create pay groups first
 * - no_employees: Pay groups exist but no employees assigned
 * - ready: Ready to run payroll
 */
export async function checkPayrollPageStatus(): Promise<PayrollServiceResult<PayrollPageStatus>> {
	try {
		getCurrentUserId();

		// Query pay groups count via the summary view
		const { data: payGroups, error: pgError } = await supabase
			.from('v_pay_group_summary')
			.select('id, employee_count')
			.limit(100);

		if (pgError) {
			console.error('Failed to query pay groups:', pgError);
			return { data: null, error: pgError.message };
		}

		if (!payGroups || payGroups.length === 0) {
			return {
				data: { status: 'no_pay_groups' },
				error: null
			};
		}

		const payGroupCount = payGroups.length;
		const totalEmployees = payGroups.reduce((sum, pg) => sum + (pg.employee_count ?? 0), 0);

		if (totalEmployees === 0) {
			return {
				data: { status: 'no_employees', payGroupCount },
				error: null
			};
		}

		return {
			data: {
				status: 'ready',
				payGroupCount,
				employeeCount: totalEmployees
			},
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to check payroll status';
		console.error('checkPayrollPageStatus error:', message);
		return { data: null, error: message };
	}
}

// ===========================================
// Upcoming Pay Dates
// ===========================================

/**
 * Get upcoming pay dates for the dashboard
 * Queries pay_groups to calculate upcoming pay dates based on next_pay_date
 */
export async function getUpcomingPayDates(): Promise<PayrollServiceResult<UpcomingPayDate[]>> {
	try {
		getCurrentUserId();

		// Query pay groups with employee counts
		const { data: payGroups, error: pgError } = await supabase
			.from('v_pay_group_summary')
			.select('*')
			.order('next_pay_date');

		if (pgError) {
			console.error('Failed to query pay groups:', pgError);
			return { data: null, error: pgError.message };
		}

		if (!payGroups || payGroups.length === 0) {
			return { data: [], error: null };
		}

		// Group pay groups by next_pay_date
		const payDateMap = new Map<string, UpcomingPayDate>();

		for (const pg of payGroups) {
			const payDate = pg.next_pay_date;
			if (!payDate) continue;

			// Calculate period start/end (simplified: 2 weeks before pay date for bi-weekly)
			const payDateObj = new Date(payDate);
			const periodEnd = new Date(payDateObj);
			periodEnd.setDate(periodEnd.getDate() - 6); // 6 days before pay date
			const periodStart = new Date(periodEnd);
			periodStart.setDate(periodStart.getDate() - 13); // 14 day period

			const existing = payDateMap.get(payDate);
			const payGroupSummary = {
				id: pg.id,
				name: pg.name,
				payFrequency: pg.pay_frequency,
				employmentType: pg.employment_type,
				employeeCount: pg.employee_count ?? 0,
				estimatedGross: 0, // Would need salary data to estimate
				periodStart: periodStart.toISOString().split('T')[0],
				periodEnd: periodEnd.toISOString().split('T')[0]
			};

			if (existing) {
				existing.payGroups.push(payGroupSummary);
				existing.totalEmployees += pg.employee_count ?? 0;
			} else {
				payDateMap.set(payDate, {
					payDate,
					payGroups: [payGroupSummary],
					totalEmployees: pg.employee_count ?? 0,
					totalEstimatedGross: 0
				});
			}
		}

		// Check for existing payroll runs for these dates
		const payDates = Array.from(payDateMap.keys());
		if (payDates.length > 0) {
			const { data: runs } = await supabase
				.from('payroll_runs')
				.select('id, pay_date, status')
				.in('pay_date', payDates);

			if (runs) {
				for (const run of runs) {
					const upcomingPayDate = payDateMap.get(run.pay_date);
					if (upcomingPayDate) {
						upcomingPayDate.runId = run.id;
						upcomingPayDate.runStatus = run.status as PayrollRunStatus;
					}
				}
			}
		}

		// Sort by pay date
		const result = Array.from(payDateMap.values()).sort(
			(a, b) => new Date(a.payDate).getTime() - new Date(b.payDate).getTime()
		);

		return { data: result, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to get upcoming pay dates';
		console.error('getUpcomingPayDates error:', message);
		return { data: null, error: message };
	}
}

// ===========================================
// Payroll Run Operations
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
			.single();

		if (runError) {
			// Not found is not an error, just return null
			if (runError.code === 'PGRST116') {
				return { data: null, error: null };
			}
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
			.single();

		if (runError) {
			if (runError.code === 'PGRST116') {
				return { data: null, error: null };
			}
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
// Dashboard Statistics
// ===========================================

export interface PayrollDashboardStats {
	upcomingCount: number;
	nextPayDate: string | null;
	nextPayDateEmployees: number;
	nextPayDateEstimatedGross: number;
}

export async function getPayrollDashboardStats(): Promise<PayrollServiceResult<PayrollDashboardStats>> {
	try {
		const { data: upcomingPayDates, error } = await getUpcomingPayDates();

		if (error || !upcomingPayDates) {
			return { data: null, error: error ?? 'Failed to get upcoming pay dates' };
		}

		const nextPayDate = upcomingPayDates.length > 0 ? upcomingPayDates[0] : null;

		const stats: PayrollDashboardStats = {
			upcomingCount: upcomingPayDates.length,
			nextPayDate: nextPayDate?.payDate ?? null,
			nextPayDateEmployees: nextPayDate?.totalEmployees ?? 0,
			nextPayDateEstimatedGross: nextPayDate?.totalEstimatedGross ?? 0
		};

		return { data: stats, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to get dashboard stats';
		return { data: null, error: message };
	}
}

// ===========================================
// Payroll Run List
// ===========================================

/**
 * List payroll runs with pagination
 */
export interface PayrollRunListOptions {
	status?: PayrollRunStatus;
	limit?: number;
	offset?: number;
}

export interface PayrollRunListResult {
	data: PayrollRunWithGroups[];
	count: number;
	error: string | null;
}

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
// Pay Groups for Specific Pay Date
// ===========================================

/**
 * Get pay groups for a specific pay date
 * Used on the Payroll Run page to show pay groups even when no payroll run exists
 */
export async function getPayGroupsForPayDate(
	payDate: string
): Promise<PayrollServiceResult<UpcomingPayDate | null>> {
	try {
		getCurrentUserId();

		// Query pay groups with this next_pay_date
		const { data: payGroups, error: pgError } = await supabase
			.from('v_pay_group_summary')
			.select('*')
			.eq('next_pay_date', payDate);

		if (pgError) {
			console.error('Failed to query pay groups:', pgError);
			return { data: null, error: pgError.message };
		}

		if (!payGroups || payGroups.length === 0) {
			return { data: null, error: null };
		}

		// Calculate period dates (simplified: 2 weeks before pay date for bi-weekly)
		const payDateObj = new Date(payDate);
		const periodEnd = new Date(payDateObj);
		periodEnd.setDate(periodEnd.getDate() - 6);
		const periodStart = new Date(periodEnd);
		periodStart.setDate(periodStart.getDate() - 13);

		const result: UpcomingPayDate = {
			payDate,
			payGroups: payGroups.map((pg) => ({
				id: pg.id,
				name: pg.name,
				payFrequency: pg.pay_frequency,
				employmentType: pg.employment_type,
				employeeCount: pg.employee_count ?? 0,
				estimatedGross: 0,
				periodStart: periodStart.toISOString().split('T')[0],
				periodEnd: periodEnd.toISOString().split('T')[0]
			})),
			totalEmployees: payGroups.reduce((sum, pg) => sum + (pg.employee_count ?? 0), 0),
			totalEstimatedGross: 0
		};

		// Check for existing payroll run
		const { data: runs } = await supabase
			.from('payroll_runs')
			.select('id, status')
			.eq('pay_date', payDate)
			.single();

		if (runs) {
			result.runId = runs.id;
			result.runStatus = runs.status as PayrollRunStatus;
		}

		return { data: result, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to get pay groups for date';
		console.error('getPayGroupsForPayDate error:', message);
		return { data: null, error: message };
	}
}

// ===========================================
// Pay Groups with Employees (Before Run State)
// ===========================================

/**
 * Employee info for "before run" state (no payroll calculations yet)
 */
export interface EmployeeForPayroll {
	id: string;
	firstName: string;
	lastName: string;
	province: string;
	payGroupId: string;
	annualSalary: number | null;
	hourlyRate: number | null;
}

/**
 * Pay group with employees for "before run" state
 */
export interface PayGroupWithEmployees {
	id: string;
	name: string;
	payFrequency: 'weekly' | 'bi_weekly' | 'semi_monthly' | 'monthly';
	employmentType: 'full_time' | 'part_time';
	periodStart: string;
	periodEnd: string;
	employees: EmployeeForPayroll[];
}

/**
 * Data for "before run" state - pay groups with their employees
 */
export interface BeforeRunData {
	payDate: string;
	payGroups: PayGroupWithEmployees[];
	totalEmployees: number;
	holidays: { date: string; name: string; province: string }[];
}

/**
 * Get pay groups with employees for a specific pay date (before payroll run is created)
 * This is used to display the full UI with employee list before clicking "Start Payroll Run"
 */
export async function getPayGroupsWithEmployeesForPayDate(
	payDate: string
): Promise<PayrollServiceResult<BeforeRunData>> {
	try {
		const userId = getCurrentUserId();
		const ledgerId = getCurrentLedgerId();

		// Query pay groups with this next_pay_date
		const { data: payGroups, error: pgError } = await supabase
			.from('v_pay_group_summary')
			.select('*')
			.eq('next_pay_date', payDate);

		if (pgError) {
			console.error('Failed to query pay groups:', pgError);
			return { data: null, error: pgError.message };
		}

		if (!payGroups || payGroups.length === 0) {
			return { data: null, error: null };
		}

		// Calculate period dates (simplified: 2 weeks before pay date for bi-weekly)
		const payDateObj = new Date(payDate);
		const periodEnd = new Date(payDateObj);
		periodEnd.setDate(periodEnd.getDate() - 6);
		const periodStart = new Date(periodEnd);
		periodStart.setDate(periodStart.getDate() - 13);

		const periodStartStr = periodStart.toISOString().split('T')[0];
		const periodEndStr = periodEnd.toISOString().split('T')[0];

		// Get employees for each pay group
		const payGroupsWithEmployees: PayGroupWithEmployees[] = [];
		let totalEmployees = 0;

		for (const pg of payGroups) {
			const { data: employees, error: empError } = await supabase
				.from('employees')
				.select('id, first_name, last_name, province_of_employment, pay_group_id, annual_salary, hourly_rate')
				.eq('user_id', userId)
				.eq('ledger_id', ledgerId)
				.eq('pay_group_id', pg.id)
				.is('termination_date', null)
				.order('last_name')
				.order('first_name');

			if (empError) {
				console.error('Failed to query employees for pay group:', empError);
				continue;
			}

			const employeeList: EmployeeForPayroll[] = (employees ?? []).map((emp) => ({
				id: emp.id,
				firstName: emp.first_name,
				lastName: emp.last_name,
				province: emp.province_of_employment,
				payGroupId: emp.pay_group_id,
				annualSalary: emp.annual_salary ? Number(emp.annual_salary) : null,
				hourlyRate: emp.hourly_rate ? Number(emp.hourly_rate) : null
			}));

			payGroupsWithEmployees.push({
				id: pg.id,
				name: pg.name,
				payFrequency: pg.pay_frequency,
				employmentType: pg.employment_type,
				periodStart: periodStartStr,
				periodEnd: periodEndStr,
				employees: employeeList
			});

			totalEmployees += employeeList.length;
		}

		// Get holidays for the pay period
		// For now, returning empty array - would query from holidays table
		const holidays: { date: string; name: string; province: string }[] = [];

		return {
			data: {
				payDate,
				payGroups: payGroupsWithEmployees,
				totalEmployees,
				holidays
			},
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to get pay groups with employees';
		console.error('getPayGroupsWithEmployeesForPayDate error:', message);
		return { data: null, error: message };
	}
}

// ===========================================
// Start Payroll Run
// ===========================================

/**
 * Start a payroll run for a specific pay date
 * Creates the payroll_runs record and payroll_records for all employees
 * Calculates CPP, EI, and taxes for each employee
 */
export async function startPayrollRun(
	payDate: string
): Promise<PayrollServiceResult<PayrollRunWithGroups>> {
	try {
		const userId = getCurrentUserId();
		const ledgerId = getCurrentLedgerId();

		// First, get pay groups with employees
		const beforeRunResult = await getPayGroupsWithEmployeesForPayDate(payDate);
		if (beforeRunResult.error || !beforeRunResult.data) {
			return { data: null, error: beforeRunResult.error ?? 'No pay groups found for this date' };
		}

		const { payGroups, totalEmployees } = beforeRunResult.data;

		if (totalEmployees === 0) {
			return { data: null, error: 'No employees to process for this pay date' };
		}

		// Calculate period dates from the first pay group
		const periodStart = payGroups[0].periodStart;
		const periodEnd = payGroups[0].periodEnd;

		// Create the payroll_runs record
		const { data: runData, error: runError } = await supabase
			.from('payroll_runs')
			.insert({
				user_id: userId,
				ledger_id: ledgerId,
				period_start: periodStart,
				period_end: periodEnd,
				pay_date: payDate,
				status: 'pending_approval',
				total_employees: totalEmployees,
				total_gross: 0,
				total_cpp_employee: 0,
				total_cpp_employer: 0,
				total_ei_employee: 0,
				total_ei_employer: 0,
				total_federal_tax: 0,
				total_provincial_tax: 0,
				total_net_pay: 0,
				total_employer_cost: 0
			})
			.select()
			.single();

		if (runError) {
			console.error('Failed to create payroll run:', runError);
			return { data: null, error: runError.message };
		}

		const runId = runData.id;

		// Calculate and create payroll records for each employee
		let totalGross = 0;
		let totalCppEmployee = 0;
		let totalCppEmployer = 0;
		let totalEiEmployee = 0;
		let totalEiEmployer = 0;
		let totalFederalTax = 0;
		let totalProvincialTax = 0;
		let totalNetPay = 0;
		let totalEmployerCost = 0;

		const payrollRecords: Array<{
			payroll_run_id: string;
			employee_id: string;
			user_id: string;
			ledger_id: string;
			gross_regular: number;
			gross_overtime: number;
			holiday_pay: number;
			holiday_premium_pay: number;
			vacation_pay_paid: number;
			other_earnings: number;
			cpp_employee: number;
			cpp_additional: number;
			ei_employee: number;
			federal_tax: number;
			provincial_tax: number;
			rrsp: number;
			union_dues: number;
			garnishments: number;
			other_deductions: number;
			cpp_employer: number;
			ei_employer: number;
			ytd_gross: number;
			ytd_cpp: number;
			ytd_ei: number;
			ytd_federal_tax: number;
			ytd_provincial_tax: number;
			vacation_accrued: number;
			vacation_hours_taken: number;
		}> = [];

		for (const payGroup of payGroups) {
			for (const employee of payGroup.employees) {
				// Calculate gross pay based on salary or hourly rate
				let grossRegular = 0;
				if (employee.annualSalary) {
					// For salaried employees, divide annual salary by pay periods
					const periodsPerYear = payGroup.payFrequency === 'weekly' ? 52 :
						payGroup.payFrequency === 'bi_weekly' ? 26 :
						payGroup.payFrequency === 'semi_monthly' ? 24 : 12;
					grossRegular = employee.annualSalary / periodsPerYear;
				} else if (employee.hourlyRate) {
					// For hourly employees, assume standard hours per period
					const hoursPerPeriod = payGroup.payFrequency === 'weekly' ? 40 :
						payGroup.payFrequency === 'bi_weekly' ? 80 :
						payGroup.payFrequency === 'semi_monthly' ? 86.67 : 173.33;
					grossRegular = employee.hourlyRate * hoursPerPeriod;
				}

				// Simple tax calculations (these would be replaced with proper CRA calculations)
				// Using approximate rates for demonstration
				const cppEmployee = grossRegular * 0.0595; // 5.95% employee portion
				const cppEmployer = cppEmployee; // Same for employer
				const eiEmployee = grossRegular * 0.0166; // 1.66% employee portion
				const eiEmployer = eiEmployee * 1.4; // 1.4x for employer
				const federalTax = grossRegular * 0.15; // Simplified federal tax
				const provincialTax = grossRegular * 0.05; // Simplified provincial tax

				const totalDeductions = cppEmployee + eiEmployee + federalTax + provincialTax;
				const netPay = grossRegular - totalDeductions;
				const employerCost = cppEmployer + eiEmployer;

				// Accumulate totals
				totalGross += grossRegular;
				totalCppEmployee += cppEmployee;
				totalCppEmployer += cppEmployer;
				totalEiEmployee += eiEmployee;
				totalEiEmployer += eiEmployer;
				totalFederalTax += federalTax;
				totalProvincialTax += provincialTax;
				totalNetPay += netPay;
				totalEmployerCost += employerCost;

				payrollRecords.push({
					payroll_run_id: runId,
					employee_id: employee.id,
					user_id: userId,
					ledger_id: ledgerId,
					gross_regular: grossRegular,
					gross_overtime: 0,
					holiday_pay: 0,
					holiday_premium_pay: 0,
					vacation_pay_paid: 0,
					other_earnings: 0,
					cpp_employee: cppEmployee,
					cpp_additional: 0,
					ei_employee: eiEmployee,
					federal_tax: federalTax,
					provincial_tax: provincialTax,
					rrsp: 0,
					union_dues: 0,
					garnishments: 0,
					other_deductions: 0,
					cpp_employer: cppEmployer,
					ei_employer: eiEmployer,
					ytd_gross: grossRegular,
					ytd_cpp: cppEmployee,
					ytd_ei: eiEmployee,
					ytd_federal_tax: federalTax,
					ytd_provincial_tax: provincialTax,
					vacation_accrued: 0,
					vacation_hours_taken: 0
				});
			}
		}

		// Insert all payroll records
		const { error: recordsError } = await supabase
			.from('payroll_records')
			.insert(payrollRecords);

		if (recordsError) {
			console.error('Failed to create payroll records:', recordsError);
			// Try to clean up the run
			await supabase.from('payroll_runs').delete().eq('id', runId);
			return { data: null, error: recordsError.message };
		}

		// Update the payroll_runs with totals
		const { error: updateError } = await supabase
			.from('payroll_runs')
			.update({
				total_gross: totalGross,
				total_cpp_employee: totalCppEmployee,
				total_cpp_employer: totalCppEmployer,
				total_ei_employee: totalEiEmployee,
				total_ei_employer: totalEiEmployer,
				total_federal_tax: totalFederalTax,
				total_provincial_tax: totalProvincialTax,
				total_net_pay: totalNetPay,
				total_employer_cost: totalEmployerCost
			})
			.eq('id', runId);

		if (updateError) {
			console.error('Failed to update payroll run totals:', updateError);
		}

		// Return the full payroll run data
		return getPayrollRunByPayDate(payDate);
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to start payroll run';
		console.error('startPayrollRun error:', message);
		return { data: null, error: message };
	}
}

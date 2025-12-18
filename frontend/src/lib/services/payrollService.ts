/**
 * Payroll Service - Data access layer for payroll operations
 *
 * Hybrid Implementation:
 * - Simple CRUD: Direct Supabase queries
 * - Complex calculations: Backend API calls
 */

import { supabase } from '$lib/api/supabase';
import { api } from '$lib/api/client';
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
			.maybeSingle();

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
 * Compensation type based on whether employee has salary or hourly rate
 */
export type EmployeeCompensationType = 'salaried' | 'hourly';

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
	// Computed compensation type
	compensationType: EmployeeCompensationType;
}

/**
 * Hours input for a single employee when starting payroll run
 */
export interface EmployeeHoursInput {
	employeeId: string;
	regularHours: number;
	overtimeHours?: number;
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

			const employeeList: EmployeeForPayroll[] = (employees ?? []).map((emp) => {
				const hourlyRate = emp.hourly_rate ? Number(emp.hourly_rate) : null;
				const annualSalary = emp.annual_salary ? Number(emp.annual_salary) : null;
				// Employee is hourly if they have hourly_rate and no annual_salary
				const compensationType: EmployeeCompensationType = (hourlyRate !== null && annualSalary === null) ? 'hourly' : 'salaried';
				return {
					id: emp.id,
					firstName: emp.first_name,
					lastName: emp.last_name,
					province: emp.province_of_employment,
					payGroupId: emp.pay_group_id,
					annualSalary,
					hourlyRate,
					compensationType
				};
			});

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
// Backend API Types for Payroll Calculation
// ===========================================

interface EmployeeCalculationRequest {
	employee_id: string;
	province: string;
	pay_frequency: string;
	gross_regular: string;
	gross_overtime?: string;
	holiday_pay?: string;
	holiday_premium_pay?: string;
	vacation_pay?: string;
	other_earnings?: string;
	federal_claim_amount?: string;
	provincial_claim_amount?: string;
	rrsp_per_period?: string;
	union_dues_per_period?: string;
	garnishments?: string;
	other_deductions?: string;
	ytd_gross?: string;
	ytd_pensionable_earnings?: string;
	ytd_insurable_earnings?: string;
	ytd_cpp_base?: string;
	ytd_cpp_additional?: string;
	ytd_ei?: string;
	is_cpp_exempt?: boolean;
	is_ei_exempt?: boolean;
	cpp2_exempt?: boolean;
}

interface BatchCalculationRequest {
	employees: EmployeeCalculationRequest[];
	include_details?: boolean;
}

interface CalculationResult {
	employee_id: string;
	province: string;
	gross_regular: string;
	gross_overtime: string;
	holiday_pay: string;
	holiday_premium_pay: string;
	vacation_pay: string;
	other_earnings: string;
	total_gross: string;
	cpp_base: string;
	cpp_additional: string;
	cpp_total: string;
	ei_employee: string;
	federal_tax: string;
	provincial_tax: string;
	rrsp: string;
	union_dues: string;
	garnishments: string;
	other_deductions: string;
	total_employee_deductions: string;
	cpp_employer: string;
	ei_employer: string;
	total_employer_costs: string;
	net_pay: string;
	new_ytd_gross: string;
	new_ytd_cpp: string;
	new_ytd_ei: string;
}

interface BatchCalculationResponse {
	results: CalculationResult[];
	summary: {
		total_employees: number;
		total_gross: string;
		total_cpp_employee: string;
		total_cpp_employer: string;
		total_ei_employee: string;
		total_ei_employer: string;
		total_federal_tax: string;
		total_provincial_tax: string;
		total_deductions: string;
		total_net_pay: string;
		total_employer_costs: string;
	};
}

// ===========================================
// Start Payroll Run
// ===========================================

/**
 * Start a payroll run for a specific pay date
 * Creates the payroll_runs record and payroll_records for all employees
 * Calls backend API for accurate CRA-compliant tax calculations
 *
 * @param payDate - The pay date in ISO format
 * @param hoursInput - Hours worked for each hourly employee. Required for hourly employees.
 */
export async function startPayrollRun(
	payDate: string,
	hoursInput: EmployeeHoursInput[] = []
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

		// Create a map of hours input by employee ID for quick lookup
		const hoursMap = new Map<string, EmployeeHoursInput>();
		for (const h of hoursInput) {
			hoursMap.set(h.employeeId, h);
		}

		// Track hours used for each employee (to store in payroll_records)
		const employeeHoursUsed = new Map<string, { regularHours: number; overtimeHours: number; hourlyRate: number | null }>();

		// Build calculation requests for all employees
		const calculationRequests: EmployeeCalculationRequest[] = [];

		for (const payGroup of payGroups) {
			// Map pay frequency to backend format
			const payFrequency = payGroup.payFrequency === 'bi_weekly' ? 'bi_weekly' :
				payGroup.payFrequency === 'semi_monthly' ? 'semi_monthly' :
				payGroup.payFrequency === 'monthly' ? 'monthly' : 'weekly';

			for (const employee of payGroup.employees) {
				// Calculate gross pay based on salary or hourly rate
				let grossRegular = 0;
				let grossOvertime = 0;
				let regularHoursUsed = 0;
				let overtimeHoursUsed = 0;

				if (employee.compensationType === 'salaried' && employee.annualSalary) {
					// Salaried employee: calculate from annual salary
					const periodsPerYear = payGroup.payFrequency === 'weekly' ? 52 :
						payGroup.payFrequency === 'bi_weekly' ? 26 :
						payGroup.payFrequency === 'semi_monthly' ? 24 : 12;
					grossRegular = employee.annualSalary / periodsPerYear;
				} else if (employee.compensationType === 'hourly' && employee.hourlyRate) {
					// Hourly employee: use provided hours
					const hoursForEmployee = hoursMap.get(employee.id);
					if (!hoursForEmployee) {
						return {
							data: null,
							error: `Missing hours input for hourly employee: ${employee.firstName} ${employee.lastName}`
						};
					}
					regularHoursUsed = hoursForEmployee.regularHours;
					overtimeHoursUsed = hoursForEmployee.overtimeHours ?? 0;
					grossRegular = employee.hourlyRate * regularHoursUsed;
					grossOvertime = employee.hourlyRate * 1.5 * overtimeHoursUsed; // Standard 1.5x overtime
				}

				// Track hours used
				employeeHoursUsed.set(employee.id, {
					regularHours: regularHoursUsed,
					overtimeHours: overtimeHoursUsed,
					hourlyRate: employee.hourlyRate
				});

				calculationRequests.push({
					employee_id: employee.id,
					province: employee.province,
					pay_frequency: payFrequency,
					gross_regular: grossRegular.toFixed(2),
					gross_overtime: grossOvertime.toFixed(2),
					// Use default BPA values - would be from employee TD1 in production
					federal_claim_amount: '16129.00',
					provincial_claim_amount: getProvincialBpa(employee.province),
					// YTD values would come from previous payroll records
					ytd_gross: '0',
					ytd_cpp_base: '0',
					ytd_cpp_additional: '0',
					ytd_ei: '0',
				});
			}
		}

		// Call backend API for batch calculation
		let calculationResponse: BatchCalculationResponse;
		try {
			calculationResponse = await api.post<BatchCalculationResponse>(
				'/payroll/calculate/batch',
				{
					employees: calculationRequests,
					include_details: false
				} as BatchCalculationRequest
			);
		} catch (apiError) {
			console.error('Backend calculation failed:', apiError);
			return { data: null, error: `Calculation failed: ${apiError instanceof Error ? apiError.message : 'Unknown error'}` };
		}

		// Create the payroll_runs record with calculated totals
		const summary = calculationResponse.summary;
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
				total_gross: parseFloat(summary.total_gross),
				total_cpp_employee: parseFloat(summary.total_cpp_employee),
				total_cpp_employer: parseFloat(summary.total_cpp_employer),
				total_ei_employee: parseFloat(summary.total_ei_employee),
				total_ei_employer: parseFloat(summary.total_ei_employer),
				total_federal_tax: parseFloat(summary.total_federal_tax),
				total_provincial_tax: parseFloat(summary.total_provincial_tax),
				total_net_pay: parseFloat(summary.total_net_pay),
				total_employer_cost: parseFloat(summary.total_employer_costs)
			})
			.select()
			.single();

		if (runError) {
			console.error('Failed to create payroll run:', runError);
			return { data: null, error: runError.message };
		}

		const runId = runData.id;

		// Create payroll records from calculation results
		const payrollRecords = calculationResponse.results.map((result) => {
			// Get hours data for this employee
			const hoursData = employeeHoursUsed.get(result.employee_id);
			return {
				payroll_run_id: runId,
				employee_id: result.employee_id,
				user_id: userId,
				ledger_id: ledgerId,
				// Hours worked (for hourly employees)
				regular_hours_worked: hoursData?.regularHours || null,
				overtime_hours_worked: hoursData?.overtimeHours || 0,
				hourly_rate_snapshot: hoursData?.hourlyRate || null,
				// Earnings
				gross_regular: parseFloat(result.gross_regular),
				gross_overtime: parseFloat(result.gross_overtime),
				holiday_pay: parseFloat(result.holiday_pay),
				holiday_premium_pay: parseFloat(result.holiday_premium_pay),
				vacation_pay_paid: parseFloat(result.vacation_pay),
				other_earnings: parseFloat(result.other_earnings),
				cpp_employee: parseFloat(result.cpp_base),
				cpp_additional: parseFloat(result.cpp_additional),
				ei_employee: parseFloat(result.ei_employee),
				federal_tax: parseFloat(result.federal_tax),
				provincial_tax: parseFloat(result.provincial_tax),
				rrsp: parseFloat(result.rrsp),
				union_dues: parseFloat(result.union_dues),
				garnishments: parseFloat(result.garnishments),
				other_deductions: parseFloat(result.other_deductions),
				cpp_employer: parseFloat(result.cpp_employer),
				ei_employer: parseFloat(result.ei_employer),
				ytd_gross: parseFloat(result.new_ytd_gross),
				ytd_cpp: parseFloat(result.new_ytd_cpp),
				ytd_ei: parseFloat(result.new_ytd_ei),
				ytd_federal_tax: 0, // Would be updated from result
				ytd_provincial_tax: 0, // Would be updated from result
				vacation_accrued: 0,
				vacation_hours_taken: 0
			};
		});

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

		// Return the full payroll run data
		return getPayrollRunByPayDate(payDate);
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to start payroll run';
		console.error('startPayrollRun error:', message);
		return { data: null, error: message };
	}
}

/**
 * Get provincial Basic Personal Amount based on province code
 */
function getProvincialBpa(province: string): string {
	const bpaMap: Record<string, string> = {
		AB: '22323.00',
		BC: '12932.00',
		MB: '15591.00',
		NB: '13396.00',
		NL: '11067.00',
		NS: '11744.00',
		NT: '17842.00',
		NU: '19274.00',
		ON: '12747.00',
		PE: '15050.00',
		SK: '19491.00',
		YT: '16129.00',
	};
	return bpaMap[province] ?? '12747.00'; // Default to ON if unknown
}

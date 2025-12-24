/**
 * Pay Groups Service for Payroll
 * Functions for getting pay groups with employees for payroll operations
 */

import { supabase } from '$lib/api/supabase';
import type {
	UpcomingPayDate,
	PayrollRunStatus
} from '$lib/types/payroll';
import {
	DEFAULT_EARNINGS_CONFIG,
	DEFAULT_TAXABLE_BENEFITS_CONFIG,
	DEFAULT_DEDUCTIONS_CONFIG,
	DEFAULT_OVERTIME_POLICY,
	DEFAULT_GROUP_BENEFITS,
	DEFAULT_STATUTORY_DEFAULTS
} from '$lib/types/pay-group';
import { getCurrentUserId, getCurrentLedgerId } from './helpers';
import type {
	PayrollServiceResult,
	PayGroupWithEmployees,
	BeforeRunData,
	EmployeeForPayroll,
	EmployeeCompensationType
} from './types';

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
				employees: employeeList,
				// Pay Group configuration for UI rendering
				leaveEnabled: pg.leave_enabled ?? true,
				overtimePolicy: pg.overtime_policy ?? DEFAULT_OVERTIME_POLICY,
				groupBenefits: pg.group_benefits ?? DEFAULT_GROUP_BENEFITS,
				statutoryDefaults: pg.statutory_defaults ?? DEFAULT_STATUTORY_DEFAULTS,
				// Structured configurations
				earningsConfig: pg.earnings_config ?? DEFAULT_EARNINGS_CONFIG,
				taxableBenefitsConfig: pg.taxable_benefits_config ?? DEFAULT_TAXABLE_BENEFITS_CONFIG,
				deductionsConfig: pg.deductions_config ?? DEFAULT_DEDUCTIONS_CONFIG
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

/**
 * Pay Groups Service for Payroll
 * Functions for getting pay groups with employees for payroll operations
 */

import { supabase } from '$lib/api/supabase';
import type { UpcomingPeriod, PayrollRunStatus } from '$lib/types/payroll';
import {
	DEFAULT_EARNINGS_CONFIG,
	DEFAULT_TAXABLE_BENEFITS_CONFIG,
	DEFAULT_DEDUCTIONS_CONFIG,
	DEFAULT_OVERTIME_POLICY,
	DEFAULT_GROUP_BENEFITS,
	calculatePayDate
} from '$lib/types/pay-group';
import { getCurrentUserId, getCurrentCompanyId } from './helpers';
import type {
	PayrollServiceResult,
	PayGroupWithEmployees,
	BeforeRunData,
	EmployeeForPayroll,
	EmployeeCompensationType
} from './types';

// ===========================================
// Pay Groups for Specific Period End
// ===========================================

/**
 * Get pay groups for a specific period end date
 * Used on the Payroll Run page to show pay groups even when no payroll run exists
 *
 * @param periodEnd Period end date (ISO string) - the authoritative grouping key
 */
export async function getPayGroupsForPeriodEnd(
	periodEnd: string
): Promise<PayrollServiceResult<UpcomingPeriod | null>> {
	try {
		getCurrentUserId();

		// Query pay groups with this next_period_end
		const { data: payGroups, error: pgError } = await supabase
			.from('v_pay_group_summary')
			.select('*')
			.eq('next_period_end', periodEnd);

		if (pgError) {
			console.error('Failed to query pay groups:', pgError);
			return { data: null, error: pgError.message };
		}

		if (!payGroups || payGroups.length === 0) {
			return { data: null, error: null };
		}

		// Calculate pay date from period end (SK: +6 days)
		const payDate = calculatePayDate(periodEnd, 'SK');

		// Period start is calculated based on frequency
		// For bi-weekly: period_start = period_end - 13 days
		const periodEndObj = new Date(periodEnd);
		const periodStart = new Date(periodEndObj);
		periodStart.setDate(periodStart.getDate() - 13);

		const result: UpcomingPeriod = {
			periodEnd,
			payDate,
			payGroups: payGroups.map((pg) => ({
				id: pg.id,
				name: pg.name,
				payFrequency: pg.pay_frequency,
				employmentType: pg.employment_type,
				employeeCount: pg.employee_count ?? 0,
				estimatedGross: 0,
				periodStart: periodStart.toISOString().split('T')[0],
				periodEnd,
				province: pg.province ?? 'SK'
			})),
			totalEmployees: payGroups.reduce((sum, pg) => sum + (pg.employee_count ?? 0), 0),
			totalEstimatedGross: 0
		};

		// Check for existing payroll run by period_end
		const { data: runs } = await supabase
			.from('payroll_runs')
			.select('id, status')
			.eq('period_end', periodEnd)
			.maybeSingle();

		if (runs) {
			result.runId = runs.id;
			result.runStatus = runs.status as PayrollRunStatus;
		}

		return { data: result, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to get pay groups for period';
		console.error('getPayGroupsForPeriodEnd error:', message);
		return { data: null, error: message };
	}
}

/**
 * @deprecated Use getPayGroupsForPeriodEnd instead
 */
export const getPayGroupsForPayDate = getPayGroupsForPeriodEnd;

// ===========================================
// Pay Groups with Employees (Before Run State)
// ===========================================

/**
 * Get pay groups with employees for a specific period end (before payroll run is created)
 * This is used to display the full UI with employee list before clicking "Start Payroll Run"
 *
 * @param periodEnd Period end date (ISO string) - the authoritative grouping key
 */
export async function getPayGroupsWithEmployeesForPeriodEnd(
	periodEnd: string
): Promise<PayrollServiceResult<BeforeRunData>> {
	try {
		const userId = getCurrentUserId();
		const companyId = getCurrentCompanyId();

		// Query pay groups with this next_period_end
		const { data: payGroups, error: pgError } = await supabase
			.from('v_pay_group_summary')
			.select('*')
			.eq('next_period_end', periodEnd);

		if (pgError) {
			console.error('Failed to query pay groups:', pgError);
			return { data: null, error: pgError.message };
		}

		if (!payGroups || payGroups.length === 0) {
			return { data: null, error: null };
		}

		// Calculate pay date from period end (SK: +6 days)
		const payDate = calculatePayDate(periodEnd, 'SK');

		// Period start is calculated based on frequency
		// For bi-weekly: period_start = period_end - 13 days
		const periodEndObj = new Date(periodEnd);
		const periodStart = new Date(periodEndObj);
		periodStart.setDate(periodStart.getDate() - 13);

		const periodStartStr = periodStart.toISOString().split('T')[0];
		const periodEndStr = periodEnd;

		// Get employees for each pay group
		const payGroupsWithEmployees: PayGroupWithEmployees[] = [];
		let totalEmployees = 0;

		for (const pg of payGroups) {
			const { data: employees, error: empError } = await supabase
				.from('employees')
				.select(
					'id, first_name, last_name, province_of_employment, pay_group_id, annual_salary, hourly_rate'
				)
				.eq('user_id', userId)
				.eq('company_id', companyId)
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
				const compensationType: EmployeeCompensationType =
					hourlyRate !== null && annualSalary === null ? 'hourly' : 'salaried';
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
				// Structured configurations
				earningsConfig: pg.earnings_config ?? DEFAULT_EARNINGS_CONFIG,
				taxableBenefitsConfig: pg.taxable_benefits_config ?? DEFAULT_TAXABLE_BENEFITS_CONFIG,
				deductionsConfig: pg.deductions_config ?? DEFAULT_DEDUCTIONS_CONFIG
			});

			totalEmployees += employeeList.length;
		}

		// Get unique provinces from all employees
		const provinces = new Set<string>();
		for (const pg of payGroupsWithEmployees) {
			for (const emp of pg.employees) {
				if (emp.province) {
					provinces.add(emp.province);
				}
			}
		}

		// Query holidays for the pay period from Supabase
		let holidays: { date: string; name: string; province: string }[] = [];
		if (provinces.size > 0) {
			const { data: holidayData, error: holidayError } = await supabase
				.from('statutory_holidays')
				.select('holiday_date, name, province')
				.gte('holiday_date', periodStartStr)
				.lte('holiday_date', periodEndStr)
				.in('province', Array.from(provinces))
				.eq('is_statutory', true);

			if (holidayError) {
				console.error('Failed to query holidays:', holidayError);
			} else if (holidayData) {
				holidays = holidayData.map((h) => ({
					date: h.holiday_date,
					name: h.name,
					province: h.province
				}));
			}
		}

		return {
			data: {
				periodEnd,
				payDate,
				payGroups: payGroupsWithEmployees,
				totalEmployees,
				holidays
			},
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to get pay groups with employees';
		console.error('getPayGroupsWithEmployeesForPeriodEnd error:', message);
		return { data: null, error: message };
	}
}

/**
 * @deprecated Use getPayGroupsWithEmployeesForPeriodEnd instead
 */
export const getPayGroupsWithEmployeesForPayDate = getPayGroupsWithEmployeesForPeriodEnd;

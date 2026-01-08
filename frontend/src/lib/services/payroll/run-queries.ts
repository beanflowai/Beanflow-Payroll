/**
 * Payroll Run Query Functions
 * Read operations for payroll runs
 */

import { supabase } from '$lib/api/supabase';
import type {
	PayrollRunWithGroups,
	PayrollRunPayGroup,
	PayrollRunStatus,
	DbPayrollRun,
	DbPayrollRecordWithEmployee,
	Holiday
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
import { getCurrentUserId, getCurrentCompanyId } from './helpers';
import type { PayrollServiceResult, PayrollRunListOptions, PayrollRunListResult } from './types';

// ===========================================
// Helper: Query Holidays for Period
// ===========================================

/**
 * Query statutory holidays for a pay period from the database
 * @param periodStart Start date of the pay period (ISO string)
 * @param periodEnd End date of the pay period (ISO string)
 * @param provinces Array of province codes to filter by
 * @returns Array of holidays in the period
 */
export async function queryHolidaysForPeriod(
	periodStart: string,
	periodEnd: string,
	provinces: string[]
): Promise<Holiday[]> {
	if (provinces.length === 0) {
		return [];
	}

	try {
		const { data: holidayData, error: holidayError } = await supabase
			.from('statutory_holidays')
			.select('holiday_date, name, province')
			.gte('holiday_date', periodStart)
			.lte('holiday_date', periodEnd)
			.in('province', provinces)
			.eq('is_statutory', true);

		if (holidayError) {
			console.error('Failed to query holidays:', holidayError);
			return [];
		}

		return (holidayData ?? []).map((h) => ({
			date: h.holiday_date,
			name: h.name,
			province: h.province
		}));
	} catch (err) {
		console.error('Error querying holidays:', err);
		return [];
	}
}

// ===========================================
// Helper: Build PayrollRunWithGroups from DB data
// ===========================================

/**
 * Build PayrollRunWithGroups from database records
 * Shared logic for getPayrollRunByPayDate and getPayrollRunByPeriodEnd
 */
async function buildPayrollRunWithGroups(
	runData: DbPayrollRun,
	recordsData: DbPayrollRecordWithEmployee[]
): Promise<PayrollRunWithGroups> {
	// Group records by pay group (use snapshot fields for historical accuracy)
	const payGroupMap = new Map<string, PayrollRunPayGroup>();

	for (const record of recordsData) {
		const payGroup = record.employees.pay_groups;
		// Use snapshot fields for grouping to preserve historical pay group assignment
		// Fallback to joined data for records created before snapshots were added
		const payGroupId = record.pay_group_id_snapshot ?? payGroup?.id ?? 'unknown';
		const payGroupName = record.pay_group_name_snapshot ?? payGroup?.name ?? 'Unknown Pay Group';
		// Get province from pay group (employees in same pay group must have same province)
		const payGroupProvince =
			(payGroup as { province?: string })?.province ??
			record.province_snapshot ??
			record.employees.province_of_employment ??
			'SK';

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
				payFrequency: (payGroup?.pay_frequency ?? 'bi_weekly') as
					| 'weekly'
					| 'bi_weekly'
					| 'semi_monthly'
					| 'monthly',
				employmentType: (payGroup?.employment_type ?? 'full_time') as 'full_time' | 'part_time',
				province: payGroupProvince,
				periodStart: runData.period_start,
				periodEnd: runData.period_end,
				totalEmployees: 1,
				totalGross: uiRecord.totalGross,
				totalDeductions: uiRecord.totalDeductions,
				totalNetPay: uiRecord.netPay,
				totalEmployerCost: uiRecord.totalEmployerCost,
				records: [uiRecord],
				earningsConfig:
					(payGroup?.earnings_config as EarningsConfig | undefined) ?? DEFAULT_EARNINGS_CONFIG,
				taxableBenefitsConfig:
					(payGroup?.taxable_benefits_config as TaxableBenefitsConfig | undefined) ??
					DEFAULT_TAXABLE_BENEFITS_CONFIG,
				deductionsConfig:
					(payGroup?.deductions_config as DeductionsConfig | undefined) ??
					DEFAULT_DEDUCTIONS_CONFIG,
				groupBenefits:
					(payGroup?.group_benefits as GroupBenefits | undefined) ?? DEFAULT_GROUP_BENEFITS
			});
		}
	}

	const totalGross = Number(runData.total_gross);
	const totalNetPay = Number(runData.total_net_pay);
	const totalCppEmployee = Number(runData.total_cpp_employee);
	const totalCppEmployer = Number(runData.total_cpp_employer);
	const totalEiEmployee = Number(runData.total_ei_employee);
	const totalEiEmployer = Number(runData.total_ei_employer);
	const totalFederalTax = Number(runData.total_federal_tax);
	const totalProvincialTax = Number(runData.total_provincial_tax);
	const totalEmployerCost = Number(runData.total_employer_cost);

	// Collect unique provinces from pay groups
	const provinces = new Set<string>();
	for (const pg of payGroupMap.values()) {
		if (pg.province) {
			provinces.add(pg.province);
		}
	}

	// Query holidays for this pay period (all provinces)
	const allHolidays = await queryHolidaysForPeriod(
		runData.period_start,
		runData.period_end,
		Array.from(provinces)
	);

	// Attach holidays to each pay group based on province
	const payGroups = Array.from(payGroupMap.values()).map((pg) => ({
		...pg,
		holidays: allHolidays.filter((h) => h.province === pg.province)
	}));

	// Also keep all holidays at run level for backward compatibility
	const holidays = allHolidays;

	return {
		id: runData.id,
		periodEnd: runData.period_end,
		payDate: runData.pay_date,
		status: runData.status,
		payGroups,
		totalEmployees: runData.total_employees,
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
		totalRemittance:
			totalCppEmployee +
			totalCppEmployer +
			totalEiEmployee +
			totalEiEmployer +
			totalFederalTax +
			totalProvincialTax,
		holidays
	};
}

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
		const companyId = getCurrentCompanyId();

		// Query payroll run for this date (filter by user_id and company_id)
		// Use order + limit(1) instead of maybeSingle() to safely handle
		// edge cases where multiple runs exist for the same pay_date
		const { data: runsData, error: runError } = await supabase
			.from('payroll_runs')
			.select('*')
			.eq('user_id', userId)
			.eq('company_id', companyId)
			.eq('pay_date', payDate)
			.order('created_at', { ascending: false })
			.limit(1);

		if (runError) {
			console.error('Failed to get payroll run:', runError);
			return { data: null, error: runError.message };
		}

		const runData = runsData?.[0];
		if (!runData) {
			return { data: null, error: null };
		}

		// Get payroll records with employee and pay group info
		const { data: recordsData, error: recordsError } = await supabase
			.from('payroll_records')
			.select(
				`
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
					vacation_balance,
					sick_balance,
					pay_groups (
						id,
						name,
						pay_frequency,
						employment_type,
						province,
						earnings_config,
						taxable_benefits_config,
						deductions_config,
						group_benefits
					)
				)
			`
			)
			.eq('payroll_run_id', runData.id);

		if (recordsError) {
			console.error('Failed to get payroll records:', recordsError);
			return { data: null, error: recordsError.message };
		}

		const result = await buildPayrollRunWithGroups(
			runData as DbPayrollRun,
			(recordsData as DbPayrollRecordWithEmployee[]) ?? []
		);

		return { data: result, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to get payroll run';
		console.error('getPayrollRunByPayDate error:', message);
		return { data: null, error: message };
	}
}

/**
 * Get a payroll run by period end date
 * Uses period_end as the primary query key (new approach)
 */
export async function getPayrollRunByPeriodEnd(
	periodEnd: string
): Promise<PayrollServiceResult<PayrollRunWithGroups>> {
	try {
		const userId = getCurrentUserId();
		const companyId = getCurrentCompanyId();

		// Query payroll run for this period end (filter by user_id and company_id)
		const { data: runsData, error: runError } = await supabase
			.from('payroll_runs')
			.select('*')
			.eq('user_id', userId)
			.eq('company_id', companyId)
			.eq('period_end', periodEnd)
			.order('created_at', { ascending: false })
			.limit(1);

		if (runError) {
			console.error('Failed to get payroll run:', runError);
			return { data: null, error: runError.message };
		}

		const runData = runsData?.[0];
		if (!runData) {
			return { data: null, error: null };
		}

		// Get payroll records with employee and pay group info
		const { data: recordsData, error: recordsError } = await supabase
			.from('payroll_records')
			.select(
				`
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
					vacation_balance,
					sick_balance,
					pay_groups (
						id,
						name,
						pay_frequency,
						employment_type,
						province,
						earnings_config,
						taxable_benefits_config,
						deductions_config,
						group_benefits
					)
				)
			`
			)
			.eq('payroll_run_id', runData.id);

		if (recordsError) {
			console.error('Failed to get payroll records:', recordsError);
			return { data: null, error: recordsError.message };
		}

		const result = await buildPayrollRunWithGroups(
			runData as DbPayrollRun,
			(recordsData as DbPayrollRecordWithEmployee[]) ?? []
		);

		return { data: result, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to get payroll run';
		console.error('getPayrollRunByPeriodEnd error:', message);
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
		const companyId = getCurrentCompanyId();

		// Query payroll run by ID (filter by user_id and company_id)
		const { data: runData, error: runError } = await supabase
			.from('payroll_runs')
			.select('*')
			.eq('user_id', userId)
			.eq('company_id', companyId)
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
// List Payroll Runs
// ===========================================

/**
 * Extended options for listing payroll runs
 */
export interface PayrollRunListOptionsExt extends PayrollRunListOptions {
	excludeStatuses?: string[];
}

/**
 * List payroll runs with pagination via Supabase direct query
 */
export async function listPayrollRuns(
	options: PayrollRunListOptionsExt = {}
): Promise<PayrollRunListResult> {
	const { status, excludeStatuses, limit = 20, offset = 0 } = options;

	try {
		const userId = getCurrentUserId();
		const companyId = getCurrentCompanyId();

		// Direct Supabase query (filter by user_id and company_id)
		let query = supabase
			.from('payroll_runs')
			.select('*', { count: 'exact' })
			.eq('user_id', userId)
			.eq('company_id', companyId);

		if (status) {
			query = query.eq('status', status);
		}

		if (excludeStatuses && excludeStatuses.length > 0) {
			query = query.not('status', 'in', `(${excludeStatuses.join(',')})`);
		}

		const { data, error, count } = await query
			.order('pay_date', { ascending: false })
			.range(offset, offset + limit - 1);

		if (error) throw error;

		// Convert snake_case DB fields to camelCase PayrollRunWithGroups
		const runs: PayrollRunWithGroups[] = (data || []).map((run) => {
			const totalGross = run.total_gross ?? 0;
			const totalNetPay = run.total_net_pay ?? 0;
			const totalEmployerCost = run.total_employer_cost ?? 0;

			return {
				id: run.id,
				periodEnd: run.period_end,
				payDate: run.pay_date,
				status: run.status as PayrollRunStatus,
				payGroups: [],
				totalEmployees: run.total_employees ?? 0,
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

		return { data: runs, count: count ?? 0, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to list payroll runs';
		return { data: [], count: 0, error: message };
	}
}

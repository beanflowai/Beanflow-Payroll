/**
 * Payroll Dashboard Service
 * Functions for payroll dashboard, page status, and upcoming pay dates
 */

import { supabase } from '$lib/api/supabase';
import type {
	UpcomingPeriod,
	PayrollRunStatus,
	PayrollPageStatus,
	PayrollRunWithGroups
} from '$lib/types/payroll';
import { calculatePayDate } from '$lib/types/pay-group';
import { getCurrentUserId, getCurrentCompanyId } from './helpers';
import type { PayrollServiceResult, PayrollDashboardStats } from './types';
import { listPayrollRuns, type PayrollRunListOptionsExt } from './run-queries';

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
		const companyId = getCurrentCompanyId();

		// Query pay groups count via the summary view (filter by company_id)
		const { data: payGroups, error: pgError } = await supabase
			.from('v_pay_group_summary')
			.select('id, employee_count')
			.eq('company_id', companyId)
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
// Upcoming Pay Periods
// ===========================================

/**
 * Get upcoming pay periods for the dashboard
 * Queries pay_groups to get next_period_end, groups by period_end
 * pay_date is auto-calculated as period_end + 6 days (SK)
 */
export async function getUpcomingPeriods(): Promise<PayrollServiceResult<UpcomingPeriod[]>> {
	try {
		getCurrentUserId();
		const companyId = getCurrentCompanyId();

		// Query pay groups with employee counts (ordered by next_period_end, filter by company_id)
		const { data: payGroups, error: pgError } = await supabase
			.from('v_pay_group_summary')
			.select('*')
			.eq('company_id', companyId)
			.order('next_period_end');

		if (pgError) {
			console.error('Failed to query pay groups:', pgError);
			return { data: null, error: pgError.message };
		}

		if (!payGroups || payGroups.length === 0) {
			return { data: [], error: null };
		}

		// Group pay groups by period_end (the authoritative date)
		const periodMap = new Map<string, UpcomingPeriod>();

		for (const pg of payGroups) {
			const periodEnd = pg.next_period_end;
			if (!periodEnd) continue;

			// Calculate pay_date from period_end (SK: +6 days)
			const payDate = calculatePayDate(periodEnd, 'SK');

			// Calculate period start (simplified: 14 day period for bi-weekly)
			const periodEndObj = new Date(periodEnd);
			const periodStart = new Date(periodEndObj);
			periodStart.setDate(periodStart.getDate() - 13); // 14 day period

			const existing = periodMap.get(periodEnd);
			const payGroupSummary = {
				id: pg.id,
				name: pg.name,
				payFrequency: pg.pay_frequency,
				employmentType: pg.employment_type,
				employeeCount: pg.employee_count ?? 0,
				estimatedGross: 0, // Would need salary data to estimate
				periodStart: periodStart.toISOString().split('T')[0],
				periodEnd: periodEnd,
				province: pg.province ?? 'SK'
			};

			if (existing) {
				existing.payGroups.push(payGroupSummary);
				existing.totalEmployees += pg.employee_count ?? 0;
			} else {
				periodMap.set(periodEnd, {
					periodEnd,
					payDate,
					payGroups: [payGroupSummary],
					totalEmployees: pg.employee_count ?? 0,
					totalEstimatedGross: 0
				});
			}
		}

		// Check for existing payroll runs for these period ends (filter by company_id)
		const periodEnds = Array.from(periodMap.keys());
		if (periodEnds.length > 0) {
			const { data: runs } = await supabase
				.from('payroll_runs')
				.select('id, period_end, status')
				.eq('company_id', companyId)
				.in('period_end', periodEnds);

			if (runs) {
				for (const run of runs) {
					const upcomingPeriod = periodMap.get(run.period_end);
					if (upcomingPeriod) {
						upcomingPeriod.runId = run.id;
						upcomingPeriod.runStatus = run.status as PayrollRunStatus;
					}
				}
			}
		}

		// Sort by period_end
		const result = Array.from(periodMap.values()).sort(
			(a, b) => new Date(a.periodEnd).getTime() - new Date(b.periodEnd).getTime()
		);

		return { data: result, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to get upcoming periods';
		console.error('getUpcomingPeriods error:', message);
		return { data: null, error: message };
	}
}

/**
 * @deprecated Use getUpcomingPeriods instead
 */
export const getUpcomingPayDates = getUpcomingPeriods;

// ===========================================
// Dashboard Statistics
// ===========================================

export async function getPayrollDashboardStats(): Promise<
	PayrollServiceResult<PayrollDashboardStats>
> {
	try {
		const { data: upcomingPeriods, error } = await getUpcomingPeriods();

		if (error || !upcomingPeriods) {
			return { data: null, error: error ?? 'Failed to get upcoming periods' };
		}

		const nextPeriod = upcomingPeriods.length > 0 ? upcomingPeriods[0] : null;

		const stats: PayrollDashboardStats = {
			upcomingCount: upcomingPeriods.length,
			nextPayDate: nextPeriod?.periodEnd ?? null, // Now returns periodEnd
			nextPayDateEmployees: nextPeriod?.totalEmployees ?? 0,
			nextPayDateEstimatedGross: nextPeriod?.totalEstimatedGross ?? 0
		};

		return { data: stats, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to get dashboard stats';
		return { data: null, error: message };
	}
}

// ===========================================
// Recent Completed Runs
// ===========================================

/**
 * Get recent completed payroll runs for dashboard display.
 * Returns runs with status 'approved' or 'paid', sorted by pay_date descending.
 */
export async function getRecentCompletedRuns(
	limit: number = 5
): Promise<PayrollServiceResult<PayrollRunWithGroups[]>> {
	try {
		// Use listPayrollRuns with excludeStatuses to get only completed runs
		// Completed = all runs except draft, pending_approval, cancelled
		const result = await listPayrollRuns({
			excludeStatuses: ['draft', 'pending_approval', 'cancelled'],
			limit,
			offset: 0
		} as PayrollRunListOptionsExt);

		if (result.error) {
			return { data: null, error: result.error };
		}

		return { data: result.data, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to get recent completed runs';
		return { data: null, error: message };
	}
}

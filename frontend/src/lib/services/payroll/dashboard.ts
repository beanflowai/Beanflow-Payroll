/**
 * Payroll Dashboard Service
 * Functions for payroll dashboard, page status, and upcoming pay dates
 */

import { supabase } from '$lib/api/supabase';
import type {
	UpcomingPayDate,
	PayrollRunStatus,
	PayrollPageStatus,
	PayrollRunWithGroups
} from '$lib/types/payroll';
import { getCurrentUserId } from './helpers';
import type { PayrollServiceResult, PayrollDashboardStats } from './types';
import { listPayrollRuns, type PayrollRunListOptionsExt } from './payroll-runs';

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
// Dashboard Statistics
// ===========================================

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

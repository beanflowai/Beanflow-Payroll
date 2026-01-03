/**
 * Payroll Calculation Service
 * Functions for starting payroll runs with backend API calculations
 */

import { supabase } from '$lib/api/supabase';
import { api } from '$lib/api/client';
import type { PayrollRunWithGroups } from '$lib/types/payroll';
import { getCurrentUserId, getCurrentCompanyId, getProvincialBpa } from './helpers';
import { getPayGroupsWithEmployeesForPayDate } from './pay-groups';
import { getPayrollRunByPayDate } from './run-queries';
import type {
	PayrollServiceResult,
	EmployeeHoursInput,
	EmployeeCalculationRequest,
	BatchCalculationRequest,
	BatchCalculationResponse
} from './types';

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
		const companyId = getCurrentCompanyId();

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

		// Track snapshot data for each employee (for historical accuracy)
		const employeeSnapshotData = new Map<string, {
			name: string;
			province: string;
			annualSalary: number | null;
			payGroupId: string;
			payGroupName: string;
		}>();

		// Build calculation requests for all employees
		const calculationRequests: EmployeeCalculationRequest[] = [];

		for (const payGroup of payGroups) {
			// Map pay frequency to backend format
			const payFrequency = payGroup.payFrequency === 'bi_weekly' ? 'bi_weekly' :
				payGroup.payFrequency === 'semi_monthly' ? 'semi_monthly' :
				payGroup.payFrequency === 'monthly' ? 'monthly' : 'weekly';

			for (const employee of payGroup.employees) {
				// Store snapshot data for this employee
				employeeSnapshotData.set(employee.id, {
					name: `${employee.firstName} ${employee.lastName}`,
					province: employee.province,
					annualSalary: employee.annualSalary,
					payGroupId: payGroup.id,
					payGroupName: payGroup.name
				});

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
				company_id: companyId,
				period_start: periodStart,
				period_end: periodEnd,
				pay_date: payDate,
				status: 'draft',
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
			// Get snapshot data for this employee
			const snapshotData = employeeSnapshotData.get(result.employee_id);
			return {
				payroll_run_id: runId,
				employee_id: result.employee_id,
				user_id: userId,
				company_id: companyId,
				// Employee snapshots (captured at payroll creation time)
				employee_name_snapshot: snapshotData?.name ?? null,
				province_snapshot: snapshotData?.province ?? null,
				annual_salary_snapshot: snapshotData?.annualSalary ?? null,
				pay_group_id_snapshot: snapshotData?.payGroupId ?? null,
				pay_group_name_snapshot: snapshotData?.payGroupName ?? null,
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
				vacation_hours_taken: 0,
				// Draft flow support: store original input data for recalculation
				input_data: {
					regularHours: hoursData?.regularHours || 0,
					overtimeHours: hoursData?.overtimeHours || 0,
					leaveEntries: [],
					holidayWorkEntries: [],
					adjustments: [],
					overrides: {}
				},
				is_modified: false
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

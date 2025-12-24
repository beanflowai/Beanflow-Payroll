/**
 * Payroll types for UI
 */

import type {
	EarningsConfig,
	TaxableBenefitsConfig,
	DeductionsConfig
} from './pay-group';

// Leave types
export type LeaveType = 'vacation' | 'sick';

export const LEAVE_TYPE_LABELS: Record<LeaveType, { short: string; full: string; icon: string }> = {
	vacation: { short: 'VAC', full: 'Vacation', icon: '🏖️' },
	sick: { short: 'SIC', full: 'Sick', icon: '🏥' }
};

export interface LeaveEntry {
	id: string;
	employeeId: string;
	employeeName: string;
	leaveType: LeaveType;
	hours: number;
	payRate: number; // hourly rate at time of leave
	leavePay: number; // calculated: hours × payRate
}

// Overtime entry for tracking overtime hours worked
export interface OvertimeEntry {
	id: string;
	employeeId: string;
	employeeName: string;
	hours: number; // overtime hours worked
	hourlyRate: number; // regular hourly rate
	multiplier: number; // overtime multiplier (default 1.5)
	overtimePay: number; // calculated: hours × hourlyRate × multiplier
}

// Vacation payout types (for accrual method employees only)
export type VacationPayoutReason = 'scheduled' | 'cashout_request' | 'termination';

export const VACATION_PAYOUT_LABELS: Record<
	VacationPayoutReason,
	{ label: string; icon: string }
> = {
	scheduled: { label: 'Scheduled Payout', icon: '📅' },
	cashout_request: { label: 'Cashout Request', icon: '💵' },
	termination: { label: 'Termination', icon: '🚪' }
};

export interface VacationPayoutEntry {
	id: string;
	employeeId: string;
	employeeName: string;
	payoutReason: VacationPayoutReason;
	hours: number;
	payRate: number; // hourly rate at time of payout
	payoutAmount: number; // calculated: hours × payRate
	notes?: string;
}

export type PayrollRunStatus =
	| 'draft'
	| 'calculating'
	| 'pending_approval'
	| 'approved'
	| 'paid'
	| 'cancelled';

// Paystub send status for individual employee
export type PaystubStatus = 'pending' | 'sending' | 'sent' | 'failed';

export const PAYSTUB_STATUS_LABELS: Record<PaystubStatus, string> = {
	pending: 'Not Generated',
	sending: 'Sending...',
	sent: 'Sent',
	failed: 'Failed'
};

export const PAYROLL_STATUS_LABELS: Record<PayrollRunStatus, string> = {
	draft: 'Draft',
	calculating: 'Calculating',
	pending_approval: 'Pending Approval',
	approved: 'Approved',
	paid: 'Paid',
	cancelled: 'Cancelled'
};

export const PAYROLL_STATUS_COLORS: Record<PayrollRunStatus, string> = {
	draft: 'gray',
	calculating: 'blue',
	pending_approval: 'yellow',
	approved: 'blue',
	paid: 'green',
	cancelled: 'red'
};

// Payroll Run header
export interface PayrollRun {
	id: string;
	periodStart: string;
	periodEnd: string;
	payDate: string;
	status: PayrollRunStatus;
	totalEmployees: number;
	totalGross: number;
	totalCppEmployee: number;
	totalCppEmployer: number;
	totalEiEmployee: number;
	totalEiEmployer: number;
	totalFederalTax: number;
	totalProvincialTax: number;
	totalDeductions: number;
	totalNetPay: number;
	totalEmployerCost: number;
	holidays?: Holiday[];
}

// Compensation type for determining how gross pay is calculated
export type CompensationType = 'salaried' | 'hourly';

// Individual employee payroll record
export interface PayrollRecord {
	id: string;
	employeeId: string;
	employeeName: string;
	employeeProvince: string;

	// Compensation info (for display and calculation)
	compensationType: CompensationType;
	annualSalary?: number;  // For salaried employees
	hourlyRate?: number;    // For hourly employees

	// Hours worked (for hourly employees)
	regularHoursWorked?: number;   // NULL for salaried employees
	overtimeHoursWorked?: number;
	hourlyRateSnapshot?: number;   // Rate at time of payroll

	// Earnings
	grossRegular: number;
	grossOvertime: number;
	holidayPay: number;
	holidayPremiumPay: number;
	vacationPayPaid: number;
	otherEarnings: number;
	totalGross: number;

	// Deductions
	cppEmployee: number;
	cppAdditional: number; // CPP2
	eiEmployee: number;
	federalTax: number;
	provincialTax: number;
	rrsp: number;
	unionDues: number;
	garnishments: number;
	otherDeductions: number;
	totalDeductions: number;

	// Net
	netPay: number;

	// Employer costs
	cppEmployer: number;
	eiEmployer: number;
	totalEmployerCost: number;

	// YTD (Year-to-Date)
	ytdGross: number;
	ytdCpp: number;
	ytdEi: number;
	ytdFederalTax: number;
	ytdProvincialTax: number;
	ytdNetPay: number;

	// Holiday work hours (for this period)
	holidayWorkHours?: HolidayWorkEntry[];

	// Overtime tracking
	overtimeEntries?: OvertimeEntry[];

	// Leave tracking
	leaveEntries?: LeaveEntry[];
	vacationHoursTaken?: number;
	sickHoursTaken?: number;
	sickPayPaid?: number;

	// Balance snapshot (after this period)
	vacationBalanceHours?: number;
	vacationBalanceDollars?: number;
	sickBalanceHours?: number;

	// YTD Leave (Year-to-Date leave usage)
	ytdVacationHours?: number;
	ytdSickHours?: number;

	// Vacation payout tracking (for accrual method employees)
	vacationPayoutEntries?: VacationPayoutEntry[];
	totalVacationPayout?: number;

	// Paystub status
	paystubStatus?: PaystubStatus;
	paystubSentAt?: string; // ISO datetime
	paystubSentTo?: string; // email address

	// Input data for draft editing (contains user-modified values)
	inputData?: Partial<EmployeePayrollInput>;

	// Modified flag for draft status
	isModified?: boolean;
}

// Holiday in a pay period
export interface Holiday {
	date: string;
	name: string;
	province: string;
}

// Holiday work entry for an employee
export interface HolidayWorkEntry {
	employeeId: string;
	employeeName: string;
	holidayDate: string;
	holidayName: string;
	hoursWorked: number;
}

// Earnings breakdown for expanded row
export interface EarningsBreakdown {
	key: string;       // Unique identifier for the earning item
	label: string;
	amount: number;
	detail?: string;   // e.g., "5h @ $23.08"
	editable?: boolean;
	editType?: 'amount' | 'hours';  // What to edit: dollar amount or hours
	editValue?: number;  // The current value to edit (hours for overtime, amount for regular pay)
}

// Deductions breakdown for expanded row
export interface DeductionsBreakdown {
	label: string;
	amount: number;
	isAutoCalculated: boolean;
}

// ===========================================
// Multi Pay Group Support Types
// ===========================================

/**
 * Summary of a Pay Group for dashboard display
 */
export interface PayGroupSummary {
	id: string;
	name: string;
	payFrequency: 'weekly' | 'bi_weekly' | 'semi_monthly' | 'monthly';
	employmentType: 'full_time' | 'part_time';
	employeeCount: number;
	estimatedGross: number;
	periodStart: string;
	periodEnd: string;
}

/**
 * Upcoming pay date with associated pay groups
 * Used in the Payroll Dashboard
 */
export interface UpcomingPayDate {
	payDate: string; // ISO date string
	payGroups: PayGroupSummary[];
	totalEmployees: number;
	totalEstimatedGross: number;
	// Status of the payroll run for this date (if exists)
	runStatus?: PayrollRunStatus;
	runId?: string;
}

/**
 * Extended PayrollRecord with Pay Group info
 */
export interface PayrollRecordWithGroup extends PayrollRecord {
	payGroupId: string;
	payGroupName: string;
}

/**
 * Pay Group section within a Payroll Run
 */
export interface PayrollRunPayGroup {
	payGroupId: string;
	payGroupName: string;
	payFrequency: 'weekly' | 'bi_weekly' | 'semi_monthly' | 'monthly';
	employmentType: 'full_time' | 'part_time';
	periodStart: string;
	periodEnd: string;
	// Aggregated totals for this pay group
	totalEmployees: number;
	totalGross: number;
	totalDeductions: number;
	totalNetPay: number;
	totalEmployerCost: number;
	// Employee records for this pay group
	records: PayrollRecord[];
	// Structured configurations from pay group
	earningsConfig?: EarningsConfig;
	taxableBenefitsConfig?: TaxableBenefitsConfig;
	deductionsConfig?: DeductionsConfig;
}

/**
 * Payroll Run with multiple Pay Groups
 * Used in the Payroll Run detail page
 */
export interface PayrollRunWithGroups {
	id: string;
	payDate: string;
	status: PayrollRunStatus;
	// All pay groups in this run
	payGroups: PayrollRunPayGroup[];
	// Aggregated totals across all pay groups
	totalEmployees: number;
	totalGross: number;
	totalCppEmployee: number;
	totalCppEmployer: number;
	totalEiEmployee: number;
	totalEiEmployer: number;
	totalFederalTax: number;
	totalProvincialTax: number;
	totalDeductions: number;
	totalNetPay: number;
	totalEmployerCost: number;
	// Holidays applicable to this pay date
	holidays?: Holiday[];
}

// Pay frequency labels for display
export const PAY_FREQUENCY_LABELS: Record<string, string> = {
	weekly: 'Weekly',
	bi_weekly: 'Bi-weekly',
	semi_monthly: 'Semi-monthly',
	monthly: 'Monthly'
};

// Employment type labels for display
export const EMPLOYMENT_TYPE_LABELS: Record<string, string> = {
	full_time: 'Full-time',
	part_time: 'Part-time'
};

// ===========================================
// Payroll Page Status Types
// ===========================================

/**
 * Status of the payroll page for conditional rendering
 * - no_pay_groups: User needs to create pay groups first
 * - no_employees: Pay groups exist but no employees assigned
 * - ready: Ready to display payroll dashboard
 */
export type PayrollPageStatus =
	| { status: 'no_pay_groups' }
	| { status: 'no_employees'; payGroupCount: number }
	| { status: 'ready'; payGroupCount: number; employeeCount: number };

// ===========================================
// Database Types (Supabase)
// ===========================================

/**
 * Database payroll_runs table (snake_case from Supabase)
 */
export interface DbPayrollRun {
	id: string;
	user_id: string;
	ledger_id: string;
	period_start: string;
	period_end: string;
	pay_date: string;
	status: PayrollRunStatus;
	total_employees: number;
	total_gross: number;
	total_cpp_employee: number;
	total_cpp_employer: number;
	total_ei_employee: number;
	total_ei_employer: number;
	total_federal_tax: number;
	total_provincial_tax: number;
	total_net_pay: number;
	total_employer_cost: number;
	beancount_transaction_ids: string[] | null;
	approved_by: string | null;
	approved_at: string | null;
	notes: string | null;
	created_at: string;
	updated_at: string;
}

/**
 * Database payroll_records table (snake_case from Supabase)
 */
export interface DbPayrollRecord {
	id: string;
	payroll_run_id: string;
	employee_id: string;
	user_id: string;
	ledger_id: string;
	// Hours worked (for hourly employees)
	regular_hours_worked: number | null;
	overtime_hours_worked: number;
	hourly_rate_snapshot: number | null;
	// Earnings
	gross_regular: number;
	gross_overtime: number;
	holiday_pay: number;
	holiday_premium_pay: number;
	vacation_pay_paid: number;
	other_earnings: number;
	// Employee Deductions
	cpp_employee: number;
	cpp_additional: number;
	ei_employee: number;
	federal_tax: number;
	provincial_tax: number;
	rrsp: number;
	union_dues: number;
	garnishments: number;
	other_deductions: number;
	// Employer Costs
	cpp_employer: number;
	ei_employer: number;
	// Generated columns
	total_gross: number;
	total_deductions: number;
	net_pay: number;
	total_employer_cost: number;
	// YTD
	ytd_gross: number;
	ytd_cpp: number;
	ytd_ei: number;
	ytd_federal_tax: number;
	ytd_provincial_tax: number;
	// Vacation
	vacation_accrued: number;
	vacation_hours_taken: number;
	// Audit
	calculation_details: Record<string, unknown> | null;
	paystub_storage_key: string | null;
	paystub_generated_at: string | null;
	created_at: string;
	// Draft editing fields
	input_data: Record<string, unknown> | null;
	is_modified: boolean;
}

/**
 * Database payroll_record joined with employee info
 * Used when querying records with employee details
 */
export interface DbPayrollRecordWithEmployee extends DbPayrollRecord {
	employees: {
		id: string;
		first_name: string;
		last_name: string;
		province_of_employment: string;
		pay_group_id: string | null;
		email: string | null;
		annual_salary: number | null;
		hourly_rate: number | null;
		pay_groups: {
			id: string;
			name: string;
			pay_frequency: string;
			employment_type: string;
			earnings_config?: EarningsConfig;
			taxable_benefits_config?: TaxableBenefitsConfig;
			deductions_config?: DeductionsConfig;
		} | null;
	};
}

// ===========================================
// Database to UI Conversion Functions
// ===========================================

/**
 * Convert database payroll_run to UI PayrollRun
 */
export function dbPayrollRunToUi(db: DbPayrollRun): PayrollRun {
	return {
		id: db.id,
		periodStart: db.period_start,
		periodEnd: db.period_end,
		payDate: db.pay_date,
		status: db.status,
		totalEmployees: db.total_employees,
		totalGross: Number(db.total_gross),
		totalCppEmployee: Number(db.total_cpp_employee),
		totalCppEmployer: Number(db.total_cpp_employer),
		totalEiEmployee: Number(db.total_ei_employee),
		totalEiEmployer: Number(db.total_ei_employer),
		totalFederalTax: Number(db.total_federal_tax),
		totalProvincialTax: Number(db.total_provincial_tax),
		totalDeductions: Number(db.total_cpp_employee) + Number(db.total_ei_employee) + Number(db.total_federal_tax) + Number(db.total_provincial_tax),
		totalNetPay: Number(db.total_net_pay),
		totalEmployerCost: Number(db.total_employer_cost)
	};
}

/**
 * Convert database payroll_record with employee info to UI PayrollRecord
 */
export function dbPayrollRecordToUi(db: DbPayrollRecordWithEmployee): PayrollRecord {
	const employee = db.employees;
	// Determine compensation type based on employee salary/rate
	const compensationType: CompensationType = employee.hourly_rate != null ? 'hourly' : 'salaried';

	return {
		id: db.id,
		employeeId: db.employee_id,
		employeeName: `${employee.first_name} ${employee.last_name}`,
		employeeProvince: employee.province_of_employment,
		// Compensation info
		compensationType,
		annualSalary: employee.annual_salary ?? undefined,
		hourlyRate: employee.hourly_rate ?? undefined,
		// Hours worked (for hourly employees)
		regularHoursWorked: db.regular_hours_worked ?? undefined,
		overtimeHoursWorked: db.overtime_hours_worked ?? undefined,
		hourlyRateSnapshot: db.hourly_rate_snapshot ?? undefined,
		// Earnings
		grossRegular: Number(db.gross_regular),
		grossOvertime: Number(db.gross_overtime),
		holidayPay: Number(db.holiday_pay),
		holidayPremiumPay: Number(db.holiday_premium_pay),
		vacationPayPaid: Number(db.vacation_pay_paid),
		otherEarnings: Number(db.other_earnings),
		totalGross: Number(db.total_gross),
		// Deductions
		cppEmployee: Number(db.cpp_employee),
		cppAdditional: Number(db.cpp_additional),
		eiEmployee: Number(db.ei_employee),
		federalTax: Number(db.federal_tax),
		provincialTax: Number(db.provincial_tax),
		rrsp: Number(db.rrsp),
		unionDues: Number(db.union_dues),
		garnishments: Number(db.garnishments),
		otherDeductions: Number(db.other_deductions),
		totalDeductions: Number(db.total_deductions),
		// Net
		netPay: Number(db.net_pay),
		// Employer costs
		cppEmployer: Number(db.cpp_employer),
		eiEmployer: Number(db.ei_employer),
		totalEmployerCost: Number(db.total_employer_cost),
		// YTD
		ytdGross: Number(db.ytd_gross),
		ytdCpp: Number(db.ytd_cpp),
		ytdEi: Number(db.ytd_ei),
		ytdFederalTax: Number(db.ytd_federal_tax),
		ytdProvincialTax: Number(db.ytd_provincial_tax),
		ytdNetPay: Number(db.ytd_gross) - Number(db.ytd_cpp) - Number(db.ytd_ei) - Number(db.ytd_federal_tax) - Number(db.ytd_provincial_tax),
		// Vacation
		vacationHoursTaken: Number(db.vacation_hours_taken),
		// Holiday work hours - empty by default, would be loaded separately
		holidayWorkHours: [],
		// Paystub status
		paystubStatus: db.paystub_generated_at ? 'sent' : 'pending',
		paystubSentAt: db.paystub_generated_at ?? undefined,
		// Draft editing fields
		inputData: db.input_data as Partial<EmployeePayrollInput> | undefined,
		isModified: db.is_modified ?? false
	};
}

/**
 * Convert database payroll_record with employee info to UI PayrollRecordWithGroup
 */
export function dbPayrollRecordToUiWithGroup(db: DbPayrollRecordWithEmployee): PayrollRecordWithGroup {
	const baseRecord = dbPayrollRecordToUi(db);
	const payGroup = db.employees.pay_groups;

	return {
		...baseRecord,
		payGroupId: payGroup?.id ?? 'unknown',
		payGroupName: payGroup?.name ?? 'Unknown Pay Group'
	};
}

// ===========================================
// Before Run State Types
// ===========================================

/**
 * Hours input entry for hourly employees before starting payroll run
 * Maps employee ID to their hours worked for this pay period
 */
export interface HoursInput {
	employeeId: string;
	regularHours: number;
	overtimeHours?: number;
}

// ===========================================
// One-time Adjustment Types
// ===========================================

export type AdjustmentType = 'bonus' | 'retroactive_pay' | 'taxable_benefit' | 'reimbursement' | 'deduction' | 'other';

// Overtime choice when bank time is enabled
export type OvertimeChoice = 'pay_out' | 'bank_time';

export const ADJUSTMENT_TYPE_LABELS: Record<AdjustmentType, { label: string; icon: string; taxable: boolean }> = {
	bonus: { label: 'Bonus', icon: '💰', taxable: true },
	retroactive_pay: { label: 'Retroactive Pay', icon: '⏪', taxable: true },
	taxable_benefit: { label: 'Taxable Benefit', icon: '🎁', taxable: true },
	reimbursement: { label: 'Reimbursement', icon: '💵', taxable: false },
	deduction: { label: 'Deduction', icon: '➖', taxable: false },
	other: { label: 'Other', icon: '📝', taxable: true }
};

export interface Adjustment {
	id: string;
	type: AdjustmentType;
	amount: number;
	description: string;
	taxable: boolean;
	/** Reference to pay group's custom deduction (for deduction type) */
	customDeductionId?: string;
	/** For deductions: pre_tax vs post_tax */
	isPreTax?: boolean;
}

// ===========================================
// Employee Payroll Input (Before Run)
// ===========================================

/**
 * Complete employee payroll input data for Before Run state
 * Includes hours, leave, holiday work, and one-time adjustments
 */
export interface EmployeePayrollInput {
	employeeId: string;

	// Hours
	regularHours: number;          // Required for hourly employees
	overtimeHours: number;         // Overtime hours worked

	// Overtime choice (when bank time is enabled)
	overtimeChoice?: OvertimeChoice;

	// Leave entries
	leaveEntries: Array<{
		type: LeaveType;
		hours: number;
	}>;

	// Holiday work entries
	holidayWorkEntries: Array<{
		holidayDate: string;
		holidayName: string;
		hoursWorked: number;
	}>;

	// One-time adjustments
	adjustments: Adjustment[];

	// Amount overrides (from inline editing)
	overrides?: {
		regularPay?: number;
		overtimePay?: number;
		holidayPay?: number;
	};
}

/**
 * Create a default EmployeePayrollInput
 */
export function createDefaultPayrollInput(
	employeeId: string,
	defaultRegularHours: number = 0
): EmployeePayrollInput {
	return {
		employeeId,
		regularHours: defaultRegularHours,
		overtimeHours: 0,
		leaveEntries: [],
		holidayWorkEntries: [],
		adjustments: []
	};
}

/**
 * Validation result for hours input before starting payroll run
 */
export interface HoursInputValidation {
	isValid: boolean;
	missingHoursEmployees: string[]; // Employee names with missing hours
	errors: string[];
}

/**
 * Helper function to get default regular hours based on pay frequency
 */
export function getDefaultRegularHours(payFrequency: 'weekly' | 'bi_weekly' | 'semi_monthly' | 'monthly'): number {
	switch (payFrequency) {
		case 'weekly':
			return 40;
		case 'bi_weekly':
			return 80;
		case 'semi_monthly':
			return 86.67; // Approximate
		case 'monthly':
			return 173.33; // Approximate
		default:
			return 80;
	}
}

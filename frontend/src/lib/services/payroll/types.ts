/**
 * Payroll Service Types
 * All type definitions for payroll service operations
 */

import type { PayrollRunStatus, PayrollRunWithGroups, PayrollRecord } from '$lib/types/payroll';
import type {
	OvertimePolicy,
	GroupBenefits,
	EarningsConfig,
	TaxableBenefitsConfig,
	DeductionsConfig
} from '$lib/types/pay-group';

// ===========================================
// Service Result Types
// ===========================================

export interface PayrollServiceResult<T> {
	data: T | null;
	error: string | null;
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

// ===========================================
// Payroll Run List
// ===========================================

export interface PayrollRunListOptions {
	status?: PayrollRunStatus;
	limit?: number;
	offset?: number;
}

export interface PayrollRunListOptionsExt extends PayrollRunListOptions {
	excludeStatuses?: string[];
	payGroupId?: string; // Filter by pay group
	employeeId?: string; // Filter by employee
	startDate?: string; // ISO date string (period_end >= startDate)
	endDate?: string; // ISO date string (period_end <= endDate)
}

export interface PayrollRunListResult {
	data: PayrollRunWithGroups[];
	count: number;
	error: string | null;
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
 * Includes Pay Group configuration for conditional UI rendering
 */
export interface PayGroupWithEmployees {
	id: string;
	name: string;
	payFrequency: 'weekly' | 'bi_weekly' | 'semi_monthly' | 'monthly';
	employmentType: 'full_time' | 'part_time' | 'seasonal' | 'contract' | 'casual';
	periodStart: string;
	periodEnd: string;
	employees: EmployeeForPayroll[];
	leaveEnabled: boolean;
	overtimePolicy: OvertimePolicy;
	groupBenefits: GroupBenefits;
	// Structured configurations
	earningsConfig: EarningsConfig;
	taxableBenefitsConfig: TaxableBenefitsConfig;
	deductionsConfig: DeductionsConfig;
}

/**
 * Data for "before run" state - pay groups with their employees
 */
export interface BeforeRunData {
	periodEnd: string; // Authoritative grouping key
	payDate: string; // Auto-calculated: periodEnd + 6 days (SK)
	payGroups: PayGroupWithEmployees[];
	totalEmployees: number;
	holidays: { date: string; name: string; province: string }[];
}

// ===========================================
// Backend API Types for Payroll Calculation
// ===========================================

export interface EmployeeCalculationRequest {
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

export interface BatchCalculationRequest {
	employees: EmployeeCalculationRequest[];
	include_details?: boolean;
}

export interface CalculationResult {
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

export interface BatchCalculationResponse {
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
// Employee Payroll Record List (for History)
// ===========================================

/**
 * Options for listing employee payroll records
 * Used when viewing individual employee's payroll history
 */
export interface PayrollRecordListOptions {
	startDate?: string; // Filter by period_end >= startDate
	endDate?: string; // Filter by period_end <= endDate
	status?: PayrollRunStatus; // Filter by run status
	excludeStatuses?: string[]; // Exclude these statuses
	limit?: number; // Default 20
	offset?: number; // Default 0
}

/**
 * Result type for employee payroll records list
 */
export interface PayrollRecordListResult {
	data: PayrollRecordWithPeriod[];
	count: number;
	error: string | null;
}

/**
 * Extended PayrollRecord with period info from the parent payroll run
 * Used for displaying individual employee's payroll history
 */
export interface PayrollRecordWithPeriod extends PayrollRecord {
	periodEnd: string; // From payroll_runs
	payDate: string; // From payroll_runs
	runStatus: PayrollRunStatus; // From payroll_runs
	runId: string; // For navigation to the run detail page
}

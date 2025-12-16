/**
 * Employee types for Payroll UI
 */

export type Province =
	| 'AB' | 'BC' | 'MB' | 'NB' | 'NL' | 'NS'
	| 'NT' | 'NU' | 'ON' | 'PE' | 'QC' | 'SK' | 'YT';

export const PROVINCE_LABELS: Record<Province, string> = {
	AB: 'Alberta', BC: 'British Columbia', MB: 'Manitoba',
	NB: 'New Brunswick', NL: 'Newfoundland', NS: 'Nova Scotia',
	NT: 'NW Territories', NU: 'Nunavut', ON: 'Ontario',
	PE: 'PEI', QC: 'Quebec', SK: 'Saskatchewan', YT: 'Yukon'
};

export type PayFrequency = 'weekly' | 'bi_weekly' | 'semi_monthly' | 'monthly';

export const PAY_FREQUENCY_LABELS: Record<PayFrequency, string> = {
	weekly: 'Weekly', bi_weekly: 'Bi-weekly',
	semi_monthly: 'Semi-monthly', monthly: 'Monthly'
};

// Pay periods per year
export const PAY_PERIODS_PER_YEAR: Record<PayFrequency, number> = {
	weekly: 52,
	bi_weekly: 26,
	semi_monthly: 24,
	monthly: 12
};

export type EmploymentType = 'full_time' | 'part_time';

export const EMPLOYMENT_TYPE_LABELS: Record<EmploymentType, string> = {
	full_time: 'Full-time',
	part_time: 'Part-time'
};

export type VacationPayoutMethod = 'accrual' | 'pay_as_you_go' | 'lump_sum';
export type VacationRate = '0.04' | '0.06' | '0.08';
export type CompensationType = 'salaried' | 'hourly';
export type EmployeeStatus = 'draft' | 'active' | 'terminated';

export const EMPLOYEE_STATUS_LABELS: Record<EmployeeStatus, string> = {
	draft: 'Draft',
	active: 'Active',
	terminated: 'Terminated'
};

export const VACATION_RATE_LABELS: Record<VacationRate, string> = {
	'0.04': '4% (< 5 years)',
	'0.06': '6% (5+ years)',
	'0.08': '8% (Federal 10+)'
};

export interface VacationConfig {
	payoutMethod: VacationPayoutMethod;
	vacationRate: VacationRate;
}

export interface Employee {
	id: string;
	firstName: string;
	lastName: string;
	sin: string; // For UI display (masked or full)
	email?: string;
	provinceOfEmployment: Province;  // Determines provincial tax & holiday rules
	payFrequency: PayFrequency;
	employmentType: EmploymentType;
	status: EmployeeStatus;
	hireDate: string;
	terminationDate?: string | null;
	annualSalary?: number | null;
	hourlyRate?: number | null;
	federalClaimAmount: number;
	provincialClaimAmount: number;
	isCppExempt: boolean;
	isEiExempt: boolean;
	cpp2Exempt: boolean;
	rrspPerPeriod: number;
	unionDuesPerPeriod: number;
	vacationConfig: VacationConfig;
	vacationBalance: number;  // Read-only, updated by payroll system
}

// Column groups for Excel-like table view
export type ColumnGroup = 'personal' | 'employment' | 'compensation' | 'tax' | 'deductions';

export const COLUMN_GROUP_LABELS: Record<ColumnGroup, string> = {
	personal: 'Personal',
	employment: 'Employment',
	compensation: 'Compensation',
	tax: 'Tax',
	deductions: 'Deductions'
};

// ============================================================================
// Filter Types
// ============================================================================

export interface EmployeeFilters {
	status: EmployeeStatus | 'all';
	province: Province | 'all';
	payFrequency: PayFrequency | 'all';
	employmentType: EmploymentType | 'all';
	compensationType: CompensationType | 'all';
	searchQuery: string;
}

export const DEFAULT_EMPLOYEE_FILTERS: EmployeeFilters = {
	status: 'all',
	province: 'all',
	payFrequency: 'all',
	employmentType: 'all',
	compensationType: 'all',
	searchQuery: ''
};

export interface EmployeeStatusCounts {
	total: number;
	draft: number;
	active: number;
	terminated: number;
}

// 2025 Basic Personal Amounts
export const FEDERAL_BPA_2025 = 16129;
export const PROVINCIAL_BPA_2025: Record<Province, number> = {
	AB: 21003, BC: 12580, MB: 15780, NB: 13044, NL: 10818, NS: 8481,
	NT: 17373, NU: 18767, ON: 12399, PE: 14250, QC: 18056, SK: 18491, YT: 16129
};

// ============================================================================
// Computed Fields & Helper Functions
// ============================================================================

/**
 * Calculate years of service from hire date.
 * Used for vacation rate determination.
 */
export function calculateYearsOfService(hireDate: string): number {
	const hire = new Date(hireDate);
	const today = new Date();
	const diffMs = today.getTime() - hire.getTime();
	const diffDays = diffMs / (1000 * 60 * 60 * 24);
	return Math.round((diffDays / 365.25) * 100) / 100; // 2 decimal places
}

/**
 * Suggest vacation rate based on years of service.
 *
 * Standard rates (all provinces except Federal):
 * - 0-5 years: 4%
 * - 5+ years: 6%
 * - 10+ years (Federal only): 8%
 */
export function suggestVacationRate(yearsOfService: number, isFederal = false): VacationRate {
	if (yearsOfService >= 10 && isFederal) return '0.08';
	if (yearsOfService >= 5) return '0.06';
	return '0.04';
}

/**
 * Calculate per-period gross pay from annual salary.
 */
export function calculatePerPeriodGross(annualSalary: number, payFrequency: PayFrequency): number {
	return annualSalary / PAY_PERIODS_PER_YEAR[payFrequency];
}

/**
 * Check if an employee's vacation balance can be edited.
 * Only new (draft) employees or during initial import can have balance edited.
 */
export function canEditVacationBalance(employee: Employee): boolean {
	return employee.status === 'draft' || employee.id.startsWith('new-');
}

/**
 * Employee types for Payroll UI
 */

// 12 provinces/territories supported (Quebec excluded - separate system required)
export type Province =
	| 'AB' | 'BC' | 'MB' | 'NB' | 'NL' | 'NS'
	| 'NT' | 'NU' | 'ON' | 'PE' | 'SK' | 'YT';

export const PROVINCE_LABELS: Record<Province, string> = {
	AB: 'Alberta', BC: 'British Columbia', MB: 'Manitoba',
	NB: 'New Brunswick', NL: 'Newfoundland', NS: 'Nova Scotia',
	NT: 'NW Territories', NU: 'Nunavut', ON: 'Ontario',
	PE: 'PEI', SK: 'Saskatchewan', YT: 'Yukon'
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

export type EmploymentType = 'full_time' | 'part_time' | 'contract' | 'casual';

export const EMPLOYMENT_TYPE_LABELS: Record<EmploymentType, string> = {
	full_time: 'Full-time',
	part_time: 'Part-time',
	contract: 'Contract',
	casual: 'Casual'
};

export type VacationPayoutMethod = 'accrual' | 'pay_as_you_go';
// Predefined vacation rates or 'custom' for user-defined rates
export type VacationRatePreset = '0' | '0.04' | '0.06' | '0.08' | 'custom';
// Actual vacation rate can be any numeric string (for custom) or preset
export type VacationRate = string;
export type CompensationType = 'salaried' | 'hourly';
export type EmployeeStatus = 'draft' | 'active' | 'terminated';

export const EMPLOYEE_STATUS_LABELS: Record<EmployeeStatus, string> = {
	draft: 'Draft',
	active: 'Active',
	terminated: 'Terminated'
};

export const VACATION_RATE_LABELS: Record<VacationRatePreset, string> = {
	'0': 'None (Owner/Contractor)',
	'0.04': '4% (< 5 years)',
	'0.06': '6% (5+ years)',
	'0.08': '8% (Federal 10+)',
	'custom': 'Custom Rate'
};

/**
 * Check if a vacation rate is a preset or custom
 */
export function isPresetVacationRate(rate: string): rate is VacationRatePreset {
	return rate in VACATION_RATE_LABELS;
}

/**
 * Get the preset key for display, or 'custom' if not a preset
 */
export function getVacationRatePreset(rate: string): VacationRatePreset {
	if (rate === '0' || rate === '0.04' || rate === '0.06' || rate === '0.08') {
		return rate;
	}
	return 'custom';
}

/**
 * Format vacation rate as percentage for display
 */
export function formatVacationRate(rate: string): string {
	const numRate = parseFloat(rate);
	if (isNaN(numRate)) return '0%';
	return `${(numRate * 100).toFixed(2).replace(/\.?0+$/, '')}%`;
}

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
	// Address fields (for paystub)
	addressStreet?: string | null;
	addressCity?: string | null;
	addressPostalCode?: string | null;
	occupation?: string | null;
	// Compensation
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
	sickBalance: number;  // Read-only, updated by payroll system
	tags: string[];  // Employee categorization tags
	payGroupId?: string | null;  // Pay group assignment
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
	payGroupId: string | 'all';  // Filter by pay group assignment
	searchQuery: string;
}

export const DEFAULT_EMPLOYEE_FILTERS: EmployeeFilters = {
	status: 'all',
	province: 'all',
	payFrequency: 'all',
	employmentType: 'all',
	compensationType: 'all',
	payGroupId: 'all',
	searchQuery: ''
};

export interface EmployeeStatusCounts {
	total: number;
	draft: number;
	active: number;
	terminated: number;
}

// 2025 Basic Personal Amounts (from T4127 July 2025 edition)
export const FEDERAL_BPA_2025 = 16129;
export const PROVINCIAL_BPA_2025: Record<Province, number> = {
	AB: 22323, BC: 12932, MB: 15591, NB: 13396, NL: 11067, NS: 11744,
	NT: 17842, NU: 19274, ON: 12747, PE: 15050, SK: 19991, YT: 16129
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
export function suggestVacationRate(yearsOfService: number, isFederal = false): VacationRatePreset {
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

// ============================================================================
// Database Types (for Supabase interactions)
// ============================================================================

/**
 * Database row type for employees table (snake_case)
 */
export interface DbEmployee {
	id: string;
	user_id: string;
	ledger_id: string;
	first_name: string;
	last_name: string;
	sin_encrypted: string;
	email: string | null;
	province_of_employment: Province;
	pay_frequency: PayFrequency;
	employment_type: EmploymentType;
	// Address fields
	address_street: string | null;
	address_city: string | null;
	address_postal_code: string | null;
	occupation: string | null;
	// Compensation
	annual_salary: number | null;
	hourly_rate: number | null;
	federal_claim_amount: number;
	provincial_claim_amount: number;
	is_cpp_exempt: boolean;
	is_ei_exempt: boolean;
	cpp2_exempt: boolean;
	rrsp_per_period: number;
	union_dues_per_period: number;
	hire_date: string;
	termination_date: string | null;
	vacation_config: {
		payout_method: VacationPayoutMethod;
		vacation_rate: string;
	};
	vacation_balance: number;
	sick_balance: number;
	tags: string[];
	pay_group_id: string | null;
	created_at: string;
	updated_at: string;
}

/**
 * Input type for creating an employee (excludes auto-generated fields)
 */
export interface EmployeeCreateInput {
	first_name: string;
	last_name: string;
	sin: string; // Raw SIN - will be encrypted on backend
	email?: string | null;
	province_of_employment: Province;
	pay_frequency: PayFrequency;
	employment_type?: EmploymentType;
	// Address fields
	address_street?: string | null;
	address_city?: string | null;
	address_postal_code?: string | null;
	occupation?: string | null;
	// Compensation
	annual_salary?: number | null;
	hourly_rate?: number | null;
	federal_claim_amount: number;
	provincial_claim_amount: number;
	is_cpp_exempt?: boolean;
	is_ei_exempt?: boolean;
	cpp2_exempt?: boolean;
	rrsp_per_period?: number;
	union_dues_per_period?: number;
	hire_date: string;
	termination_date?: string | null;
	vacation_config?: {
		payout_method: VacationPayoutMethod;
		vacation_rate: string;
	};
	vacation_balance?: number;
}

/**
 * Input type for updating an employee (all fields optional)
 */
export type EmployeeUpdateInput = Partial<Omit<EmployeeCreateInput, 'sin'>>;

/**
 * Convert database employee to UI employee
 */
export function dbEmployeeToUi(db: DbEmployee, maskedSin: string): Employee {
	return {
		id: db.id,
		firstName: db.first_name,
		lastName: db.last_name,
		sin: maskedSin,
		email: db.email ?? undefined,
		provinceOfEmployment: db.province_of_employment,
		payFrequency: db.pay_frequency,
		employmentType: db.employment_type,
		status: db.termination_date ? 'terminated' : 'active',
		hireDate: db.hire_date,
		terminationDate: db.termination_date,
		// Address fields
		addressStreet: db.address_street,
		addressCity: db.address_city,
		addressPostalCode: db.address_postal_code,
		occupation: db.occupation,
		// Compensation
		annualSalary: db.annual_salary,
		hourlyRate: db.hourly_rate,
		federalClaimAmount: db.federal_claim_amount,
		provincialClaimAmount: db.provincial_claim_amount,
		isCppExempt: db.is_cpp_exempt,
		isEiExempt: db.is_ei_exempt,
		cpp2Exempt: db.cpp2_exempt,
		rrspPerPeriod: db.rrsp_per_period,
		unionDuesPerPeriod: db.union_dues_per_period,
		vacationConfig: {
			payoutMethod: db.vacation_config.payout_method,
			vacationRate: db.vacation_config.vacation_rate as VacationRate
		},
		vacationBalance: db.vacation_balance,
		sickBalance: db.sick_balance ?? 0,
		tags: db.tags ?? [],
		payGroupId: db.pay_group_id
	};
}

/**
 * Convert UI employee to database input for create
 */
export function uiEmployeeToDbCreate(
	ui: Omit<Employee, 'id' | 'status' | 'vacationBalance'> & { sin: string }
): EmployeeCreateInput {
	return {
		first_name: ui.firstName,
		last_name: ui.lastName,
		sin: ui.sin,
		email: ui.email ?? null,
		province_of_employment: ui.provinceOfEmployment,
		pay_frequency: ui.payFrequency,
		employment_type: ui.employmentType,
		// Address fields
		address_street: ui.addressStreet ?? null,
		address_city: ui.addressCity ?? null,
		address_postal_code: ui.addressPostalCode ?? null,
		occupation: ui.occupation ?? null,
		// Compensation
		annual_salary: ui.annualSalary ?? null,
		hourly_rate: ui.hourlyRate ?? null,
		federal_claim_amount: ui.federalClaimAmount,
		provincial_claim_amount: ui.provincialClaimAmount,
		is_cpp_exempt: ui.isCppExempt,
		is_ei_exempt: ui.isEiExempt,
		cpp2_exempt: ui.cpp2Exempt,
		rrsp_per_period: ui.rrspPerPeriod,
		union_dues_per_period: ui.unionDuesPerPeriod,
		hire_date: ui.hireDate,
		termination_date: ui.terminationDate ?? null,
		vacation_config: {
			payout_method: ui.vacationConfig.payoutMethod,
			vacation_rate: ui.vacationConfig.vacationRate
		}
	};
}

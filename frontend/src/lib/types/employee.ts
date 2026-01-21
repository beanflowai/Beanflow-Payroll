/**
 * Employee types for Payroll UI
 */

// Re-export PortalStatus from employee-portal for convenience
export type { PortalStatus } from './employee-portal';

// Import types from pay-group for matching logic
import type {
	CompensationType as PayGroupCompensationType,
	EmploymentType as PayGroupEmploymentType,
	PayFrequency as PayGroupPayFrequency
} from './pay-group';

// 12 provinces/territories supported (Quebec excluded - separate system required)
export type Province =
	| 'AB'
	| 'BC'
	| 'MB'
	| 'NB'
	| 'NL'
	| 'NS'
	| 'NT'
	| 'NU'
	| 'ON'
	| 'PE'
	| 'SK'
	| 'YT';

export const PROVINCE_LABELS: Record<Province, string> = {
	AB: 'Alberta',
	BC: 'British Columbia',
	MB: 'Manitoba',
	NB: 'New Brunswick',
	NL: 'Newfoundland',
	NS: 'Nova Scotia',
	NT: 'NW Territories',
	NU: 'Nunavut',
	ON: 'Ontario',
	PE: 'PEI',
	SK: 'Saskatchewan',
	YT: 'Yukon'
};

export type PayFrequency = 'weekly' | 'bi_weekly' | 'semi_monthly' | 'monthly';

export const PAY_FREQUENCY_LABELS: Record<PayFrequency, string> = {
	weekly: 'Weekly',
	bi_weekly: 'Bi-weekly',
	semi_monthly: 'Semi-monthly',
	monthly: 'Monthly'
};

// Pay periods per year
export const PAY_PERIODS_PER_YEAR: Record<PayFrequency, number> = {
	weekly: 52,
	bi_weekly: 26,
	semi_monthly: 24,
	monthly: 12
};

export type EmploymentType = 'full_time' | 'part_time' | 'seasonal' | 'contract' | 'casual';

export const EMPLOYMENT_TYPE_LABELS: Record<EmploymentType, string> = {
	full_time: 'Full-time',
	part_time: 'Part-time',
	seasonal: 'Seasonal',
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
	custom: 'Custom Rate'
};

// Note: Provincial minimum vacation rates are managed in backend config files
// See backend/config/vacation_pay/{year}/provinces_{edition}.json
// SK is unique: 5.77% (3 weeks) from day one, most others: 4% (2 weeks)

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
	/** Vacation rate as decimal (e.g., '0.04' = 4%, '0' = none for Owner/Contractor). */
	vacationRate: VacationRate;
}

export interface Employee {
	id: string;
	firstName: string;
	lastName: string;
	sin: string; // For UI display (masked or empty if not provided)
	email?: string;
	provinceOfEmployment: Province; // Determines provincial tax & holiday rules
	payFrequency: PayFrequency;
	employmentType: EmploymentType;
	status: EmployeeStatus;
	hireDate: string;
	dateOfBirth?: string | null; // For CPP calculations
	terminationDate?: string | null;
	// Address fields (for paystub)
	addressStreet?: string | null;
	addressCity?: string | null;
	addressPostalCode?: string | null;
	occupation?: string | null;
	// Compensation
	annualSalary?: number | null;
	hourlyRate?: number | null;
	// TD1 additional claims beyond BPA (BPA is fetched dynamically from tax tables)
	federalAdditionalClaims: number;
	provincialAdditionalClaims: number;
	isCppExempt: boolean;
	isEiExempt: boolean;
	cpp2Exempt: boolean;
	vacationConfig: VacationConfig;
	vacationBalance: number; // Read-only, updated by payroll system
	sickBalance: number; // Read-only, updated by payroll system
	tags: string[]; // Employee categorization tags
	payGroupId?: string | null; // Pay group assignment
	// Initial YTD for transferred employees (CPP/EI only - tax handled by Cumulative Averaging)
	initialYtdCpp: number;
	initialYtdCpp2: number;
	initialYtdEi: number;
	initialYtdYear: number | null; // Tax year these values apply to
	// Portal access fields
	portalStatus: 'not_set' | 'invited' | 'active' | 'disabled';
	portalInvitedAt?: string | null;
	portalLastLoginAt?: string | null;
}

// Column groups for Excel-like table view
export type ColumnGroup = 'personal' | 'employment' | 'compensation' | 'tax';

export const COLUMN_GROUP_LABELS: Record<ColumnGroup, string> = {
	personal: 'Personal',
	employment: 'Employment',
	compensation: 'Compensation',
	tax: 'Tax'
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
	payGroupId: string | 'all'; // Filter by pay group assignment
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

// ============================================================================
// BPA Constants (Fallback Values)
// ============================================================================
// NOTE: These constants are used as FALLBACK values when API is unavailable.
// For dynamic BPA that adapts to tax year and edition, use taxConfigService.ts
// which fetches BPA from the API: /api/v1/payroll/bpa-defaults/{province}
// ============================================================================

// 2025 Basic Personal Amounts (Fallback)
// Federal: same for both editions
export const FEDERAL_BPA_2025 = 16129;

// Provincial BPA - January Edition (T4127 120th Edition, for Jan-Jun payrolls)
// SK and PE have different BPA in January vs July
export const PROVINCIAL_BPA_2025_JAN: Record<Province, number> = {
	AB: 22323,
	BC: 12932,
	MB: 15591,
	NB: 13396,
	NL: 11067,
	NS: 11744,
	NT: 17842,
	NU: 19274,
	ON: 12747,
	PE: 14250,
	SK: 18991,
	YT: 16129
};

// Provincial BPA - July Edition (T4127 121st Edition, for Jul-Dec payrolls)
export const PROVINCIAL_BPA_2025_JUL: Record<Province, number> = {
	AB: 22323,
	BC: 12932,
	MB: 15591,
	NB: 13396,
	NL: 11067,
	NS: 11744,
	NT: 17842,
	NU: 19274,
	ON: 12747,
	PE: 15050,
	SK: 19991,
	YT: 16129
};

// Default export (July edition for backward compatibility)
export const PROVINCIAL_BPA_2025 = PROVINCIAL_BPA_2025_JUL;

// Provinces with different BPA in January vs July editions
export const PROVINCES_WITH_EDITION_DIFF: readonly Province[] = ['SK', 'PE'] as const;

/**
 * Get the correct provincial BPA based on pay date.
 * For 2025, SK and PE have different BPA in January vs July edition.
 *
 * @param province - Province code
 * @param payDate - Pay date (defaults to July edition if not provided)
 * @returns Provincial BPA for the correct edition
 */
export function getProvincialBPA(province: Province, payDate?: Date): number {
	if (!payDate) {
		return PROVINCIAL_BPA_2025_JUL[province];
	}
	// Before July 1 uses January edition, on/after July 1 uses July edition
	const useJanEdition = payDate.getMonth() < 6; // 0-based month, 6 = July
	return useJanEdition ? PROVINCIAL_BPA_2025_JAN[province] : PROVINCIAL_BPA_2025_JUL[province];
}

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
// Employee Tax Claims (TD1 by year)
// ============================================================================

/**
 * TD1 tax claim for a specific year
 * BPA values are read-only (from tax config), only additional claims are editable
 */
export interface EmployeeTaxClaim {
	id: string;
	employeeId: string;
	companyId: string;
	taxYear: number;
	// Federal TD1
	federalBpa: number; // Read-only, from config
	federalAdditionalClaims: number;
	federalTotalClaim: number; // Computed: bpa + additional
	// Provincial TD1
	provincialBpa: number; // Read-only, from config
	provincialAdditionalClaims: number;
	provincialTotalClaim: number; // Computed: bpa + additional
	// Metadata
	createdAt: string;
	updatedAt: string;
}

/**
 * Database row type for employee_tax_claims (snake_case)
 */
export interface DbEmployeeTaxClaim {
	id: string;
	employee_id: string;
	company_id: string;
	user_id: string;
	tax_year: number;
	federal_bpa: number;
	federal_additional_claims: number;
	federal_total_claim?: number; // Computed field
	provincial_bpa: number;
	provincial_additional_claims: number;
	provincial_total_claim?: number; // Computed field
	created_at: string;
	updated_at: string;
}

/**
 * Input for updating tax claim additional claims
 */
export interface TaxClaimUpdateInput {
	federalAdditionalClaims?: number;
	provincialAdditionalClaims?: number;
}

/**
 * Convert database tax claim to UI format
 */
export function dbTaxClaimToUi(db: DbEmployeeTaxClaim): EmployeeTaxClaim {
	const federalTotal = db.federal_bpa + db.federal_additional_claims;
	const provincialTotal = db.provincial_bpa + db.provincial_additional_claims;
	return {
		id: db.id,
		employeeId: db.employee_id,
		companyId: db.company_id,
		taxYear: db.tax_year,
		federalBpa: db.federal_bpa,
		federalAdditionalClaims: db.federal_additional_claims,
		federalTotalClaim: db.federal_total_claim ?? federalTotal,
		provincialBpa: db.provincial_bpa,
		provincialAdditionalClaims: db.provincial_additional_claims,
		provincialTotalClaim: db.provincial_total_claim ?? provincialTotal,
		createdAt: db.created_at,
		updatedAt: db.updated_at
	};
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
	first_name: string;
	last_name: string;
	sin_encrypted: string | null;
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
	federal_additional_claims: number;
	provincial_additional_claims: number;
	is_cpp_exempt: boolean;
	is_ei_exempt: boolean;
	cpp2_exempt: boolean;
	hire_date: string;
	date_of_birth: string | null;
	termination_date: string | null;
	vacation_config: {
		payout_method: VacationPayoutMethod;
		vacation_rate: string | null; // null handled as '0.04' default; "0" = none
	};
	vacation_balance: number;
	sick_balance: number;
	tags: string[];
	pay_group_id: string | null;
	// Initial YTD for transferred employees
	initial_ytd_cpp: number;
	initial_ytd_cpp2: number;
	initial_ytd_ei: number;
	initial_ytd_year: number | null;
	// Portal access fields
	portal_status: 'not_set' | 'invited' | 'active' | 'disabled';
	portal_invited_at: string | null;
	portal_last_login_at: string | null;
	created_at: string;
	updated_at: string;
}

/**
 * Input type for creating an employee (excludes auto-generated fields)
 */
export interface EmployeeCreateInput {
	first_name: string;
	last_name: string;
	sin?: string | null; // Raw SIN - will be encrypted on backend, now optional
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
	federal_additional_claims: number;
	provincial_additional_claims: number;
	is_cpp_exempt?: boolean;
	is_ei_exempt?: boolean;
	cpp2_exempt?: boolean;
	date_of_birth?: string | null;
	hire_date: string;
	termination_date?: string | null;
	vacation_config?: {
		payout_method: VacationPayoutMethod;
		vacation_rate: string | null; // null = use default; "0" = none
	};
	vacation_balance?: number;
	// Initial YTD for transferred employees
	initial_ytd_cpp?: number;
	initial_ytd_cpp2?: number;
	initial_ytd_ei?: number;
	initial_ytd_year?: number | null;
}

/**
 * Input type for updating an employee (all fields optional)
 */
export type EmployeeUpdateInput = Partial<EmployeeCreateInput>;

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
		dateOfBirth: db.date_of_birth,
		terminationDate: db.termination_date,
		// Address fields
		addressStreet: db.address_street,
		addressCity: db.address_city,
		addressPostalCode: db.address_postal_code,
		occupation: db.occupation,
		// Compensation
		annualSalary: db.annual_salary,
		hourlyRate: db.hourly_rate,
		federalAdditionalClaims: db.federal_additional_claims,
		provincialAdditionalClaims: db.provincial_additional_claims,
		isCppExempt: db.is_cpp_exempt,
		isEiExempt: db.is_ei_exempt,
		cpp2Exempt: db.cpp2_exempt,
		vacationConfig: {
			payoutMethod: db.vacation_config.payout_method,
			vacationRate: (db.vacation_config.vacation_rate ?? '0.04') as VacationRate
		},
		vacationBalance: db.vacation_balance,
		sickBalance: db.sick_balance ?? 0,
		tags: db.tags ?? [],
		payGroupId: db.pay_group_id,
		// Initial YTD for transferred employees
		initialYtdCpp: db.initial_ytd_cpp ?? 0,
		initialYtdCpp2: db.initial_ytd_cpp2 ?? 0,
		initialYtdEi: db.initial_ytd_ei ?? 0,
		initialYtdYear: db.initial_ytd_year ?? null,
		// Portal access fields
		portalStatus: db.portal_status ?? 'not_set',
		portalInvitedAt: db.portal_invited_at,
		portalLastLoginAt: db.portal_last_login_at
	};
}

/**
 * Convert UI employee to database input for create
 */
export function uiEmployeeToDbCreate(
	ui: Omit<Employee, 'id' | 'status' | 'vacationBalance'> & { sin?: string | null }
): EmployeeCreateInput {
	return {
		first_name: ui.firstName,
		last_name: ui.lastName,
		sin: ui.sin ?? null,
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
		federal_additional_claims: ui.federalAdditionalClaims,
		provincial_additional_claims: ui.provincialAdditionalClaims,
		is_cpp_exempt: ui.isCppExempt,
		is_ei_exempt: ui.isEiExempt,
		cpp2_exempt: ui.cpp2Exempt,
		date_of_birth: ui.dateOfBirth ?? null,
		hire_date: ui.hireDate,
		termination_date: ui.terminationDate ?? null,
		vacation_config: {
			payout_method: ui.vacationConfig.payoutMethod,
			vacation_rate: ui.vacationConfig.vacationRate
		},
		// Initial YTD for transferred employees
		initial_ytd_cpp: ui.initialYtdCpp ?? 0,
		initial_ytd_cpp2: ui.initialYtdCpp2 ?? 0,
		initial_ytd_ei: ui.initialYtdEi ?? 0,
		initial_ytd_year: ui.initialYtdYear ?? null
	};
}

// ============================================================================
// Pay Group Employee Matching Types
// ============================================================================

/**
 * Mismatch reason for employee-pay group matching
 */
export type MismatchReason =
	| { field: 'province'; expected: Province; actual: Province }
	| { field: 'payFrequency'; expected: PayGroupPayFrequency; actual: PayFrequency }
	| { field: 'employmentType'; expected: PayGroupEmploymentType; actual: EmploymentType }
	| { field: 'compensationType'; expected: PayGroupCompensationType; actual: PayGroupCompensationType };

/**
 * Result of checking if an employee matches a pay group
 */
export interface EmployeeMatchResult {
	employee: Employee;
	isMatch: boolean;
	mismatchReasons: MismatchReason[];
}

/**
 * Get the compensation type from an employee (inferred from annualSalary/hourlyRate)
 * Priority: hourly rate takes precedence (even if 0), otherwise salaried
 */
export function getEmployeeCompensationType(employee: Employee): PayGroupCompensationType {
	// Use != null to check for both null and undefined, but allow 0 as valid hourly rate
	return employee.hourlyRate != null ? 'hourly' : 'salary';
}

/**
 * Format a mismatch reason for display
 */
export function formatMismatchReason(reason: MismatchReason): string {
	const fieldLabels: Record<MismatchReason['field'], string> = {
		province: 'Province',
		payFrequency: 'Pay Frequency',
		employmentType: 'Employment Type',
		compensationType: 'Compensation Type'
	};

	const formatValue = (field: MismatchReason['field'], value: string): string => {
		switch (field) {
			case 'province':
				return PROVINCE_LABELS[value as Province] || value;
			case 'payFrequency':
				return PAY_FREQUENCY_LABELS[value as PayFrequency] || value;
			case 'employmentType':
				return EMPLOYMENT_TYPE_LABELS[value as EmploymentType] || value;
			case 'compensationType':
				return value === 'salary' ? 'Salary' : 'Hourly';
			default:
				return value;
		}
	};

	return `${fieldLabels[reason.field]}: ${formatValue(reason.field, reason.actual)} (expected ${formatValue(reason.field, reason.expected)})`;
}

/**
 * Pay Group Types for BeanFlow Payroll
 *
 * Pay Groups are "Policy Templates" that define payroll configuration including:
 * - Pay schedule (frequency, dates)
 * - Province (defaults to company province, determines holidays)
 * - Statutory deduction defaults (CPP/EI exemptions)
 * - Overtime & bank time policies
 * - WCB/workers compensation configuration
 * - Group benefits (health, dental, vision, life, disability)
 * - Earnings configuration (bonus, commission, allowances)
 * - Taxable benefits configuration (automobile, housing)
 * - Deductions configuration (RRSP, union dues, custom)
 */

import type { Province } from './employee';

// Pay frequency options
export type PayFrequency = 'weekly' | 'bi_weekly' | 'semi_monthly' | 'monthly';

/**
 * Tax calculation method per CRA T4127
 * - annualization: Option 1 - Each period calculated independently
 * - cumulative_averaging: Option 2 - Considers YTD earnings and tax
 */
export type TaxCalculationMethod = 'annualization' | 'cumulative_averaging';

// Bank time rate options (varies by province)
export type BankTimeRate = 1.0 | 1.5;

// Bank time expiry options (in months)
export type BankTimeExpiryMonths = 3 | 6 | 12;

// Deduction type for custom deductions
export type DeductionType = 'pre_tax' | 'post_tax';

// Calculation type for deductions/earnings
export type CalculationType = 'fixed' | 'percentage';

// ============================================
// EARNINGS CONFIG TYPES (CRA Compliant)
// ============================================

/** Bonus type - affects overtime/vacation pay calculation per CRA rules */
export type BonusType = 'discretionary' | 'non_discretionary';

/** Commission calculation methods */
export type CommissionCalculationType =
	| 'percentage_gross' // % of gross pay
	| 'sales_percentage' // % of sales (requires input)
	| 'fixed'; // Fixed amount

/** Allowance types with specific tax rules per CRA */
export type AllowanceType =
	| 'meal' // Non-taxable if <= $23 + overtime + occasional
	| 'travel' // Non-taxable if reasonable (70c/km)
	| 'housing' // Always taxable
	| 'moving' // Non-taxable if <= $650
	| 'northern_zone' // $11/day northern, $5.50/day intermediate
	| 'tool' // Tradesperson tools
	| 'uniform' // Non-taxable if employer-required
	| 'cell_phone' // Non-taxable if business use
	| 'other';

/** Individual allowance configuration */
export interface AllowanceConfig {
	id: string;
	type: AllowanceType;
	name: string;
	enabled: boolean;
	calculationType: 'fixed' | 'per_diem' | 'per_km';
	defaultAmount: number;
	ratePerKm?: number;
	requiresOvertime?: boolean; // For meal allowance
	taxableOverride?: boolean;
	description?: string;
}

/** Bonus configuration with CRA discretionary/non-discretionary distinction */
export interface BonusConfig {
	enabled: boolean;
	/** Discretionary bonuses are NOT included in overtime/vacation base */
	discretionaryEnabled: boolean;
	/** Non-discretionary bonuses ARE included in overtime/vacation base (CRA rule) */
	nonDiscretionaryEnabled: boolean;
	defaultTaxable: boolean;
}

/** Commission configuration */
export interface CommissionConfig {
	enabled: boolean;
	calculationType: CommissionCalculationType;
	defaultAmount: number;
	requiresSalesInput: boolean;
	/** CRA: commission may be included in overtime base */
	includeInOvertimeBase: boolean;
}

/** Expense category for reimbursement */
export interface ExpenseCategory {
	id: string;
	name: string;
	maxAmount?: number;
	taxable: boolean;
}

/** Expense reimbursement configuration */
export interface ExpenseReimbursementConfig {
	enabled: boolean;
	requireReceipts: boolean;
	maxAmountWithoutApproval?: number;
	categories: ExpenseCategory[];
}

/** Custom earning type */
export interface CustomEarning {
	id: string;
	name: string;
	calculationType: CalculationType;
	amount: number;
	taxable: boolean;
	includeInVacationPay: boolean;
	includeInOvertimeBase: boolean;
	isDefaultEnabled: boolean;
	description?: string;
}

/** Complete earnings configuration for a pay group */
export interface EarningsConfig {
	enabled: boolean;
	bonus: BonusConfig;
	commission: CommissionConfig;
	expenseReimbursement: ExpenseReimbursementConfig;
	allowances: AllowanceConfig[];
	customEarnings: CustomEarning[];
}

// ============================================
// TAXABLE BENEFITS CONFIG TYPES (CRA T4130)
// ============================================

/** Automobile benefit configuration per CRA T4130 */
export interface AutomobileBenefitConfig {
	enabled: boolean;
	// Standby Charge calculation
	vehicleCost: number;
	isLeased: boolean;
	monthlyLeaseCost?: number;
	daysAvailablePerMonth: number;
	// Operating Expense Benefit
	personalKilometers: number;
	totalKilometers?: number;
	useOperatingExpenseBenefit: boolean;
	/** 2025 CRA rate: $0.34/km */
	operatingExpenseRate: number;
	// GST/HST
	includesGstHst: boolean;
	gstHstRate: number;
	// Overrides
	calculatedMonthlyBenefit?: number;
	manualMonthlyOverride?: number;
}

/** Housing benefit configuration */
export interface HousingBenefitConfig {
	enabled: boolean;
	monthlyValue: number;
	includesUtilities: boolean;
	utilitiesValue?: number;
}

/** Travel assistance benefit (northern zones) */
export interface TravelAssistanceBenefitConfig {
	enabled: boolean;
	isPrescribedZone: boolean;
	isIntermediateZone: boolean;
	annualValue: number;
	tripsPerYear: number;
}

/** Board and lodging benefit */
export interface BoardLodgingBenefitConfig {
	enabled: boolean;
	valueType: 'daily' | 'monthly';
	value: number;
	isSubsidized: boolean;
	employeeContribution?: number;
}

/** Group life insurance benefit */
export interface GroupLifeInsuranceBenefitConfig {
	enabled: boolean;
	coverageAmount: number;
	employerPremium: number;
	employeePremium: number;
	useCraRates: boolean;
}

/** Custom taxable benefit */
export interface CustomTaxableBenefit {
	id: string;
	name: string;
	calculationType: 'fixed_monthly' | 'fixed_per_period' | 'annual';
	amount: number;
	subjectToCppEi: boolean;
	isDefaultEnabled: boolean;
	description?: string;
}

/** Complete taxable benefits configuration */
export interface TaxableBenefitsConfig {
	enabled: boolean;
	automobile: AutomobileBenefitConfig;
	housing: HousingBenefitConfig;
	travelAssistance: TravelAssistanceBenefitConfig;
	boardLodging: BoardLodgingBenefitConfig;
	groupLifeInsurance: GroupLifeInsuranceBenefitConfig;
	customBenefits: CustomTaxableBenefit[];
}

// ============================================
// DEDUCTIONS CONFIG TYPES (Replaces customDeductions)
// ============================================

/** Deduction categories with specific tax treatments */
export type DeductionCategory =
	| 'rrsp' // Pre-tax, annual limit
	| 'union_dues' // Pre-tax, 100% tax deductible
	| 'professional_dues' // Pre-tax
	| 'parking' // Post-tax typically
	| 'charitable' // Post-tax, tax receipt
	| 'garnishment' // Post-tax, court-ordered
	| 'loan_repayment' // Post-tax
	| 'equipment' // Post-tax
	| 'other';

/** RRSP deduction configuration */
export interface RrspDeductionConfig {
	enabled: boolean;
	calculationType: CalculationType;
	amount: number;
	employerMatchEnabled: boolean;
	employerMatchPercentage?: number;
	employerMatchMaxAmount?: number;
	respectAnnualLimit: boolean;
	isDefaultEnabled: boolean;
}

/** Union dues configuration */
export interface UnionDuesConfig {
	enabled: boolean;
	calculationType: CalculationType;
	amount: number;
	unionName?: string;
	isDefaultEnabled: boolean;
}

/** Garnishment deduction configuration */
export interface GarnishmentDeductionConfig {
	enabled: boolean;
	allowGarnishments: boolean;
	// Garnishment details stored separately per employee
}

/** Approved charity for donations */
export interface ApprovedCharity {
	id: string;
	name: string;
	registrationNumber: string;
	defaultAmount?: number;
}

/** Charitable donation configuration */
export interface CharitableDonationConfig {
	enabled: boolean;
	approvedCharities: ApprovedCharity[];
	isDefaultEnabled: boolean;
}

/** Custom deduction (enhanced from old CustomDeduction) */
export interface CustomDeduction {
	id: string;
	name: string;
	category: DeductionCategory;
	/** Pre-tax reduces taxable income, post-tax deducted from net pay */
	taxTreatment: DeductionType;
	calculationType: CalculationType;
	amount: number;
	isEmployerContribution: boolean;
	employerAmount?: number;
	annualLimit?: number;
	perPayPeriodLimit?: number;
	isDefaultEnabled: boolean;
	description?: string;
}

/** Complete deductions configuration */
export interface DeductionsConfig {
	enabled: boolean;
	rrsp: RrspDeductionConfig;
	unionDues: UnionDuesConfig;
	garnishments: GarnishmentDeductionConfig;
	charitableDonations: CharitableDonationConfig;
	customDeductions: CustomDeduction[];
}

// Employment type options (expanded to match employee types)
export type EmploymentType = 'full_time' | 'part_time' | 'seasonal' | 'contract' | 'casual';

// Compensation type options
export type CompensationType = 'salary' | 'hourly';

// Period start day options vary by frequency
export type PeriodStartDay =
	| 'sunday'
	| 'monday'
	| 'tuesday'
	| 'wednesday'
	| 'thursday'
	| 'friday'
	| 'saturday'
	| '1st_and_16th'
	| '15th_and_last'
	| '1st_of_month'
	| '15th_of_month'
	| 'last_day_of_month';

// ============================================
// Policy Configuration Interfaces
// ============================================

/**
 * Overtime and bank time (TOIL) policy configuration
 */
export interface OvertimePolicy {
	/** Enable bank time / time off in lieu */
	bankTimeEnabled: boolean;
	/** Bank time accrual rate (1.0 = straight time, 1.5 = time and a half) */
	bankTimeRate: BankTimeRate;
	/** Months before banked time must be paid out */
	bankTimeExpiryMonths: BankTimeExpiryMonths;
	/** Require written agreement with each employee */
	requireWrittenAgreement: boolean;
}

/**
 * WCB/WSIB workers compensation configuration
 */
export interface WcbConfig {
	/** Whether employees in this group are covered by WCB */
	enabled: boolean;
	/** NAICS industry classification code */
	industryClassCode?: string;
	/** Human-readable industry name */
	industryName?: string;
	/** Assessment rate per $100 of insurable earnings */
	assessmentRate: number;
	/** Maximum assessable earnings (varies by province/year) */
	maxAssessableEarnings?: number;
}

/**
 * Individual benefit configuration (health, dental, vision, disability)
 */
export interface BenefitConfig {
	/** Whether this benefit is enabled */
	enabled: boolean;
	/** Employee deduction per pay period */
	employeeDeduction: number;
	/** Employer contribution per pay period */
	employerContribution: number;
	/** Whether employer contribution is a taxable benefit */
	isTaxable: boolean;
}

/**
 * Life insurance configuration (extends BenefitConfig)
 */
export interface LifeInsuranceConfig extends BenefitConfig {
	/** Fixed coverage amount in dollars */
	coverageAmount: number;
	/** Optional multiplier of annual salary for coverage */
	coverageMultiplier?: number;
}

/**
 * Group benefits configuration
 */
export interface GroupBenefits {
	/** Master toggle for group benefits */
	enabled: boolean;
	/** Health insurance */
	health: BenefitConfig;
	/** Dental insurance */
	dental: BenefitConfig;
	/** Vision insurance */
	vision: BenefitConfig;
	/** Life insurance */
	lifeInsurance: LifeInsuranceConfig;
	/** Disability insurance (short/long term) */
	disability: BenefitConfig;
}

// ============================================
// Main Pay Group Interface
// ============================================

/**
 * Pay Group - Policy Template for payroll configuration
 *
 * Note: employeeCount has been removed as Pay Group is now a pure policy template.
 * Employees are associated with Pay Groups during Payroll Run, not stored here.
 */
export interface PayGroup {
	id: string;
	companyId: string;

	// Basic Info
	name: string;
	description?: string;
	payFrequency: PayFrequency;
	employmentType: EmploymentType;
	compensationType: CompensationType;

	// Province (defaults to company province, determines holidays)
	province: Province;

	// Pay Schedule
	nextPeriodEnd: string; // ISO date string (period end, NOT pay date)
	periodStartDay: PeriodStartDay;

	// Leave Policy
	leaveEnabled: boolean;

	// Tax Calculation Method
	/** CRA-approved tax calculation method */
	taxCalculationMethod: TaxCalculationMethod;

	// Overtime & Bank Time Policy
	overtimePolicy: OvertimePolicy;

	// WCB/Workers Compensation
	wcbConfig: WcbConfig;

	// Group Benefits
	groupBenefits: GroupBenefits;

	// === Structured Configurations (CRA Compliant) ===

	/** Earnings configuration (bonus, commission, allowances, custom earnings) */
	earningsConfig: EarningsConfig;

	/** Taxable benefits configuration (automobile, housing, etc.) */
	taxableBenefitsConfig: TaxableBenefitsConfig;

	/** Deductions configuration (RRSP, union dues, custom deductions) */
	deductionsConfig: DeductionsConfig;

	// Status
	/** Soft delete flag. FALSE = inactive (won't appear in payroll run or employee dropdowns) */
	isActive: boolean;

	// Metadata
	createdAt: string;
	updatedAt: string;
}

/**
 * Criteria for matching employees to a pay group
 * Contains only the fields needed for validation
 */
export interface PayGroupMatchCriteria {
	id: string;
	payFrequency: PayFrequency;
	employmentType: EmploymentType;
	compensationType: CompensationType;
	province: Province;
}

/**
 * Form data for creating/editing pay groups (basic info only)
 * Used in the simple create modal
 */
export interface PayGroupFormData {
	name: string;
	description?: string;
	payFrequency: PayFrequency;
	employmentType: EmploymentType;
	compensationType: CompensationType;
	province: Province;
	nextPeriodEnd: string;
	periodStartDay: PeriodStartDay;
	leaveEnabled: boolean;
}

// ============================================
// Default Values & Factory Functions
// ============================================

/**
 * Default tax calculation method
 */
export const DEFAULT_TAX_CALCULATION_METHOD: TaxCalculationMethod = 'annualization';

/**
 * Tax calculation method display information
 */
export const TAX_CALCULATION_METHOD_INFO: Record<
	TaxCalculationMethod,
	{
		label: string;
		description: string;
		badge?: string;
		disabled?: boolean;
	}
> = {
	annualization: {
		label: 'Annualization (Option 1)',
		description: 'Each pay period calculated independently. Best for stable salary income.'
	},
	cumulative_averaging: {
		label: 'Cumulative Averaging (Option 2)',
		description:
			'Considers YTD earnings for more accurate withholding. Best for variable income (commissions, bonuses).',
		badge: 'Coming Soon',
		disabled: true
	}
};

/**
 * Default overtime policy
 */
export const DEFAULT_OVERTIME_POLICY: OvertimePolicy = {
	bankTimeEnabled: false,
	bankTimeRate: 1.5,
	bankTimeExpiryMonths: 3,
	requireWrittenAgreement: true
};

/**
 * Default WCB config (disabled)
 */
export const DEFAULT_WCB_CONFIG: WcbConfig = {
	enabled: false,
	assessmentRate: 0
};

/**
 * Default benefit config (disabled)
 */
export const DEFAULT_BENEFIT_CONFIG: BenefitConfig = {
	enabled: false,
	employeeDeduction: 0,
	employerContribution: 0,
	isTaxable: false
};

/**
 * Default life insurance config (disabled)
 */
export const DEFAULT_LIFE_INSURANCE_CONFIG: LifeInsuranceConfig = {
	...DEFAULT_BENEFIT_CONFIG,
	coverageAmount: 0
};

/**
 * Default group benefits (all disabled)
 */
export const DEFAULT_GROUP_BENEFITS: GroupBenefits = {
	enabled: false,
	health: { ...DEFAULT_BENEFIT_CONFIG },
	dental: { ...DEFAULT_BENEFIT_CONFIG },
	vision: { ...DEFAULT_BENEFIT_CONFIG },
	lifeInsurance: { ...DEFAULT_LIFE_INSURANCE_CONFIG },
	disability: { ...DEFAULT_BENEFIT_CONFIG }
};

// ============================================
// Default Values for Structured Configurations
// ============================================

/**
 * Default earnings configuration
 */
export const DEFAULT_EARNINGS_CONFIG: EarningsConfig = {
	enabled: false,
	bonus: {
		enabled: false,
		discretionaryEnabled: false,
		nonDiscretionaryEnabled: false,
		defaultTaxable: true
	},
	commission: {
		enabled: false,
		calculationType: 'fixed',
		defaultAmount: 0,
		requiresSalesInput: false,
		includeInOvertimeBase: false
	},
	expenseReimbursement: {
		enabled: false,
		requireReceipts: true,
		categories: []
	},
	allowances: [],
	customEarnings: []
};

/**
 * Default taxable benefits configuration
 */
export const DEFAULT_TAXABLE_BENEFITS_CONFIG: TaxableBenefitsConfig = {
	enabled: false,
	automobile: {
		enabled: false,
		vehicleCost: 0,
		isLeased: false,
		daysAvailablePerMonth: 30,
		personalKilometers: 0,
		useOperatingExpenseBenefit: false,
		operatingExpenseRate: 0.34, // 2025 CRA rate
		includesGstHst: true,
		gstHstRate: 0.13
	},
	housing: {
		enabled: false,
		monthlyValue: 0,
		includesUtilities: false
	},
	travelAssistance: {
		enabled: false,
		isPrescribedZone: false,
		isIntermediateZone: false,
		annualValue: 0,
		tripsPerYear: 2
	},
	boardLodging: {
		enabled: false,
		valueType: 'daily',
		value: 0,
		isSubsidized: false
	},
	groupLifeInsurance: {
		enabled: false,
		coverageAmount: 0,
		employerPremium: 0,
		employeePremium: 0,
		useCraRates: true
	},
	customBenefits: []
};

/**
 * Default deductions configuration
 */
export const DEFAULT_DEDUCTIONS_CONFIG: DeductionsConfig = {
	enabled: true,
	rrsp: {
		enabled: false,
		calculationType: 'fixed',
		amount: 0,
		employerMatchEnabled: false,
		respectAnnualLimit: true,
		isDefaultEnabled: false
	},
	unionDues: {
		enabled: false,
		calculationType: 'fixed',
		amount: 0,
		isDefaultEnabled: false
	},
	garnishments: {
		enabled: true,
		allowGarnishments: true
	},
	charitableDonations: {
		enabled: false,
		approvedCharities: [],
		isDefaultEnabled: false
	},
	customDeductions: []
};

/**
 * Create a new PayGroup with default values
 * @param companyId - The company ID
 * @param companyProvince - The company's province (used as default for pay group)
 */
export function createDefaultPayGroup(
	companyId: string,
	companyProvince: Province = 'SK'
): Omit<PayGroup, 'id' | 'createdAt' | 'updatedAt'> {
	return {
		companyId,
		name: '',
		payFrequency: 'bi_weekly',
		employmentType: 'full_time',
		compensationType: 'salary',
		province: companyProvince,
		nextPeriodEnd: '',
		periodStartDay: 'monday',
		leaveEnabled: true,
		taxCalculationMethod: DEFAULT_TAX_CALCULATION_METHOD,
		overtimePolicy: { ...DEFAULT_OVERTIME_POLICY },
		wcbConfig: { ...DEFAULT_WCB_CONFIG },
		groupBenefits: { ...DEFAULT_GROUP_BENEFITS },
		earningsConfig: { ...DEFAULT_EARNINGS_CONFIG },
		taxableBenefitsConfig: { ...DEFAULT_TAXABLE_BENEFITS_CONFIG },
		deductionsConfig: { ...DEFAULT_DEDUCTIONS_CONFIG },
		isActive: true
	};
}

/**
 * Pay frequency display information
 */
export const PAY_FREQUENCY_INFO: Record<
	PayFrequency,
	{
		label: string;
		description: string;
		periodsPerYear: number;
	}
> = {
	weekly: {
		label: 'Weekly',
		description: 'Paid every week (52 pay periods/year)',
		periodsPerYear: 52
	},
	bi_weekly: {
		label: 'Bi-weekly',
		description: 'Paid every two weeks (26 pay periods/year)',
		periodsPerYear: 26
	},
	semi_monthly: {
		label: 'Semi-monthly',
		description: 'Paid twice a month (24 pay periods/year)',
		periodsPerYear: 24
	},
	monthly: {
		label: 'Monthly',
		description: 'Paid once a month (12 pay periods/year)',
		periodsPerYear: 12
	}
};

/**
 * Employment type display information
 */
export const EMPLOYMENT_TYPE_INFO: Record<
	EmploymentType,
	{
		label: string;
		description: string;
	}
> = {
	full_time: {
		label: 'Full-time',
		description: 'Full-time employees'
	},
	part_time: {
		label: 'Part-time',
		description: 'Part-time employees'
	},
	seasonal: {
		label: 'Seasonal',
		description: 'Seasonal employees'
	},
	contract: {
		label: 'Contract',
		description: 'Contract workers'
	},
	casual: {
		label: 'Casual',
		description: 'Casual/on-call workers'
	}
};

/**
 * Compensation type display information
 */
export const COMPENSATION_TYPE_INFO: Record<
	CompensationType,
	{
		label: string;
		description: string;
	}
> = {
	salary: {
		label: 'Salary',
		description: 'Annual salary employees'
	},
	hourly: {
		label: 'Hourly',
		description: 'Hourly rate employees'
	}
};

/**
 * Period start day options by pay frequency
 */
export const PERIOD_START_DAY_OPTIONS: Record<
	PayFrequency,
	Array<{ value: PeriodStartDay; label: string }>
> = {
	weekly: [
		{ value: 'sunday', label: 'Sunday' },
		{ value: 'monday', label: 'Monday' },
		{ value: 'tuesday', label: 'Tuesday' },
		{ value: 'wednesday', label: 'Wednesday' },
		{ value: 'thursday', label: 'Thursday' },
		{ value: 'friday', label: 'Friday' },
		{ value: 'saturday', label: 'Saturday' }
	],
	bi_weekly: [
		{ value: 'sunday', label: 'Sunday' },
		{ value: 'monday', label: 'Monday' },
		{ value: 'tuesday', label: 'Tuesday' },
		{ value: 'wednesday', label: 'Wednesday' },
		{ value: 'thursday', label: 'Thursday' },
		{ value: 'friday', label: 'Friday' },
		{ value: 'saturday', label: 'Saturday' }
	],
	semi_monthly: [
		{ value: '1st_and_16th', label: '1st and 16th' },
		{ value: '15th_and_last', label: '15th and last day' }
	],
	monthly: [
		{ value: '1st_of_month', label: '1st of month' },
		{ value: '15th_of_month', label: '15th of month' },
		{ value: 'last_day_of_month', label: 'Last day of month' }
	]
};

/**
 * Get default period start day for a given frequency
 */
export function getDefaultPeriodStartDay(frequency: PayFrequency): PeriodStartDay {
	switch (frequency) {
		case 'weekly':
		case 'bi_weekly':
			return 'monday';
		case 'semi_monthly':
			return '1st_and_16th';
		case 'monthly':
			return '1st_of_month';
	}
}

/**
 * Format pay group leave status for display
 */
export function formatLeaveStatus(leaveEnabled: boolean, employmentType: EmploymentType): string {
	if (!leaveEnabled) {
		return 'Disabled';
	}
	if (employmentType === 'part_time') {
		return 'Enabled (4% vacation pay accrual)';
	}
	return 'Enabled (follows provincial standards)';
}

// ============================================
// Display Helpers for Policy Configuration
// ============================================

/**
 * Bank time rate display labels
 */
export const BANK_TIME_RATE_LABELS: Record<BankTimeRate, string> = {
	1.0: '1:1 (Straight time)',
	1.5: '1.5:1 (Time and a half)'
};

/**
 * Bank time expiry display labels
 */
export const BANK_TIME_EXPIRY_LABELS: Record<BankTimeExpiryMonths, string> = {
	3: '3 months',
	6: '6 months',
	12: '12 months'
};

/**
 * Deduction type display labels
 */
export const DEDUCTION_TYPE_LABELS: Record<DeductionType, { label: string; description: string }> =
	{
		pre_tax: {
			label: 'Pre-tax',
			description: 'Deducted before tax calculation, reduces taxable income'
		},
		post_tax: {
			label: 'Post-tax',
			description: 'Deducted after tax calculation, from net pay'
		}
	};

/**
 * Benefit type labels for display
 */
export const BENEFIT_TYPE_LABELS = {
	health: { label: 'Health Insurance', icon: 'fa-hospital' },
	dental: { label: 'Dental Insurance', icon: 'fa-tooth' },
	vision: { label: 'Vision Insurance', icon: 'fa-eye' },
	lifeInsurance: { label: 'Life Insurance', icon: 'fa-shield-alt' },
	disability: { label: 'Disability Insurance', icon: 'fa-wheelchair' }
} as const;

/**
 * Count enabled benefits in a GroupBenefits config
 */
export function countEnabledBenefits(benefits: GroupBenefits): number {
	if (!benefits.enabled) return 0;
	let count = 0;
	if (benefits.health.enabled) count++;
	if (benefits.dental.enabled) count++;
	if (benefits.vision.enabled) count++;
	if (benefits.lifeInsurance.enabled) count++;
	if (benefits.disability.enabled) count++;
	return count;
}

/**
 * Get summary of enabled policies for a pay group (for badges display)
 */
export function getPayGroupPolicySummary(payGroup: PayGroup): {
	wcb: boolean;
	benefits: boolean;
	bankTime: boolean;
} {
	return {
		wcb: payGroup.wcbConfig.enabled,
		benefits: payGroup.groupBenefits.enabled,
		bankTime: payGroup.overtimePolicy.bankTimeEnabled
	};
}

// ============================================
// Pay Date Calculation
// ============================================

/**
 * Maximum days after period end to pay employees (by province)
 * Saskatchewan: must pay within 6 days of period end
 */
export const PAY_DATE_DELAY_DAYS: Record<string, number> = {
	SK: 6,
	ON: 7,
	BC: 8,
	AB: 10,
	MB: 10,
	QC: 16,
	NB: 5,
	NS: 5,
	PE: 7,
	NL: 7,
	NT: 10,
	NU: 10,
	YT: 10
};

export const DEFAULT_PAY_DATE_DELAY = 7;

/**
 * Calculate pay date from period end based on province regulations.
 * Saskatchewan law requires paying employees within 6 days of pay period end.
 *
 * @param periodEnd - Period end date (ISO string or Date)
 * @param province - Two-letter province code (default: "SK")
 * @returns Pay date as ISO string
 */
export function calculatePayDate(periodEnd: string | Date, province: string = 'SK'): string {
	const endDate = typeof periodEnd === 'string' ? new Date(periodEnd) : periodEnd;
	const delayDays = PAY_DATE_DELAY_DAYS[province] ?? DEFAULT_PAY_DATE_DELAY;
	const payDate = new Date(endDate);
	payDate.setDate(payDate.getDate() + delayDays);
	return payDate.toISOString().split('T')[0];
}

/**
 * Format pay date for display with province info
 */
export function formatPayDateInfo(periodEnd: string, province: string = 'SK'): string {
	const payDate = calculatePayDate(periodEnd, province);
	const delay = PAY_DATE_DELAY_DAYS[province] ?? DEFAULT_PAY_DATE_DELAY;
	return `${payDate} (${delay} days after period end)`;
}

/**
 * Pay Group Types for BeanFlow Payroll
 *
 * Pay Groups are "Policy Templates" that define payroll configuration including:
 * - Pay schedule (frequency, dates)
 * - Statutory deduction defaults (CPP/EI exemptions)
 * - Overtime & bank time policies
 * - WCB/workers compensation configuration
 * - Group benefits (health, dental, vision, life, disability)
 * - Custom deductions
 */

// Pay frequency options
export type PayFrequency = 'weekly' | 'bi_weekly' | 'semi_monthly' | 'monthly';

// Bank time rate options (varies by province)
export type BankTimeRate = 1.0 | 1.5;

// Bank time expiry options (in months)
export type BankTimeExpiryMonths = 3 | 6 | 12;

// Deduction type for custom deductions
export type DeductionType = 'pre_tax' | 'post_tax';

// Calculation type for deductions
export type CalculationType = 'fixed' | 'percentage';

// Employment type options
export type EmploymentType = 'full_time' | 'part_time';

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
 * Statutory deduction defaults for new employees in this pay group
 */
export interface StatutoryDefaults {
	/** CPP default exemption for new employees (e.g., for 65+ employees) */
	cppExemptByDefault: boolean;
	/** CPP2 exemption for employees with multiple jobs who've hit contribution ceiling */
	cpp2ExemptByDefault: boolean;
	/** EI exemption for related parties or >40% shareholders */
	eiExemptByDefault: boolean;
}

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

/**
 * Custom deduction item (e.g., parking, union dues, RRSP)
 */
export interface CustomDeduction {
	id: string;
	/** Display name */
	name: string;
	/** Pre-tax reduces taxable income, post-tax deducted from net pay */
	type: DeductionType;
	/** Fixed amount or percentage of gross */
	calculationType: CalculationType;
	/** Amount (dollars if fixed, percentage if percentage) */
	amount: number;
	/** Whether employer also contributes (e.g., RRSP matching) */
	isEmployerContribution: boolean;
	/** Employer contribution amount (if applicable) */
	employerAmount?: number;
	/** Whether new employees get this deduction by default */
	isDefaultEnabled: boolean;
	/** Optional description */
	description?: string;
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

	// Pay Schedule
	nextPayDate: string; // ISO date string
	periodStartDay: PeriodStartDay;

	// Leave Policy
	leaveEnabled: boolean;

	// Statutory Deduction Defaults
	statutoryDefaults: StatutoryDefaults;

	// Overtime & Bank Time Policy
	overtimePolicy: OvertimePolicy;

	// WCB/Workers Compensation
	wcbConfig: WcbConfig;

	// Group Benefits
	groupBenefits: GroupBenefits;

	// Custom Deductions
	customDeductions: CustomDeduction[];

	// Metadata
	createdAt: string;
	updatedAt: string;
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
	nextPayDate: string;
	periodStartDay: PeriodStartDay;
	leaveEnabled: boolean;
}

// ============================================
// Default Values & Factory Functions
// ============================================

/**
 * Default statutory defaults (no exemptions)
 */
export const DEFAULT_STATUTORY_DEFAULTS: StatutoryDefaults = {
	cppExemptByDefault: false,
	cpp2ExemptByDefault: false,
	eiExemptByDefault: false
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

/**
 * Create a new PayGroup with default values
 */
export function createDefaultPayGroup(companyId: string): Omit<PayGroup, 'id' | 'createdAt' | 'updatedAt'> {
	return {
		companyId,
		name: '',
		payFrequency: 'bi_weekly',
		employmentType: 'full_time',
		nextPayDate: '',
		periodStartDay: 'monday',
		leaveEnabled: true,
		statutoryDefaults: { ...DEFAULT_STATUTORY_DEFAULTS },
		overtimePolicy: { ...DEFAULT_OVERTIME_POLICY },
		wcbConfig: { ...DEFAULT_WCB_CONFIG },
		groupBenefits: { ...DEFAULT_GROUP_BENEFITS },
		customDeductions: []
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
export function formatLeaveStatus(
	leaveEnabled: boolean,
	employmentType: EmploymentType
): string {
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
export const DEDUCTION_TYPE_LABELS: Record<DeductionType, { label: string; description: string }> = {
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
	cppExempt: boolean;
	cpp2Exempt: boolean;
	eiExempt: boolean;
} {
	return {
		wcb: payGroup.wcbConfig.enabled,
		benefits: payGroup.groupBenefits.enabled,
		bankTime: payGroup.overtimePolicy.bankTimeEnabled,
		cppExempt: payGroup.statutoryDefaults.cppExemptByDefault,
		cpp2Exempt: payGroup.statutoryDefaults.cpp2ExemptByDefault,
		eiExempt: payGroup.statutoryDefaults.eiExemptByDefault
	};
}

/**
 * Company and settings types for Payroll UI
 *
 * Updated: 2025-12-10
 * - Added CompanyProfile interface (split from CompanySettings)
 * - Added BookkeepingSyncStatus interface
 * - Added BookkeepingLedger interface
 * - CompanySettings kept for backward compatibility
 */

import type { PayFrequency, Province } from './employee';

// Remitter types based on CRA classification
export type RemitterType = 'quarterly' | 'regular' | 'threshold_1' | 'threshold_2';

export const REMITTER_TYPE_INFO: Record<RemitterType, {
	label: string;
	description: string;
	frequency: string;
	amwaRange: string;
	periodsPerYear: number;
}> = {
	quarterly: {
		label: 'Quarterly',
		description: 'Remit 4 times per year',
		frequency: '4 times/year',
		amwaRange: '< $3,000',
		periodsPerYear: 4
	},
	regular: {
		label: 'Regular (Monthly)',
		description: 'Remit by 15th of following month',
		frequency: 'Monthly',
		amwaRange: '$3,000 - $24,999',
		periodsPerYear: 12
	},
	threshold_1: {
		label: 'Accelerated Threshold 1',
		description: 'Remit twice per month',
		frequency: 'Twice monthly',
		amwaRange: '$25,000 - $99,999',
		periodsPerYear: 24
	},
	threshold_2: {
		label: 'Accelerated Threshold 2',
		description: 'Remit up to 4 times per month',
		frequency: 'Up to 4x monthly',
		amwaRange: '>= $100,000',
		periodsPerYear: 48
	}
};

export interface CompanySettings {
	id: string;
	userId: string;

	// Company Information
	companyName: string;
	businessNumber: string;           // 9-digit CRA BN
	payrollAccountNumber: string;     // 15-char (e.g., 123456789RP0001)
	province: Province;               // Company's primary province

	// Address fields (for paystub)
	addressStreet?: string | null;
	addressCity?: string | null;
	addressPostalCode?: string | null;

	// Logo (for paystub branding)
	logoUrl?: string | null;

	// CRA Remittance
	remitterType: RemitterType;

	// Payroll Settings
	payFrequency: PayFrequency;
	nextPayDate: string;              // ISO date
	autoCalculateDeductions: boolean;
	sendPaystubEmails: boolean;

	// Bookkeeping Integration
	bookkeepingLedgerId: string | null;
	bookkeepingConnectedAt: string | null;

	// Metadata
	createdAt: string;
	updatedAt: string;
}

/**
 * Calculate next remittance due date based on remitter type
 */
export function calculateNextDueDate(remitterType: RemitterType, referenceDate: Date = new Date()): Date {
	const year = referenceDate.getFullYear();
	const month = referenceDate.getMonth();
	const day = referenceDate.getDate();

	switch (remitterType) {
		case 'quarterly': {
			// Due 15th of month after quarter end (Apr 15, Jul 15, Oct 15, Jan 15)
			const quarterEndMonths = [2, 5, 8, 11]; // Mar, Jun, Sep, Dec (0-indexed)
			for (const qEnd of quarterEndMonths) {
				if (month <= qEnd) {
					const dueMonth = qEnd + 1;
					const dueYear = dueMonth > 11 ? year + 1 : year;
					return new Date(dueYear, dueMonth % 12, 15);
				}
			}
			// Next year Q1
			return new Date(year + 1, 0, 15);
		}

		case 'regular': {
			// Due 15th of following month
			const dueMonth = month + 1;
			const dueYear = dueMonth > 11 ? year + 1 : year;
			return new Date(dueYear, dueMonth % 12, 15);
		}

		case 'threshold_1': {
			// Twice monthly: 25th for 1st-15th, 10th of next month for 16th-end
			if (day <= 15) {
				return new Date(year, month, 25);
			} else {
				const dueMonth = month + 1;
				const dueYear = dueMonth > 11 ? year + 1 : year;
				return new Date(dueYear, dueMonth % 12, 10);
			}
		}

		case 'threshold_2': {
			// Complex - simplified to weekly for now
			const dueDate = new Date(referenceDate);
			dueDate.setDate(day + 7);
			return dueDate;
		}

		default:
			return new Date(year, month + 1, 15);
	}
}

/**
 * Format due date with days remaining
 */
export function formatDueDateWithDays(dueDate: Date): { formatted: string; daysRemaining: number; isOverdue: boolean } {
	const today = new Date();
	today.setHours(0, 0, 0, 0);

	const due = new Date(dueDate);
	due.setHours(0, 0, 0, 0);

	const diffMs = due.getTime() - today.getTime();
	const daysRemaining = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

	const formatted = dueDate.toLocaleDateString('en-CA', {
		year: 'numeric',
		month: 'long',
		day: 'numeric'
	});

	return {
		formatted,
		daysRemaining,
		isOverdue: daysRemaining < 0
	};
}

// ============================================
// New Types for Company Page Tab Refactoring
// ============================================

/**
 * Company Profile (Tab 1: Profile)
 * Contains company information, CRA remittance config, and preferences
 */
export interface CompanyProfile {
	id: string;
	userId: string;

	// Company Information
	companyName: string;
	businessNumber: string;           // 9-digit CRA BN
	payrollAccountNumber: string;     // 15-char (e.g., 123456789RP0001)
	province: Province;               // Company's primary province

	// Address fields (for paystub)
	addressStreet?: string | null;
	addressCity?: string | null;
	addressPostalCode?: string | null;

	// Logo (for paystub branding)
	logoUrl?: string | null;

	// CRA Remittance
	remitterType: RemitterType;

	// Preferences (previously in Payroll Settings)
	autoCalculateDeductions: boolean;
	sendPaystubEmails: boolean;

	// Bookkeeping Integration
	bookkeepingLedgerId: string | null;
	bookkeepingLedgerName: string | null;
	bookkeepingConnectedAt: string | null;

	// Metadata
	createdAt: string;
	updatedAt: string;
}

/**
 * Bookkeeping ledger option for connection dropdown
 */
export interface BookkeepingLedger {
	id: string;
	name: string;
	lastUpdated: string;
}

/**
 * Bookkeeping sync status (Tab 3: Integration)
 */
export interface BookkeepingSyncStatus {
	lastSyncAt: string | null;
	entriesCreated: number;
	status: 'synced' | 'pending' | 'error';
	errorMessage?: string;
}

/**
 * Account mapping for bookkeeping integration
 */
export interface AccountMapping {
	payrollType: string;
	account: string;
}

/**
 * Default account mappings for bookkeeping integration
 */
export const DEFAULT_ACCOUNT_MAPPINGS: AccountMapping[] = [
	{ payrollType: 'Salary Expense', account: 'Expenses:Payroll:Salaries' },
	{ payrollType: 'CPP Expense', account: 'Expenses:Payroll:CPP-Employer' },
	{ payrollType: 'EI Expense', account: 'Expenses:Payroll:EI-Employer' },
	{ payrollType: 'CPP Payable', account: 'Liabilities:Payroll:CPP-Payable' },
	{ payrollType: 'EI Payable', account: 'Liabilities:Payroll:EI-Payable' },
	{ payrollType: 'Tax Payable', account: 'Liabilities:Payroll:Tax-Payable' }
];

/**
 * Province options for dropdown
 */
export const PROVINCES: Array<{ code: Province; name: string }> = [
	{ code: 'AB', name: 'Alberta' },
	{ code: 'BC', name: 'British Columbia' },
	{ code: 'MB', name: 'Manitoba' },
	{ code: 'NB', name: 'New Brunswick' },
	{ code: 'NL', name: 'Newfoundland and Labrador' },
	{ code: 'NS', name: 'Nova Scotia' },
	{ code: 'NT', name: 'Northwest Territories' },
	{ code: 'NU', name: 'Nunavut' },
	{ code: 'ON', name: 'Ontario' },
	{ code: 'PE', name: 'Prince Edward Island' },
	// Note: Quebec (QC) is excluded - requires separate payroll system
	{ code: 'SK', name: 'Saskatchewan' },
	{ code: 'YT', name: 'Yukon' }
];

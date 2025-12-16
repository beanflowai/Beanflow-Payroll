/**
 * Employee Portal Type Definitions
 * Types for the Employee Self-Service Portal (Phase 2)
 */

// ============================================================================
// Portal Access & Status
// ============================================================================

export type PortalStatus = 'not_set' | 'invited' | 'active' | 'disabled';

export interface EmployeePortalAccess {
	status: PortalStatus;
	invitedAt?: string;
	lastLoginAt?: string;
	email: string;
}

// ============================================================================
// Authentication
// ============================================================================

export interface MagicLinkToken {
	token: string;
	employeeId: string;
	companyId: string;
	email: string;
	expiresAt: string;
	usedAt?: string;
}

export interface MagicLinkRequest {
	email: string;
}

export interface MagicLinkResponse {
	success: boolean;
	message: string;
}

export interface VerifyTokenResponse {
	success: boolean;
	employeeId?: string;
	companyId?: string;
	error?: string;
}

// ============================================================================
// Employee Profile
// ============================================================================

export interface EmployeeAddress {
	street: string;
	city: string;
	province: string;
	postalCode: string;
}

export interface EmergencyContact {
	name: string;
	relationship: string;
	phone: string;
}

export interface EmployeePortalProfile {
	id: string;
	firstName: string;
	lastName: string;
	email: string;
	phone?: string;

	// Address
	address: EmployeeAddress;

	// Emergency contact
	emergencyContact?: EmergencyContact;

	// Tax info (partially masked)
	sin: string; // Masked: ***-***-789
	federalClaimAmount: number;
	provincialClaimAmount: number;
	additionalTaxPerPeriod: number;

	// Bank info (partially masked)
	bankName: string;
	transitNumber: string;
	institutionNumber: string;
	accountNumber: string; // Masked: ****4567

	// Employment (read-only)
	hireDate: string;
	jobTitle?: string;
	provinceOfEmployment: string;
}

// ============================================================================
// Profile Edit Forms
// ============================================================================

export interface PersonalInfoFormData {
	phone: string;
	address: EmployeeAddress;
	emergencyContact: EmergencyContact;
}

export interface TaxInfoFormData {
	sin?: string;
	federalClaimAmount: number;
	provincialClaimAmount: number;
	additionalTaxPerPeriod: number;
	useBasicFederalAmount: boolean;
	useBasicProvincialAmount: boolean;
}

export interface BankInfoFormData {
	bankName: string;
	transitNumber: string;
	institutionNumber: string;
	accountNumber: string;
	voidChequeFile?: File;
}

// ============================================================================
// Profile Change Requests
// ============================================================================

export type ChangeRequestType = 'personal_info' | 'tax_info' | 'bank_info';
export type ChangeRequestStatus = 'pending' | 'approved' | 'rejected';

export interface ProfileChangeRequest {
	id: string;
	employeeId: string;
	employeeName: string;
	changeType: ChangeRequestType;
	submittedAt: string;
	status: ChangeRequestStatus;
	currentValues: Record<string, unknown>;
	requestedValues: Record<string, unknown>;
	attachments?: string[];
	reviewedAt?: string;
	reviewedBy?: string;
	rejectionReason?: string;
}

// ============================================================================
// Paystubs
// ============================================================================

export interface PaystubEarning {
	type: string;
	hours?: number;
	amount: number;
}

export interface PaystubDeduction {
	type: string;
	amount: number;
}

export interface PaystubYTD {
	grossEarnings: number;
	cppPaid: number;
	eiPaid: number;
	taxPaid: number;
}

export interface PaystubSummary {
	id: string;
	payDate: string;
	payPeriodStart: string;
	payPeriodEnd: string;
	grossPay: number;
	totalDeductions: number;
	netPay: number;
}

export interface PaystubDetail extends PaystubSummary {
	companyName: string;
	companyAddress: string;
	employeeName: string;
	earnings: PaystubEarning[];
	deductions: PaystubDeduction[];
	ytd: PaystubYTD;
}

// ============================================================================
// Leave Balances
// ============================================================================

export interface LeaveHistoryEntry {
	date: string;
	endDate?: string;
	type: 'vacation' | 'sick';
	hours: number;
	balanceAfterHours: number;
	balanceAfterDollars?: number;
}

export interface EmployeeLeaveBalance {
	vacationHours: number;
	vacationDollars: number;
	vacationAccrualRate: number;
	vacationYtdAccrued: number;
	vacationYtdUsed: number;

	sickHoursRemaining: number;
	sickHoursAllowance: number;
	sickHoursUsedThisYear: number;
}

// ============================================================================
// Documents
// ============================================================================

export interface TaxDocument {
	id: string;
	type: 'T4' | 'T4A' | 'RL-1';
	year: number;
	generatedAt: string;
	downloadUrl: string;
}

// ============================================================================
// Dashboard Summary
// ============================================================================

export interface PortalDashboardSummary {
	lastPaystub: PaystubSummary | null;
	vacationBalance: {
		hours: number;
		dollars: number;
	};
	sickLeaveBalance: {
		hours: number;
	};
	pendingChangeRequests: number;
}

// ============================================================================
// Employer-Side Types
// ============================================================================

export interface EmployeeWithPortalStatus {
	id: string;
	firstName: string;
	lastName: string;
	email: string;
	status: 'active' | 'inactive' | 'terminated';
	portalStatus: PortalStatus;
	portalInvitedAt?: string;
	portalLastLoginAt?: string;
}

export interface BulkInviteRequest {
	employeeIds: string[];
}

export interface BulkInviteResponse {
	success: boolean;
	invitedCount: number;
	errors?: Array<{
		employeeId: string;
		error: string;
	}>;
}

// ============================================================================
// Constants
// ============================================================================

export const CANADIAN_BANKS = [
	{ code: '001', name: 'Bank of Montreal (BMO)' },
	{ code: '002', name: 'Bank of Nova Scotia (Scotiabank)' },
	{ code: '003', name: 'Royal Bank of Canada (RBC)' },
	{ code: '004', name: 'TD Canada Trust' },
	{ code: '006', name: 'National Bank of Canada' },
	{ code: '010', name: 'CIBC' },
	{ code: '016', name: 'HSBC Bank Canada' },
	{ code: '030', name: 'Canadian Western Bank' },
	{ code: '039', name: 'Laurentian Bank of Canada' },
	{ code: '219', name: 'ATB Financial' },
	{ code: '614', name: 'Tangerine' },
	{ code: '815', name: 'Desjardins' },
	{ code: '879', name: 'EQ Bank' },
	{ code: '000', name: 'Other' }
] as const;

export const CANADIAN_PROVINCES = [
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
	{ code: 'QC', name: 'Quebec' },
	{ code: 'SK', name: 'Saskatchewan' },
	{ code: 'YT', name: 'Yukon' }
] as const;

export const RELATIONSHIP_OPTIONS = [
	'Spouse',
	'Partner',
	'Parent',
	'Child',
	'Sibling',
	'Friend',
	'Other'
] as const;

export const TAX_CONSTANTS_2025 = {
	federalBPA: 16129,
	provincialBPA: {
		AB: 21003,
		BC: 12932,
		MB: 15780,
		NB: 13396,
		NL: 10818,
		NS: 11481,
		NT: 17373,
		NU: 18767,
		ON: 12399,
		PE: 14250,
		QC: 18056,
		SK: 18491,
		YT: 16129
	}
} as const;

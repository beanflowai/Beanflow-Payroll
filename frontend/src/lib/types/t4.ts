/**
 * T4 Statement of Remuneration Paid - Type Definitions
 *
 * Frontend types matching backend T4 models for year-end payroll processing.
 */

/**
 * T4 slip generation status
 */
export type T4Status = 'draft' | 'generated' | 'amended' | 'filed';

/**
 * T4 status display information
 */
export const T4_STATUS_INFO: Record<T4Status, { label: string; icon: string; colorClass: string }> =
	{
		draft: {
			label: 'Draft',
			icon: 'edit',
			colorClass: 'bg-surface-100 text-surface-600'
		},
		generated: {
			label: 'Generated',
			icon: 'check-circle',
			colorClass: 'bg-success-100 text-success-700'
		},
		amended: {
			label: 'Amended',
			icon: 'edit',
			colorClass: 'bg-warning-100 text-warning-700'
		},
		filed: {
			label: 'Filed',
			icon: 'paper-plane',
			colorClass: 'bg-primary-100 text-primary-700'
		}
	};

/**
 * Summary view of a T4 slip for listing
 */
export interface T4SlipSummary {
	id: string;
	employeeId: string;
	employeeName: string;
	sinMasked: string;
	box14EmploymentIncome: number;
	box22IncomeTaxDeducted: number;
	status: T4Status;
	pdfAvailable: boolean;
}

/**
 * Response for listing T4 slips
 */
export interface T4SlipListResponse {
	taxYear: number;
	totalCount: number;
	slips: T4SlipSummary[];
}

/**
 * Request to generate T4 slips
 */
export interface T4GenerationRequest {
	taxYear: number;
	employeeIds?: string[];
	regenerate?: boolean;
}

/**
 * Response from T4 generation
 */
export interface T4GenerationResponse {
	success: boolean;
	taxYear: number;
	slipsGenerated: number;
	slipsSkipped: number;
	errors: Array<{ employeeId?: string; message: string }>;
	message?: string;
}

/**
 * T4 Summary totals
 */
export interface T4SummaryData {
	companyId: string;
	taxYear: number;
	employerName: string;
	employerAccountNumber: string;
	employerAddressLine1?: string;
	employerCity?: string;
	employerProvince?: string;
	employerPostalCode?: string;
	totalNumberOfT4Slips: number;
	totalEmploymentIncome: number;
	totalCppContributions: number;
	totalCpp2Contributions: number;
	totalEiPremiums: number;
	totalIncomeTaxDeducted: number;
	totalUnionDues: number;
	totalCppEmployer: number;
	totalEiEmployer: number;
	remittanceDifference: number;
	status: T4Status;
	pdfStorageKey?: string;
	xmlStorageKey?: string;
	generatedAt?: string;
	// CRA Submission tracking
	craConfirmationNumber?: string;
	submittedAt?: string;
	submittedBy?: string;
	submissionNotes?: string;
}

/**
 * Response containing T4 Summary data
 */
export interface T4SummaryResponse {
	success: boolean;
	summary?: T4SummaryData;
	message?: string;
}

/**
 * Available tax years for T4 generation
 */
export function getAvailableTaxYears(): number[] {
	const currentYear = new Date().getFullYear();
	// Include current year and previous 2 years
	return [currentYear, currentYear - 1, currentYear - 2];
}

// =============================================================================
// CRA Submission Types
// =============================================================================

/**
 * Validation error from T4 XML validation
 */
export interface T4ValidationError {
	code: string;
	message: string;
	field?: string;
}

/**
 * Validation warning from T4 XML validation
 */
export interface T4ValidationWarning {
	code: string;
	message: string;
	field?: string;
}

/**
 * Result of T4 XML validation
 */
export interface T4ValidationResult {
	isValid: boolean;
	errors: T4ValidationError[];
	warnings: T4ValidationWarning[];
	craPortalUrl: string;
}

/**
 * Response from T4 validation endpoint
 */
export interface T4ValidationResponse {
	success: boolean;
	validation?: T4ValidationResult;
	message?: string;
}

/**
 * Input for recording CRA submission
 */
export interface RecordSubmissionInput {
	confirmationNumber: string;
	submissionNotes?: string;
}

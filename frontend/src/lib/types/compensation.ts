/**
 * Compensation History types for tracking salary/rate changes
 */

export type CompensationType = 'salary' | 'hourly';

/**
 * Compensation history record from database
 */
export interface CompensationHistory {
	id: string;
	employeeId: string;
	compensationType: CompensationType;
	annualSalary: number | null;
	hourlyRate: number | null;
	effectiveDate: string; // YYYY-MM-DD
	endDate: string | null; // YYYY-MM-DD, null = currently active
	changeReason: string | null;
	createdAt: string;
}

/**
 * Request payload for creating/updating compensation
 */
export interface CompensationHistoryCreate {
	compensationType: CompensationType;
	annualSalary?: number | null;
	hourlyRate?: number | null;
	effectiveDate: string; // YYYY-MM-DD
	changeReason?: string | null;
}

/**
 * Response from compensation history list endpoint
 */
export interface CompensationHistoryResponse {
	history: CompensationHistory[];
	currentCompensation: CompensationHistory | null;
}

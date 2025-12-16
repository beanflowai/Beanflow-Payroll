/**
 * Payroll types for UI
 */

// Leave types
export type LeaveType = 'vacation' | 'sick';

export const LEAVE_TYPE_LABELS: Record<LeaveType, { short: string; full: string; icon: string }> = {
	vacation: { short: 'VAC', full: 'Vacation', icon: '🏖️' },
	sick: { short: 'SIC', full: 'Sick', icon: '🏥' }
};

export interface LeaveEntry {
	id: string;
	employeeId: string;
	employeeName: string;
	leaveType: LeaveType;
	hours: number;
	payRate: number; // hourly rate at time of leave
	leavePay: number; // calculated: hours × payRate
}

// Overtime entry for tracking overtime hours worked
export interface OvertimeEntry {
	id: string;
	employeeId: string;
	employeeName: string;
	hours: number; // overtime hours worked
	hourlyRate: number; // regular hourly rate
	multiplier: number; // overtime multiplier (default 1.5)
	overtimePay: number; // calculated: hours × hourlyRate × multiplier
}

// Vacation payout types (for accrual method employees only)
export type VacationPayoutReason = 'scheduled' | 'cashout_request' | 'termination';

export const VACATION_PAYOUT_LABELS: Record<
	VacationPayoutReason,
	{ label: string; icon: string }
> = {
	scheduled: { label: 'Scheduled Payout', icon: '📅' },
	cashout_request: { label: 'Cashout Request', icon: '💵' },
	termination: { label: 'Termination', icon: '🚪' }
};

export interface VacationPayoutEntry {
	id: string;
	employeeId: string;
	employeeName: string;
	payoutReason: VacationPayoutReason;
	hours: number;
	payRate: number; // hourly rate at time of payout
	payoutAmount: number; // calculated: hours × payRate
	notes?: string;
}

export type PayrollRunStatus =
	| 'draft'
	| 'calculating'
	| 'pending_approval'
	| 'approved'
	| 'paid'
	| 'cancelled';

// Paystub send status for individual employee
export type PaystubStatus = 'pending' | 'sending' | 'sent' | 'failed';

export const PAYSTUB_STATUS_LABELS: Record<PaystubStatus, string> = {
	pending: 'Not Generated',
	sending: 'Sending...',
	sent: 'Sent',
	failed: 'Failed'
};

export const PAYROLL_STATUS_LABELS: Record<PayrollRunStatus, string> = {
	draft: 'Draft',
	calculating: 'Calculating',
	pending_approval: 'Pending Approval',
	approved: 'Approved',
	paid: 'Paid',
	cancelled: 'Cancelled'
};

export const PAYROLL_STATUS_COLORS: Record<PayrollRunStatus, string> = {
	draft: 'gray',
	calculating: 'blue',
	pending_approval: 'yellow',
	approved: 'blue',
	paid: 'green',
	cancelled: 'red'
};

// Payroll Run header
export interface PayrollRun {
	id: string;
	periodStart: string;
	periodEnd: string;
	payDate: string;
	status: PayrollRunStatus;
	totalEmployees: number;
	totalGross: number;
	totalCppEmployee: number;
	totalCppEmployer: number;
	totalEiEmployee: number;
	totalEiEmployer: number;
	totalFederalTax: number;
	totalProvincialTax: number;
	totalDeductions: number;
	totalNetPay: number;
	totalEmployerCost: number;
	holidays?: Holiday[];
}

// Individual employee payroll record
export interface PayrollRecord {
	id: string;
	employeeId: string;
	employeeName: string;
	employeeProvince: string;

	// Earnings
	grossRegular: number;
	grossOvertime: number;
	holidayPay: number;
	holidayPremiumPay: number;
	vacationPayPaid: number;
	otherEarnings: number;
	totalGross: number;

	// Deductions
	cppEmployee: number;
	cppAdditional: number; // CPP2
	eiEmployee: number;
	federalTax: number;
	provincialTax: number;
	rrsp: number;
	unionDues: number;
	garnishments: number;
	otherDeductions: number;
	totalDeductions: number;

	// Net
	netPay: number;

	// Employer costs
	cppEmployer: number;
	eiEmployer: number;
	totalEmployerCost: number;

	// YTD (Year-to-Date)
	ytdGross: number;
	ytdCpp: number;
	ytdEi: number;
	ytdFederalTax: number;
	ytdProvincialTax: number;
	ytdNetPay: number;

	// Holiday work hours (for this period)
	holidayWorkHours?: HolidayWorkEntry[];

	// Overtime tracking
	overtimeEntries?: OvertimeEntry[];

	// Leave tracking
	leaveEntries?: LeaveEntry[];
	vacationHoursTaken?: number;
	sickHoursTaken?: number;
	sickPayPaid?: number;

	// Balance snapshot (after this period)
	vacationBalanceHours?: number;
	vacationBalanceDollars?: number;
	sickBalanceHours?: number;

	// YTD Leave (Year-to-Date leave usage)
	ytdVacationHours?: number;
	ytdSickHours?: number;

	// Vacation payout tracking (for accrual method employees)
	vacationPayoutEntries?: VacationPayoutEntry[];
	totalVacationPayout?: number;

	// Paystub status
	paystubStatus?: PaystubStatus;
	paystubSentAt?: string; // ISO datetime
	paystubSentTo?: string; // email address
}

// Holiday in a pay period
export interface Holiday {
	date: string;
	name: string;
	province: string;
}

// Holiday work entry for an employee
export interface HolidayWorkEntry {
	employeeId: string;
	employeeName: string;
	holidayDate: string;
	holidayName: string;
	hoursWorked: number;
}

// Earnings breakdown for expanded row
export interface EarningsBreakdown {
	label: string;
	amount: number;
	detail?: string; // e.g., "5h @ $23.08"
}

// Deductions breakdown for expanded row
export interface DeductionsBreakdown {
	label: string;
	amount: number;
	isAutoCalculated: boolean;
}

// ===========================================
// Multi Pay Group Support Types
// ===========================================

/**
 * Summary of a Pay Group for dashboard display
 */
export interface PayGroupSummary {
	id: string;
	name: string;
	payFrequency: 'weekly' | 'bi_weekly' | 'semi_monthly' | 'monthly';
	employmentType: 'full_time' | 'part_time';
	employeeCount: number;
	estimatedGross: number;
	periodStart: string;
	periodEnd: string;
}

/**
 * Upcoming pay date with associated pay groups
 * Used in the Payroll Dashboard
 */
export interface UpcomingPayDate {
	payDate: string; // ISO date string
	payGroups: PayGroupSummary[];
	totalEmployees: number;
	totalEstimatedGross: number;
	// Status of the payroll run for this date (if exists)
	runStatus?: PayrollRunStatus;
	runId?: string;
}

/**
 * Extended PayrollRecord with Pay Group info
 */
export interface PayrollRecordWithGroup extends PayrollRecord {
	payGroupId: string;
	payGroupName: string;
}

/**
 * Pay Group section within a Payroll Run
 */
export interface PayrollRunPayGroup {
	payGroupId: string;
	payGroupName: string;
	payFrequency: 'weekly' | 'bi_weekly' | 'semi_monthly' | 'monthly';
	employmentType: 'full_time' | 'part_time';
	periodStart: string;
	periodEnd: string;
	// Aggregated totals for this pay group
	totalEmployees: number;
	totalGross: number;
	totalDeductions: number;
	totalNetPay: number;
	totalEmployerCost: number;
	// Employee records for this pay group
	records: PayrollRecord[];
}

/**
 * Payroll Run with multiple Pay Groups
 * Used in the Payroll Run detail page
 */
export interface PayrollRunWithGroups {
	id: string;
	payDate: string;
	status: PayrollRunStatus;
	// All pay groups in this run
	payGroups: PayrollRunPayGroup[];
	// Aggregated totals across all pay groups
	totalEmployees: number;
	totalGross: number;
	totalCppEmployee: number;
	totalCppEmployer: number;
	totalEiEmployee: number;
	totalEiEmployer: number;
	totalFederalTax: number;
	totalProvincialTax: number;
	totalDeductions: number;
	totalNetPay: number;
	totalEmployerCost: number;
	// Holidays applicable to this pay date
	holidays?: Holiday[];
}

// Pay frequency labels for display
export const PAY_FREQUENCY_LABELS: Record<string, string> = {
	weekly: 'Weekly',
	bi_weekly: 'Bi-weekly',
	semi_monthly: 'Semi-monthly',
	monthly: 'Monthly'
};

// Employment type labels for display
export const EMPLOYMENT_TYPE_LABELS: Record<string, string> = {
	full_time: 'Full-time',
	part_time: 'Part-time'
};

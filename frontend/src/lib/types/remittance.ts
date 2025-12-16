/**
 * Remittance types for CRA payroll deduction tracking
 */

import type { RemitterType } from './company';

export type RemittanceStatus = 'pending' | 'due_soon' | 'overdue' | 'paid' | 'paid_late';

export type PaymentMethod =
	| 'my_payment'
	| 'pre_authorized_debit'
	| 'online_banking'
	| 'wire_transfer'
	| 'cheque';

export const PAYMENT_METHOD_INFO: Record<PaymentMethod, {
	label: string;
	description: string;
}> = {
	my_payment: {
		label: 'My Payment (CRA Online)',
		description: "Pay through CRA's online portal"
	},
	pre_authorized_debit: {
		label: 'Pre-Authorized Debit',
		description: 'Automatic bank withdrawal by CRA'
	},
	online_banking: {
		label: 'Online Banking',
		description: 'Pay as a bill through your bank'
	},
	wire_transfer: {
		label: 'Wire Transfer',
		description: 'Direct bank wire transfer'
	},
	cheque: {
		label: 'Cheque',
		description: 'Mail a cheque to CRA'
	}
};

export const REMITTANCE_STATUS_INFO: Record<RemittanceStatus, {
	label: string;
	icon: string;
	colorClass: string;
}> = {
	pending: {
		label: 'Pending',
		icon: 'clock',
		colorClass: 'bg-gray-100 text-gray-700'
	},
	due_soon: {
		label: 'Due Soon',
		icon: 'exclamation-triangle',
		colorClass: 'bg-yellow-100 text-yellow-800'
	},
	overdue: {
		label: 'Overdue',
		icon: 'exclamation-circle',
		colorClass: 'bg-red-100 text-red-800'
	},
	paid: {
		label: 'Paid',
		icon: 'check-circle',
		colorClass: 'bg-green-100 text-green-800'
	},
	paid_late: {
		label: 'Paid Late',
		icon: 'exclamation-triangle',
		colorClass: 'bg-orange-100 text-orange-800'
	}
};

export interface RemittancePeriod {
	id: string;
	ledgerId: string;
	remitterType: RemitterType;

	// Period Information
	periodStart: string;    // ISO date
	periodEnd: string;      // ISO date
	periodLabel: string;    // e.g., "December 2025", "Q4 2025", "Dec 1-15"
	dueDate: string;        // ISO date

	// Amounts
	cppEmployee: number;
	cppEmployer: number;
	eiEmployee: number;
	eiEmployer: number;
	federalTax: number;
	provincialTax: number;
	totalAmount: number;

	// Payment Tracking
	status: RemittanceStatus;
	paidDate: string | null;
	paymentMethod: PaymentMethod | null;
	confirmationNumber: string | null;
	notes: string | null;

	// Penalty (if overdue)
	daysOverdue: number;
	penaltyRate: number;        // 0.03, 0.05, 0.07, 0.10
	penaltyAmount: number;

	// Linked Payroll Runs
	payrollRunIds: string[];

	// Metadata
	createdAt: string;
	updatedAt: string;
}

export interface RemittanceSummary {
	year: number;
	ytdRemitted: number;
	totalRemittances: number;
	completedRemittances: number;
	onTimeRate: number;         // 0.0 to 1.0
	pendingAmount: number;
	pendingCount: number;
}

/**
 * Calculate penalty rate based on days overdue
 * Reference: CRA T4001 Chapter 8
 */
export function calculatePenaltyRate(daysOverdue: number): number {
	if (daysOverdue <= 0) return 0;
	if (daysOverdue <= 3) return 0.03;
	if (daysOverdue <= 5) return 0.05;
	if (daysOverdue <= 7) return 0.07;
	return 0.10;
}

/**
 * Calculate penalty amount
 */
export function calculatePenaltyAmount(amount: number, daysOverdue: number): number {
	const rate = calculatePenaltyRate(daysOverdue);
	return Math.round(amount * rate * 100) / 100;
}

/**
 * Determine remittance status based on due date and payment
 */
export function determineRemittanceStatus(
	dueDate: string,
	paidDate: string | null,
	today: Date = new Date()
): RemittanceStatus {
	const due = new Date(dueDate);
	due.setHours(0, 0, 0, 0);

	const now = new Date(today);
	now.setHours(0, 0, 0, 0);

	if (paidDate) {
		const paid = new Date(paidDate);
		paid.setHours(0, 0, 0, 0);
		return paid > due ? 'paid_late' : 'paid';
	}

	const diffMs = due.getTime() - now.getTime();
	const daysUntilDue = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

	if (daysUntilDue < 0) return 'overdue';
	if (daysUntilDue <= 7) return 'due_soon';
	return 'pending';
}

/**
 * Format period label based on remitter type
 */
export function formatPeriodLabel(
	remitterType: RemitterType,
	periodStart: string,
	periodEnd: string
): string {
	const start = new Date(periodStart);
	const end = new Date(periodEnd);

	const monthNames = [
		'January', 'February', 'March', 'April', 'May', 'June',
		'July', 'August', 'September', 'October', 'November', 'December'
	];

	switch (remitterType) {
		case 'quarterly': {
			const quarter = Math.ceil((end.getMonth() + 1) / 3);
			return `Q${quarter} ${end.getFullYear()}`;
		}
		case 'regular': {
			return `${monthNames[end.getMonth()]} ${end.getFullYear()}`;
		}
		case 'threshold_1':
		case 'threshold_2': {
			const startDay = start.getDate();
			const endDay = end.getDate();
			const monthShort = monthNames[end.getMonth()].substring(0, 3);
			return `${monthShort} ${startDay}-${endDay}`;
		}
		default:
			return `${monthNames[end.getMonth()]} ${end.getFullYear()}`;
	}
}

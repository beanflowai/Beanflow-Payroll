/**
 * Overtime Calculator Utility
 *
 * DEPRECATED: The calculateOvertimeSplit function has been moved to the backend.
 * Use the backend API via timesheetService.calculateOvertimeSplit() instead.
 *
 * This file only contains utility functions for date formatting and display.
 */

/**
 * Parse an ISO date string as local date (not UTC).
 */
function parseLocalDate(dateStr: string): Date {
	const [year, month, day] = dateStr.split('-').map(Number);
	return new Date(year, month - 1, day);
}

/**
 * Get short day name for a date.
 */
export function getDayName(dayOfWeek: number): string {
	const names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
	return names[dayOfWeek];
}

/**
 * Format date range for display.
 */
export function formatDateRange(startDate: string, endDate: string): string {
	const start = parseLocalDate(startDate);
	const end = parseLocalDate(endDate);

	const startStr = start.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' });
	const endStr = end.toLocaleDateString('en-CA', {
		month: 'short',
		day: 'numeric',
		year: 'numeric'
	});

	return `${startStr} - ${endStr}`;
}

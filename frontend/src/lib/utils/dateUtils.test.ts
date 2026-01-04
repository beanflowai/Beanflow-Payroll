/**
 * Tests for dateUtils
 */

import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import {
	isValidDate,
	compareDates,
	isDateInRange,
	formatDateForInput,
	parseInputDate,
	parseDateString,
	formatMonth,
	formatFullDate,
	formatShortDate,
	formatDateRange,
	formatLongDate,
	formatDateNoYear,
	formatDate,
	getRelativeDateDescription
} from './dateUtils';

describe('isValidDate', () => {
	it('returns true for valid YYYY-MM-DD format', () => {
		expect(isValidDate('2025-01-15')).toBe(true);
		expect(isValidDate('2024-02-29')).toBe(true); // leap year
		expect(isValidDate('2025-12-31')).toBe(true);
	});

	it('returns false for invalid formats', () => {
		expect(isValidDate('01-15-2025')).toBe(false);
		expect(isValidDate('2025/01/15')).toBe(false);
		expect(isValidDate('January 15, 2025')).toBe(false);
		expect(isValidDate('2025-1-15')).toBe(false); // not padded
	});

	it('returns false for empty or null values', () => {
		expect(isValidDate('')).toBe(false);
		expect(isValidDate(null as unknown as string)).toBe(false);
	});

	it('validates date string format', () => {
		// Note: JavaScript Date is lenient and auto-corrects dates like Feb 30 -> Mar 2
		// The function validates format, not calendar validity
		expect(isValidDate('2025-02-30')).toBe(true); // passes format check
		expect(isValidDate('2025-13-01')).toBe(false); // Month 13 is invalid in JS Date
		expect(isValidDate('2025-00-01')).toBe(false); // Month 0 is invalid
	});
});

describe('compareDates', () => {
	it('returns negative when date1 is before date2', () => {
		expect(compareDates('2025-01-01', '2025-01-15')).toBeLessThan(0);
		expect(compareDates('2024-12-31', '2025-01-01')).toBeLessThan(0);
	});

	it('returns positive when date1 is after date2', () => {
		expect(compareDates('2025-01-15', '2025-01-01')).toBeGreaterThan(0);
		expect(compareDates('2025-01-01', '2024-12-31')).toBeGreaterThan(0);
	});

	it('returns 0 when dates are equal', () => {
		expect(compareDates('2025-01-15', '2025-01-15')).toBe(0);
	});

	it('returns 0 for empty strings', () => {
		expect(compareDates('', '')).toBe(0);
		expect(compareDates('2025-01-15', '')).toBe(0);
		expect(compareDates('', '2025-01-15')).toBe(0);
	});
});

describe('isDateInRange', () => {
	it('returns true when date is within range', () => {
		expect(isDateInRange('2025-01-15', '2025-01-01', '2025-01-31')).toBe(true);
		expect(isDateInRange('2025-01-01', '2025-01-01', '2025-01-31')).toBe(true); // edge
		expect(isDateInRange('2025-01-31', '2025-01-01', '2025-01-31')).toBe(true); // edge
	});

	it('returns false when date is outside range', () => {
		expect(isDateInRange('2025-02-01', '2025-01-01', '2025-01-31')).toBe(false);
		expect(isDateInRange('2024-12-31', '2025-01-01', '2025-01-31')).toBe(false);
	});

	it('handles missing fromDate', () => {
		expect(isDateInRange('2025-01-15', undefined, '2025-01-31')).toBe(true);
		expect(isDateInRange('2025-02-01', undefined, '2025-01-31')).toBe(false);
	});

	it('handles missing toDate', () => {
		expect(isDateInRange('2025-01-15', '2025-01-01', undefined)).toBe(true);
		expect(isDateInRange('2024-12-31', '2025-01-01', undefined)).toBe(false);
	});

	it('handles both dates missing', () => {
		expect(isDateInRange('2025-01-15', undefined, undefined)).toBe(true);
	});

	it('returns false for empty date', () => {
		expect(isDateInRange('', '2025-01-01', '2025-01-31')).toBe(false);
	});
});

describe('formatDateForInput', () => {
	it('formats Date object to YYYY-MM-DD', () => {
		const date = new Date('2025-01-15T12:00:00');
		expect(formatDateForInput(date)).toBe('2025-01-15');
	});

	it('returns empty string for invalid date', () => {
		expect(formatDateForInput(new Date('invalid'))).toBe('');
		expect(formatDateForInput(null as unknown as Date)).toBe('');
		expect(formatDateForInput(undefined as unknown as Date)).toBe('');
	});
});

describe('parseInputDate', () => {
	it('parses valid date string to Date object', () => {
		const result = parseInputDate('2025-01-15');
		expect(result).toBeInstanceOf(Date);
		expect(result?.getFullYear()).toBe(2025);
		expect(result?.getMonth()).toBe(0); // January is 0
		expect(result?.getDate()).toBe(15);
	});

	it('returns null for invalid date string', () => {
		expect(parseInputDate('invalid')).toBe(null);
		expect(parseInputDate('')).toBe(null);
		expect(parseInputDate(null as unknown as string)).toBe(null);
	});
});

describe('parseDateString', () => {
	it('parses date string with T12:00:00 to avoid timezone issues', () => {
		const result = parseDateString('2025-01-15');
		expect(result).toBeInstanceOf(Date);
		expect(result.getHours()).toBe(12);
	});
});

describe('formatMonth', () => {
	it('formats YYYY-MM to readable month', () => {
		const result = formatMonth('2025-01');
		expect(result).toContain('January');
		expect(result).toContain('2025');
	});

	it('handles different months', () => {
		expect(formatMonth('2025-12')).toContain('December');
		expect(formatMonth('2025-06')).toContain('June');
	});
});

describe('formatFullDate', () => {
	it('formats date with weekday, month, day, and year', () => {
		// Use a known date where we can verify the weekday
		const result = formatFullDate('2025-01-01');
		expect(result).toContain('January');
		expect(result).toContain('2025');
		expect(result).toContain('Wednesday');
	});
});

describe('formatShortDate', () => {
	it('formats date as short format', () => {
		const result = formatShortDate('2025-01-15');
		expect(result).toContain('Jan');
		expect(result).toContain('15');
		expect(result).toContain('2025');
	});
});

describe('formatDateRange', () => {
	it('formats date range within same month', () => {
		const result = formatDateRange('2025-01-08', '2025-01-21');
		expect(result).toBe('Jan 8 - 21');
	});

	it('formats date range across different months', () => {
		const result = formatDateRange('2025-01-25', '2025-02-10');
		expect(result).toBe('Jan 25 - Feb 10');
	});
});

describe('formatLongDate', () => {
	it('formats date with full month name', () => {
		const result = formatLongDate('2025-01-15');
		expect(result).toContain('January');
		expect(result).toContain('15');
		expect(result).toContain('2025');
	});
});

describe('formatDateNoYear', () => {
	it('formats date without year', () => {
		const result = formatDateNoYear('2025-01-15');
		expect(result).toContain('Jan');
		expect(result).toContain('15');
		expect(result).not.toContain('2025');
	});
});

describe('formatDate', () => {
	it('formats date using formatShortDate', () => {
		const result = formatDate('2025-01-15');
		expect(result).toContain('Jan');
		expect(result).toContain('15');
		expect(result).toContain('2025');
	});

	it('returns fallback for null/undefined', () => {
		expect(formatDate(null)).toBe('-');
		expect(formatDate(undefined)).toBe('-');
		expect(formatDate('')).toBe('-');
	});

	it('uses custom fallback when provided', () => {
		expect(formatDate(null, 'N/A')).toBe('N/A');
	});
});

describe('getRelativeDateDescription', () => {
	let mockDate: Date;

	beforeEach(() => {
		// Mock current date to a fixed time for consistent testing
		mockDate = new Date('2025-01-15T12:00:00');
		vi.useFakeTimers();
		vi.setSystemTime(mockDate);
	});

	afterEach(() => {
		vi.useRealTimers();
	});

	it('returns "Today" for current date', () => {
		expect(getRelativeDateDescription('2025-01-15')).toBe('Today');
	});

	it('returns "Yesterday" for previous day', () => {
		expect(getRelativeDateDescription('2025-01-14')).toBe('Yesterday');
	});

	it('returns "Tomorrow" for next day', () => {
		expect(getRelativeDateDescription('2025-01-16')).toBe('Tomorrow');
	});

	it('returns "X days ago" for recent past days', () => {
		expect(getRelativeDateDescription('2025-01-13')).toBe('2 days ago');
		expect(getRelativeDateDescription('2025-01-10')).toBe('5 days ago');
	});

	it('returns "In X days" for near future days', () => {
		expect(getRelativeDateDescription('2025-01-17')).toBe('In 2 days');
		expect(getRelativeDateDescription('2025-01-20')).toBe('In 5 days');
	});

	it('returns weeks ago for older dates', () => {
		expect(getRelativeDateDescription('2025-01-01')).toBe('2 weeks ago');
	});

	it('returns empty string for empty input', () => {
		expect(getRelativeDateDescription('')).toBe('');
	});
});

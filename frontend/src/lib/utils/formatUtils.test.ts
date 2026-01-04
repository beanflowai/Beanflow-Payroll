/**
 * Tests for formatUtils
 */

import { describe, expect, it } from 'vitest';
import { formatCurrency, formatNumber, formatPercent } from './formatUtils';

describe('formatCurrency', () => {
	it('formats positive numbers as CAD currency', () => {
		expect(formatCurrency(1234.56)).toBe('$1,234.56');
		expect(formatCurrency(0)).toBe('$0.00');
		expect(formatCurrency(100)).toBe('$100.00');
	});

	it('formats negative numbers as CAD currency', () => {
		expect(formatCurrency(-1234.56)).toBe('-$1,234.56');
		expect(formatCurrency(-100)).toBe('-$100.00');
	});

	it('returns placeholder for null/undefined values', () => {
		expect(formatCurrency(null)).toBe('-');
		expect(formatCurrency(undefined)).toBe('-');
	});

	it('uses custom placeholder when provided', () => {
		expect(formatCurrency(null, { placeholder: 'N/A' })).toBe('N/A');
		expect(formatCurrency(undefined, { placeholder: '$0.00' })).toBe('$0.00');
	});

	it('shows sign prefix when showSign is true', () => {
		expect(formatCurrency(100, { showSign: true })).toBe('+$100.00');
		expect(formatCurrency(-100, { showSign: true })).toBe('-$100.00');
		expect(formatCurrency(0, { showSign: true })).toBe('$0.00');
	});

	it('respects custom decimal places', () => {
		expect(formatCurrency(1234.567, { maximumFractionDigits: 0 })).toBe('$1,235');
		expect(formatCurrency(1234.5, { maximumFractionDigits: 1 })).toBe('$1,234.5');
		expect(formatCurrency(1234, { maximumFractionDigits: 4 })).toBe('$1,234.0000');
	});

	it('handles large numbers with thousand separators', () => {
		expect(formatCurrency(1000000)).toBe('$1,000,000.00');
		expect(formatCurrency(12345678.9)).toBe('$12,345,678.90');
	});

	it('handles small decimal values', () => {
		expect(formatCurrency(0.01)).toBe('$0.01');
		expect(formatCurrency(0.1)).toBe('$0.10');
	});
});

describe('formatNumber', () => {
	it('formats numbers with thousand separators', () => {
		expect(formatNumber(1234)).toBe('1,234');
		expect(formatNumber(1000000)).toBe('1,000,000');
	});

	it('handles zero decimals by default', () => {
		expect(formatNumber(1234.56)).toBe('1,235'); // rounds
		expect(formatNumber(1234.4)).toBe('1,234'); // rounds
	});

	it('respects custom decimal places', () => {
		expect(formatNumber(1234.567, 2)).toBe('1,234.57');
		expect(formatNumber(1234, 2)).toBe('1,234.00');
		expect(formatNumber(1234.5678, 3)).toBe('1,234.568');
	});

	it('handles zero', () => {
		expect(formatNumber(0)).toBe('0');
		expect(formatNumber(0, 2)).toBe('0.00');
	});

	it('handles negative numbers', () => {
		expect(formatNumber(-1234)).toBe('-1,234');
		expect(formatNumber(-1234.56, 2)).toBe('-1,234.56');
	});
});

describe('formatPercent', () => {
	it('formats decimal values as percentages', () => {
		expect(formatPercent(0.15)).toBe('15.0%');
		expect(formatPercent(0.5)).toBe('50.0%');
		expect(formatPercent(1)).toBe('100.0%');
	});

	it('handles zero', () => {
		expect(formatPercent(0)).toBe('0.0%');
	});

	it('handles values greater than 1', () => {
		expect(formatPercent(1.5)).toBe('150.0%');
		expect(formatPercent(2)).toBe('200.0%');
	});

	it('handles negative percentages', () => {
		expect(formatPercent(-0.15)).toBe('-15.0%');
	});

	it('respects custom decimal places', () => {
		expect(formatPercent(0.1234, 0)).toBe('12%');
		expect(formatPercent(0.1234, 2)).toBe('12.34%');
		expect(formatPercent(0.1234, 3)).toBe('12.340%');
	});

	it('handles small decimal values', () => {
		expect(formatPercent(0.001)).toBe('0.1%');
		expect(formatPercent(0.0001, 2)).toBe('0.01%');
	});
});

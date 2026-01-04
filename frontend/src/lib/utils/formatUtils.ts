/**
 * Formatting utilities for currency, numbers, and other display values
 */

// Cached formatter instances for better performance
const currencyFormatter = new Intl.NumberFormat('en-CA', {
	style: 'currency',
	currency: 'CAD',
	minimumFractionDigits: 2,
	maximumFractionDigits: 2
});

/**
 * Format a number as Canadian currency (CAD)
 * Handles null/undefined values gracefully
 * @param amount - The amount to format (can be null/undefined)
 * @param options - Optional configuration
 * @returns Formatted currency string (e.g., "$1,234.56") or placeholder for null values
 */
export function formatCurrency(
	amount: number | null | undefined,
	options?: {
		placeholder?: string;
		showSign?: boolean;
		maximumFractionDigits?: number;
	}
): string {
	const { placeholder = '-', showSign = false, maximumFractionDigits = 2 } = options ?? {};

	if (amount == null) return placeholder;

	// Use cached formatter for default case, create new one only when needed
	if (maximumFractionDigits === 2 && !showSign) {
		return currencyFormatter.format(amount);
	}

	const formatted = new Intl.NumberFormat('en-CA', {
		style: 'currency',
		currency: 'CAD',
		minimumFractionDigits: maximumFractionDigits,
		maximumFractionDigits
	}).format(Math.abs(amount));

	if (showSign) {
		if (amount < 0) return `-${formatted}`;
		if (amount > 0) return `+${formatted}`;
	}

	return amount < 0 ? `-${formatted}` : formatted;
}

/**
 * Format a number with thousand separators
 * @param value - The number to format
 * @param decimals - Number of decimal places (default: 0)
 * @returns Formatted number string (e.g., "1,234")
 */
export function formatNumber(value: number, decimals: number = 0): string {
	return new Intl.NumberFormat('en-CA', {
		minimumFractionDigits: decimals,
		maximumFractionDigits: decimals
	}).format(value);
}

/**
 * Format a number as a percentage
 * @param value - The decimal value (e.g., 0.15 for 15%)
 * @param decimals - Number of decimal places (default: 1)
 * @returns Formatted percentage string (e.g., "15.0%")
 */
export function formatPercent(value: number, decimals: number = 1): string {
	return new Intl.NumberFormat('en-CA', {
		style: 'percent',
		minimumFractionDigits: decimals,
		maximumFractionDigits: decimals
	}).format(value);
}

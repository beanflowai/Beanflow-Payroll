/**
 * Formatting utilities for currency, numbers, and other display values
 */

/**
 * Format a number as Canadian currency (CAD)
 * @param amount - The amount to format
 * @param options - Optional Intl.NumberFormat options
 * @returns Formatted currency string (e.g., "$1,234.56")
 */
export function formatCurrency(
	amount: number,
	options?: Partial<Intl.NumberFormatOptions>
): string {
	return new Intl.NumberFormat('en-CA', {
		style: 'currency',
		currency: 'CAD',
		minimumFractionDigits: 2,
		maximumFractionDigits: 2,
		...options
	}).format(amount);
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

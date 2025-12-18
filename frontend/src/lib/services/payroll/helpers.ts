/**
 * Payroll Service Helpers
 * Utility functions used across payroll service modules
 */

import { authState } from '$lib/stores/auth.svelte';

/**
 * Get the current authenticated user's ID
 * @throws Error if user is not authenticated
 */
export function getCurrentUserId(): string {
	const user = authState.user;
	if (!user) throw new Error('User not authenticated');
	return user.id;
}

/**
 * Get the current ledger ID (using user ID for simplicity)
 * @throws Error if user is not authenticated
 */
export function getCurrentLedgerId(): string {
	const user = authState.user;
	if (!user) throw new Error('User not authenticated');
	return user.id;
}

/**
 * Get provincial Basic Personal Amount based on province code
 * 2025 values
 */
export function getProvincialBpa(province: string): string {
	const bpaMap: Record<string, string> = {
		AB: '22323.00',
		BC: '12932.00',
		MB: '15591.00',
		NB: '13396.00',
		NL: '11067.00',
		NS: '11744.00',
		NT: '17842.00',
		NU: '19274.00',
		ON: '12747.00',
		PE: '15050.00',
		SK: '19491.00',
		YT: '16129.00',
	};
	return bpaMap[province] ?? '12747.00'; // Default to ON if unknown
}

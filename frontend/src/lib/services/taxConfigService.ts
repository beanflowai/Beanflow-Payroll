/**
 * Tax Configuration Service
 *
 * Fetches tax configuration from the API instead of hardcoding values.
 * This allows the system to automatically adapt to new tax years and editions.
 */

import { api } from '$lib/api/client';
import type { Province } from '$lib/types/employee';

// Fallback BPA values (2025 July edition) - used if API fails
const FALLBACK_FEDERAL_BPA = 16129;
const FALLBACK_PROVINCIAL_BPA: Record<Province, number> = {
	AB: 22323, BC: 12932, MB: 15591, NB: 13396, NL: 11067, NS: 11744,
	NT: 17842, NU: 19274, ON: 12747, PE: 15050, SK: 19991, YT: 16129
};

export interface BPADefaults {
	year: number;
	edition: 'jan' | 'jul';
	federalBPA: number;
	provincialBPA: number;
	province: string;
}

// Cache for BPA defaults to avoid repeated API calls
const bpaCache = new Map<string, { data: BPADefaults; timestamp: number }>();
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes cache

/**
 * Get BPA defaults from the API.
 *
 * @param province - Province code
 * @param payDate - Optional pay date for edition selection
 * @returns BPA defaults from API or fallback values
 */
export async function getBPADefaults(
	province: Province,
	payDate?: Date
): Promise<BPADefaults> {
	const cacheKey = `${province}-${payDate?.toISOString().split('T')[0] ?? 'default'}`;

	// Check cache
	const cached = bpaCache.get(cacheKey);
	if (cached && Date.now() - cached.timestamp < CACHE_TTL_MS) {
		return cached.data;
	}

	try {
		const params: Record<string, string> = {};
		if (payDate) {
			params['pay_date'] = payDate.toISOString().split('T')[0];
		}

		const data = await api.get<BPADefaults>(`/payroll/bpa-defaults/${province}`, params);

		// Update cache
		bpaCache.set(cacheKey, { data, timestamp: Date.now() });

		return data;
	} catch (error) {
		console.warn('Failed to fetch BPA defaults, using fallback values:', error);

		// Return fallback values
		return {
			year: new Date().getFullYear(),
			edition: 'jul',
			federalBPA: FALLBACK_FEDERAL_BPA,
			provincialBPA: FALLBACK_PROVINCIAL_BPA[province] ?? 12747,
			province
		};
	}
}

/**
 * Get federal BPA only.
 * Convenience wrapper that extracts just the federal BPA.
 */
export async function getFederalBPA(payDate?: Date): Promise<number> {
	// Use ON as default province since federal BPA is same for all provinces
	const defaults = await getBPADefaults('ON', payDate);
	return defaults.federalBPA;
}

/**
 * Get provincial BPA only.
 * Convenience wrapper that extracts just the provincial BPA.
 */
export async function getProvincialBPAFromApi(
	province: Province,
	payDate?: Date
): Promise<number> {
	const defaults = await getBPADefaults(province, payDate);
	return defaults.provincialBPA;
}

/**
 * Clear the BPA cache.
 * Useful when user changes years or for testing.
 */
export function clearBPACache(): void {
	bpaCache.clear();
}

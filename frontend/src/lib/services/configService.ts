/**
 * Configuration Service
 *
 * Fetches configuration data (vacation rates, etc.) from the backend.
 * This provides a single source of truth for provincial minimums.
 */

import { api } from '$lib/api/client';
import type { Province } from '$lib/types/employee';

export interface VacationTier {
	minYearsOfService: number;
	vacationWeeks: number;
	vacationRate: string; // Decimal as string, e.g., "0.04", "0.0577"
	notes: string | null;
}

export interface VacationRatesConfig {
	province: string;
	name: string;
	tiers: VacationTier[];
	notes: string | null;
}

// Cache for vacation rates to avoid repeated API calls
const vacationRatesCache = new Map<string, { data: VacationRatesConfig; timestamp: number }>();
const CACHE_TTL_MS = 10 * 60 * 1000; // 10 minutes cache

// Fallback vacation rates (most provinces default)
const FALLBACK_CONFIG: VacationRatesConfig = {
	province: 'DEFAULT',
	name: 'Default',
	tiers: [
		{ minYearsOfService: 0, vacationWeeks: 2, vacationRate: '0.04', notes: '2 weeks minimum' },
		{ minYearsOfService: 5, vacationWeeks: 3, vacationRate: '0.06', notes: '3 weeks after 5 years' }
	],
	notes: 'Fallback configuration'
};

/**
 * Get vacation rate configuration for a province.
 *
 * @param province - Province code (e.g., 'SK', 'ON')
 * @param year - Optional configuration year (default: 2025)
 * @returns Vacation rates configuration
 */
export async function getVacationRates(
	province: Province,
	year: number = 2025
): Promise<VacationRatesConfig> {
	const cacheKey = `${province}-${year}`;

	// Check cache
	const cached = vacationRatesCache.get(cacheKey);
	if (cached && Date.now() - cached.timestamp < CACHE_TTL_MS) {
		return cached.data;
	}

	try {
		const data = await api.get<VacationRatesConfig>(`/config/vacation-rates/${province}`, {
			year: String(year)
		});

		// Update cache
		vacationRatesCache.set(cacheKey, { data, timestamp: Date.now() });

		return data;
	} catch (error) {
		console.warn(`Failed to fetch vacation rates for ${province}, using fallback:`, error);
		return FALLBACK_CONFIG;
	}
}

/**
 * Get the minimum vacation rate for a province based on years of service.
 *
 * @param province - Province code
 * @param yearsOfService - Employee's years of service
 * @returns Minimum vacation rate as string (e.g., "0.04")
 */
export async function getMinimumVacationRate(
	province: Province,
	yearsOfService: number
): Promise<string> {
	const config = await getVacationRates(province);

	// Find the applicable tier (highest tier where yearsOfService >= minYearsOfService)
	let applicableRate = config.tiers[0]?.vacationRate ?? '0.04';
	for (const tier of config.tiers) {
		if (yearsOfService >= tier.minYearsOfService) {
			applicableRate = tier.vacationRate;
		} else {
			break;
		}
	}

	return applicableRate;
}

/**
 * Calculate years of service from hire date.
 *
 * @param hireDate - Employee's hire date
 * @param referenceDate - Date to calculate from (default: today)
 * @returns Number of complete years of service
 */
export function calculateYearsOfService(hireDate: Date, referenceDate: Date = new Date()): number {
	let years = referenceDate.getFullYear() - hireDate.getFullYear();

	// Adjust if anniversary hasn't occurred yet this year
	const hireDateThisYear = new Date(
		referenceDate.getFullYear(),
		hireDate.getMonth(),
		hireDate.getDate()
	);
	if (referenceDate < hireDateThisYear) {
		years -= 1;
	}

	return Math.max(0, years);
}

/**
 * Clear the vacation rates cache.
 */
export function clearVacationRatesCache(): void {
	vacationRatesCache.clear();
}

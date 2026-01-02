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

/**
 * Get BPA defaults for a specific tax year.
 * Uses July 1 of the year to get the July edition BPA.
 *
 * @param province - Province code
 * @param year - Tax year (e.g., 2026, 2025)
 * @returns BPA defaults for that year
 */
export async function getBPADefaultsByYear(
	province: Province,
	year: number
): Promise<BPADefaults> {
	// Use July 1 of the year to get July edition BPA
	const payDate = new Date(year, 6, 1);
	return getBPADefaults(province, payDate);
}

// =============================================================================
// CPP/EI Contribution Limits
// =============================================================================

export interface ContributionLimits {
	year: number;
	cpp: {
		maxBaseContribution: number;       // 2025: $4,034.10 = (YMPE $71,300 - exemption $3,500) × 5.95%
		maxAdditionalContribution: number; // 2025: $396.00 (CPP2 on earnings above YMPE)
	};
	ei: {
		maxEmployeePremium: number;        // 2025: $1,077.48 = MIE $65,700 × 1.64%
	};
}

// Fallback contribution limits (2025 values) - used if API fails
// These are EMPLOYEE contribution limits, not combined employer+employee totals
const FALLBACK_CONTRIBUTION_LIMITS: ContributionLimits = {
	year: 2025,
	cpp: {
		maxBaseContribution: 4034.10,   // Employee CPP max: (YMPE - exemption) × rate
		maxAdditionalContribution: 396.00
	},
	ei: {
		maxEmployeePremium: 1077.48
	}
};

// Cache for contribution limits
const limitsCache = new Map<number, { data: ContributionLimits; timestamp: number }>();

/**
 * Get CPP/EI contribution limits from the API.
 *
 * @param year - Tax year (defaults to current year)
 * @returns Contribution limits from API or fallback values
 */
export async function getContributionLimits(year?: number): Promise<ContributionLimits> {
	const targetYear = year ?? new Date().getFullYear();

	// Check cache
	const cached = limitsCache.get(targetYear);
	if (cached && Date.now() - cached.timestamp < CACHE_TTL_MS) {
		return cached.data;
	}

	try {
		const params: Record<string, string> = { year: targetYear.toString() };
		const data = await api.get<{
			year: number;
			cpp: {
				max_base_contribution: number;
				max_additional_contribution: number;
			};
			ei: {
				max_employee_premium: number;
			};
		}>('/payroll/tax-config', params);

		const limits: ContributionLimits = {
			year: data.year,
			cpp: {
				maxBaseContribution: data.cpp.max_base_contribution,
				maxAdditionalContribution: data.cpp.max_additional_contribution
			},
			ei: {
				maxEmployeePremium: data.ei.max_employee_premium
			}
		};

		// Update cache
		limitsCache.set(targetYear, { data: limits, timestamp: Date.now() });

		return limits;
	} catch (error) {
		console.warn('Failed to fetch contribution limits, using fallback values:', error);
		return FALLBACK_CONTRIBUTION_LIMITS;
	}
}

/**
 * Clear the contribution limits cache.
 */
export function clearContributionLimitsCache(): void {
	limitsCache.clear();
}

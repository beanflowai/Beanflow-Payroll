/**
 * Tests for Tax Config Service
 */

import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

// Mock modules before imports
vi.mock('$lib/api/client', () => ({
	api: {
		get: vi.fn()
	}
}));

import { api } from '$lib/api/client';
import {
	getBPADefaults,
	getFederalBPA,
	getProvincialBPAFromApi,
	clearBPACache,
	getBPADefaultsByYear,
	getContributionLimits,
	clearContributionLimitsCache
} from './taxConfigService';

const mockApi = vi.mocked(api);

describe('getBPADefaults', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		clearBPACache();
	});

	afterEach(() => {
		clearBPACache();
	});

	it('fetches BPA defaults from API', async () => {
		const mockResponse = {
			year: 2025,
			edition: 'jul' as const,
			federalBPA: 16129,
			provincialBPA: 12747,
			province: 'ON'
		};

		mockApi.get.mockResolvedValue(mockResponse);

		const result = await getBPADefaults('ON');

		expect(mockApi.get).toHaveBeenCalledWith('/payroll/bpa-defaults/ON', {});
		expect(result).toEqual(mockResponse);
	});

	it('includes pay_date parameter when provided', async () => {
		const mockResponse = {
			year: 2025,
			edition: 'jan' as const,
			federalBPA: 15705,
			provincialBPA: 11865,
			province: 'ON'
		};

		mockApi.get.mockResolvedValue(mockResponse);

		const payDate = new Date('2025-03-15');
		await getBPADefaults('ON', payDate);

		expect(mockApi.get).toHaveBeenCalledWith('/payroll/bpa-defaults/ON', {
			pay_date: '2025-03-15'
		});
	});

	it('caches results for 5 minutes', async () => {
		const mockResponse = {
			year: 2025,
			edition: 'jul' as const,
			federalBPA: 16129,
			provincialBPA: 12747,
			province: 'ON'
		};

		mockApi.get.mockResolvedValue(mockResponse);

		// First call
		await getBPADefaults('ON');
		// Second call - should use cache
		await getBPADefaults('ON');

		expect(mockApi.get).toHaveBeenCalledTimes(1);
	});

	it('uses different cache keys for different provinces', async () => {
		const onResponse = {
			year: 2025,
			edition: 'jul' as const,
			federalBPA: 16129,
			provincialBPA: 12747,
			province: 'ON'
		};

		const bcResponse = {
			year: 2025,
			edition: 'jul' as const,
			federalBPA: 16129,
			provincialBPA: 12932,
			province: 'BC'
		};

		mockApi.get.mockResolvedValueOnce(onResponse).mockResolvedValueOnce(bcResponse);

		await getBPADefaults('ON');
		await getBPADefaults('BC');

		expect(mockApi.get).toHaveBeenCalledTimes(2);
	});

	it('returns fallback values on API error', async () => {
		mockApi.get.mockRejectedValue(new Error('API error'));

		const result = await getBPADefaults('SK');

		expect(result.federalBPA).toBe(16129);
		expect(result.provincialBPA).toBe(19991);
		expect(result.province).toBe('SK');
		expect(result.edition).toBe('jul');
	});

	it('returns fallback for unknown province', async () => {
		mockApi.get.mockRejectedValue(new Error('API error'));

		// Use a province that exists in the fallback map
		const result = await getBPADefaults('AB');

		expect(result.provincialBPA).toBe(22323);
	});
});

describe('getFederalBPA', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		clearBPACache();
	});

	it('returns federal BPA value', async () => {
		const mockResponse = {
			year: 2025,
			edition: 'jul' as const,
			federalBPA: 16129,
			provincialBPA: 12747,
			province: 'ON'
		};

		mockApi.get.mockResolvedValue(mockResponse);

		const result = await getFederalBPA();

		expect(result).toBe(16129);
	});

	it('passes pay date to getBPADefaults', async () => {
		const mockResponse = {
			year: 2025,
			edition: 'jan' as const,
			federalBPA: 15705,
			provincialBPA: 11865,
			province: 'ON'
		};

		mockApi.get.mockResolvedValue(mockResponse);

		const payDate = new Date('2025-03-15');
		await getFederalBPA(payDate);

		expect(mockApi.get).toHaveBeenCalledWith('/payroll/bpa-defaults/ON', {
			pay_date: '2025-03-15'
		});
	});
});

describe('getProvincialBPAFromApi', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		clearBPACache();
	});

	it('returns provincial BPA value', async () => {
		const mockResponse = {
			year: 2025,
			edition: 'jul' as const,
			federalBPA: 16129,
			provincialBPA: 22323,
			province: 'AB'
		};

		mockApi.get.mockResolvedValue(mockResponse);

		const result = await getProvincialBPAFromApi('AB');

		expect(result).toBe(22323);
	});

	it('passes pay date to getBPADefaults', async () => {
		const mockResponse = {
			year: 2025,
			edition: 'jul' as const,
			federalBPA: 16129,
			provincialBPA: 12932,
			province: 'BC'
		};

		mockApi.get.mockResolvedValue(mockResponse);

		const payDate = new Date('2025-06-15');
		await getProvincialBPAFromApi('BC', payDate);

		expect(mockApi.get).toHaveBeenCalledWith('/payroll/bpa-defaults/BC', {
			pay_date: '2025-06-15'
		});
	});
});

describe('clearBPACache', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('clears the cache', async () => {
		const mockResponse = {
			year: 2025,
			edition: 'jul' as const,
			federalBPA: 16129,
			provincialBPA: 12747,
			province: 'ON'
		};

		mockApi.get.mockResolvedValue(mockResponse);

		// First call
		await getBPADefaults('ON');
		// Clear cache
		clearBPACache();
		// Second call - should fetch again
		await getBPADefaults('ON');

		expect(mockApi.get).toHaveBeenCalledTimes(2);
	});
});

describe('getBPADefaultsByYear', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		clearBPACache();
	});

	it('uses July 1 of the specified year', async () => {
		const mockResponse = {
			year: 2026,
			edition: 'jul' as const,
			federalBPA: 16500,
			provincialBPA: 13000,
			province: 'ON'
		};

		mockApi.get.mockResolvedValue(mockResponse);

		await getBPADefaultsByYear('ON', 2026);

		expect(mockApi.get).toHaveBeenCalledWith('/payroll/bpa-defaults/ON', {
			pay_date: '2026-07-01'
		});
	});

	it('works with different years', async () => {
		const mockResponse = {
			year: 2025,
			edition: 'jul' as const,
			federalBPA: 16129,
			provincialBPA: 12747,
			province: 'ON'
		};

		mockApi.get.mockResolvedValue(mockResponse);

		await getBPADefaultsByYear('BC', 2025);

		expect(mockApi.get).toHaveBeenCalledWith('/payroll/bpa-defaults/BC', {
			pay_date: '2025-07-01'
		});
	});
});

describe('getContributionLimits', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		clearContributionLimitsCache();
	});

	afterEach(() => {
		clearContributionLimitsCache();
	});

	it('fetches contribution limits from API', async () => {
		const mockResponse = {
			year: 2025,
			cpp: {
				max_base_contribution: 4034.1,
				max_additional_contribution: 396.0
			},
			ei: {
				max_employee_premium: 1077.48
			}
		};

		mockApi.get.mockResolvedValue(mockResponse);

		const result = await getContributionLimits(2025);

		expect(mockApi.get).toHaveBeenCalledWith('/payroll/tax-config', { year: '2025' });
		expect(result).toEqual({
			year: 2025,
			cpp: {
				maxBaseContribution: 4034.1,
				maxAdditionalContribution: 396.0
			},
			ei: {
				maxEmployeePremium: 1077.48
			}
		});
	});

	it('uses current year when no year provided', async () => {
		const currentYear = new Date().getFullYear();
		const mockResponse = {
			year: currentYear,
			cpp: {
				max_base_contribution: 4034.1,
				max_additional_contribution: 396.0
			},
			ei: {
				max_employee_premium: 1077.48
			}
		};

		mockApi.get.mockResolvedValue(mockResponse);

		await getContributionLimits();

		expect(mockApi.get).toHaveBeenCalledWith('/payroll/tax-config', {
			year: currentYear.toString()
		});
	});

	it('caches results for 5 minutes', async () => {
		const mockResponse = {
			year: 2025,
			cpp: {
				max_base_contribution: 4034.1,
				max_additional_contribution: 396.0
			},
			ei: {
				max_employee_premium: 1077.48
			}
		};

		mockApi.get.mockResolvedValue(mockResponse);

		// First call
		await getContributionLimits(2025);
		// Second call - should use cache
		await getContributionLimits(2025);

		expect(mockApi.get).toHaveBeenCalledTimes(1);
	});

	it('uses different cache keys for different years', async () => {
		const mockResponse2025 = {
			year: 2025,
			cpp: { max_base_contribution: 4034.1, max_additional_contribution: 396.0 },
			ei: { max_employee_premium: 1077.48 }
		};

		const mockResponse2026 = {
			year: 2026,
			cpp: { max_base_contribution: 4200.0, max_additional_contribution: 420.0 },
			ei: { max_employee_premium: 1100.0 }
		};

		mockApi.get.mockResolvedValueOnce(mockResponse2025).mockResolvedValueOnce(mockResponse2026);

		await getContributionLimits(2025);
		await getContributionLimits(2026);

		expect(mockApi.get).toHaveBeenCalledTimes(2);
	});

	it('returns fallback values on API error', async () => {
		mockApi.get.mockRejectedValue(new Error('API error'));

		const result = await getContributionLimits(2025);

		expect(result).toEqual({
			year: 2025,
			cpp: {
				maxBaseContribution: 4034.1,
				maxAdditionalContribution: 396.0
			},
			ei: {
				maxEmployeePremium: 1077.48
			}
		});
	});
});

describe('clearContributionLimitsCache', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('clears the cache', async () => {
		const mockResponse = {
			year: 2025,
			cpp: {
				max_base_contribution: 4034.1,
				max_additional_contribution: 396.0
			},
			ei: {
				max_employee_premium: 1077.48
			}
		};

		mockApi.get.mockResolvedValue(mockResponse);

		// First call
		await getContributionLimits(2025);
		// Clear cache
		clearContributionLimitsCache();
		// Second call - should fetch again
		await getContributionLimits(2025);

		expect(mockApi.get).toHaveBeenCalledTimes(2);
	});
});

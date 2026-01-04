/**
 * Tests for configService
 */

import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import {
	calculateYearsOfService,
	clearProvinceStandardsCache,
	clearVacationRatesCache,
	getMinimumVacationRate,
	getProvinceStandards,
	getVacationRates,
	type VacationRatesConfig
} from './configService';

// Mock the API client
vi.mock('$lib/api/client', () => ({
	api: {
		get: vi.fn()
	}
}));

import { api } from '$lib/api/client';
const mockApi = vi.mocked(api);

describe('calculateYearsOfService', () => {
	it('calculates complete years of service', () => {
		const hireDate = new Date('2020-01-15');
		const referenceDate = new Date('2025-01-20');
		expect(calculateYearsOfService(hireDate, referenceDate)).toBe(5);
	});

	it('does not count incomplete years', () => {
		const hireDate = new Date('2020-06-15');
		const referenceDate = new Date('2025-03-01');
		// Anniversary hasn't happened yet in 2025
		expect(calculateYearsOfService(hireDate, referenceDate)).toBe(4);
	});

	it('returns 0 for same year hire', () => {
		const hireDate = new Date('2025-06-01');
		const referenceDate = new Date('2025-01-15');
		expect(calculateYearsOfService(hireDate, referenceDate)).toBe(0);
	});

	it('returns 0 for negative years', () => {
		const hireDate = new Date('2026-01-01');
		const referenceDate = new Date('2025-06-01');
		expect(calculateYearsOfService(hireDate, referenceDate)).toBe(0);
	});

	it('counts exactly on anniversary date', () => {
		const hireDate = new Date('2020-03-15');
		const referenceDate = new Date('2025-03-15');
		expect(calculateYearsOfService(hireDate, referenceDate)).toBe(5);
	});

	it('counts day before anniversary correctly', () => {
		const hireDate = new Date('2020-03-15');
		const referenceDate = new Date('2025-03-14');
		expect(calculateYearsOfService(hireDate, referenceDate)).toBe(4);
	});

	it('uses current date as default reference', () => {
		const hireDate = new Date('2020-01-01');
		// Just verify it doesn't throw
		const result = calculateYearsOfService(hireDate);
		expect(typeof result).toBe('number');
		expect(result).toBeGreaterThanOrEqual(0);
	});
});

describe('getVacationRates', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		clearVacationRatesCache();
	});

	it('fetches vacation rates from API', async () => {
		const mockConfig: VacationRatesConfig = {
			province: 'SK',
			name: 'Saskatchewan',
			tiers: [
				{ minYearsOfService: 0, vacationWeeks: 3, vacationRate: '0.0577', notes: null },
				{ minYearsOfService: 10, vacationWeeks: 4, vacationRate: '0.0769', notes: null }
			],
			notes: null
		};
		mockApi.get.mockResolvedValueOnce(mockConfig);

		const result = await getVacationRates('SK');

		expect(mockApi.get).toHaveBeenCalledWith('/config/vacation-rates/SK', { year: '2025' });
		expect(result).toEqual(mockConfig);
	});

	it('caches vacation rates', async () => {
		const mockConfig: VacationRatesConfig = {
			province: 'ON',
			name: 'Ontario',
			tiers: [{ minYearsOfService: 0, vacationWeeks: 2, vacationRate: '0.04', notes: null }],
			notes: null
		};
		mockApi.get.mockResolvedValueOnce(mockConfig);

		// First call
		await getVacationRates('ON');
		// Second call should use cache
		await getVacationRates('ON');

		expect(mockApi.get).toHaveBeenCalledTimes(1);
	});

	it('returns fallback config on error', async () => {
		mockApi.get.mockRejectedValueOnce(new Error('Network error'));

		const result = await getVacationRates('BC');

		expect(result.province).toBe('DEFAULT');
		expect(result.tiers).toHaveLength(2);
	});

	it('uses custom year parameter', async () => {
		mockApi.get.mockResolvedValueOnce({
			province: 'AB',
			name: 'Alberta',
			tiers: [],
			notes: null
		});

		await getVacationRates('AB', 2024);

		expect(mockApi.get).toHaveBeenCalledWith('/config/vacation-rates/AB', { year: '2024' });
	});
});

describe('getMinimumVacationRate', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		clearVacationRatesCache();
	});

	it('returns correct rate for 0 years of service', async () => {
		const mockConfig: VacationRatesConfig = {
			province: 'SK',
			name: 'Saskatchewan',
			tiers: [
				{ minYearsOfService: 0, vacationWeeks: 3, vacationRate: '0.0577', notes: null },
				{ minYearsOfService: 10, vacationWeeks: 4, vacationRate: '0.0769', notes: null }
			],
			notes: null
		};
		mockApi.get.mockResolvedValueOnce(mockConfig);

		const result = await getMinimumVacationRate('SK', 0);

		expect(result).toBe('0.0577');
	});

	it('returns higher tier rate for more years', async () => {
		const mockConfig: VacationRatesConfig = {
			province: 'SK',
			name: 'Saskatchewan',
			tiers: [
				{ minYearsOfService: 0, vacationWeeks: 3, vacationRate: '0.0577', notes: null },
				{ minYearsOfService: 10, vacationWeeks: 4, vacationRate: '0.0769', notes: null }
			],
			notes: null
		};
		mockApi.get.mockResolvedValueOnce(mockConfig);

		const result = await getMinimumVacationRate('SK', 15);

		expect(result).toBe('0.0769');
	});

	it('returns correct rate at tier boundary', async () => {
		const mockConfig: VacationRatesConfig = {
			province: 'ON',
			name: 'Ontario',
			tiers: [
				{ minYearsOfService: 0, vacationWeeks: 2, vacationRate: '0.04', notes: null },
				{ minYearsOfService: 5, vacationWeeks: 3, vacationRate: '0.06', notes: null }
			],
			notes: null
		};
		mockApi.get.mockResolvedValueOnce(mockConfig);

		const result = await getMinimumVacationRate('ON', 5);

		expect(result).toBe('0.06');
	});

	it('returns default rate when config has no tiers', async () => {
		const mockConfig: VacationRatesConfig = {
			province: 'XX',
			name: 'Unknown',
			tiers: [],
			notes: null
		};
		mockApi.get.mockResolvedValueOnce(mockConfig);

		const result = await getMinimumVacationRate('XX' as any, 3);

		expect(result).toBe('0.04');
	});
});

describe('clearVacationRatesCache', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('clears the cache', async () => {
		const mockConfig: VacationRatesConfig = {
			province: 'MB',
			name: 'Manitoba',
			tiers: [],
			notes: null
		};
		mockApi.get.mockResolvedValue(mockConfig);

		// First call to populate cache
		await getVacationRates('MB');
		expect(mockApi.get).toHaveBeenCalledTimes(1);

		// Clear cache
		clearVacationRatesCache();

		// Should fetch again
		await getVacationRates('MB');
		expect(mockApi.get).toHaveBeenCalledTimes(2);
	});
});

describe('getProvinceStandards', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		clearProvinceStandardsCache();
	});

	it('fetches province standards from API', async () => {
		const mockStandards = {
			provinceCode: 'ON',
			provinceName: 'Ontario',
			vacation: {
				minimumWeeks: 2,
				minimumRate: 0.04,
				rateDisplay: '4%',
				upgradeYears: 5,
				upgradeWeeks: 3,
				notes: null
			},
			sickLeave: {
				paidDays: 3,
				unpaidDays: 5,
				waitingPeriodDays: 0,
				notes: null
			},
			overtime: {
				dailyThreshold: null,
				weeklyThreshold: 44,
				overtimeRate: 1.5,
				doubleTimeDaily: null,
				notes: 'Weekly threshold only'
			},
			statutoryHolidaysCount: 9
		};
		mockApi.get.mockResolvedValueOnce(mockStandards);

		const result = await getProvinceStandards('ON');

		expect(mockApi.get).toHaveBeenCalledWith('/config/province-standards/ON', { year: '2025' });
		expect(result).toEqual(mockStandards);
	});

	it('caches province standards', async () => {
		mockApi.get.mockResolvedValueOnce({ provinceCode: 'BC' });

		await getProvinceStandards('BC');
		await getProvinceStandards('BC');

		expect(mockApi.get).toHaveBeenCalledTimes(1);
	});

	it('returns null on error', async () => {
		mockApi.get.mockRejectedValueOnce(new Error('Not found'));

		const result = await getProvinceStandards('XX' as any);

		expect(result).toBeNull();
	});

	it('uses custom year parameter', async () => {
		mockApi.get.mockResolvedValueOnce({ provinceCode: 'AB' });

		await getProvinceStandards('AB', 2024);

		expect(mockApi.get).toHaveBeenCalledWith('/config/province-standards/AB', { year: '2024' });
	});
});

describe('clearProvinceStandardsCache', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('clears the province standards cache', async () => {
		mockApi.get.mockResolvedValue({ provinceCode: 'NS' });

		// First call to populate cache
		await getProvinceStandards('NS');
		expect(mockApi.get).toHaveBeenCalledTimes(1);

		// Clear cache
		clearProvinceStandardsCache();

		// Should fetch again
		await getProvinceStandards('NS');
		expect(mockApi.get).toHaveBeenCalledTimes(2);
	});
});

/**
 * Tests for sickLeaveService
 */

import { describe, expect, it, vi, beforeEach } from 'vitest';
import {
	clearSickLeaveCache,
	getEmployeeSickLeaveBalance,
	getProvincesWithPaidSickLeave,
	getSickLeaveConfig,
	getSickLeaveConfigs,
	hasPaidSickLeave
} from './sickLeaveService';

// Mock the API client
vi.mock('$lib/api/client', () => ({
	api: {
		get: vi.fn()
	}
}));

import { api } from '$lib/api/client';
const mockApi = vi.mocked(api);

describe('getSickLeaveConfigs', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		clearSickLeaveCache();
	});

	it('fetches all sick leave configs from API', async () => {
		const mockConfigs = [
			{ provinceCode: 'BC', paidDaysPerYear: 5, unpaidDaysPerYear: 3 },
			{ provinceCode: 'ON', paidDaysPerYear: 3, unpaidDaysPerYear: 0 }
		];
		mockApi.get.mockResolvedValueOnce(mockConfigs);

		const result = await getSickLeaveConfigs();

		expect(mockApi.get).toHaveBeenCalledWith('/payroll/sick-leave/configs', { year: '2025' });
		expect(result).toEqual(mockConfigs);
	});

	it('uses custom year parameter', async () => {
		mockApi.get.mockResolvedValueOnce([]);

		await getSickLeaveConfigs(2024);

		expect(mockApi.get).toHaveBeenCalledWith('/payroll/sick-leave/configs', { year: '2024' });
	});

	it('includes pay_date when provided', async () => {
		mockApi.get.mockResolvedValueOnce([]);
		const payDate = new Date('2025-07-15');

		await getSickLeaveConfigs(2025, payDate);

		expect(mockApi.get).toHaveBeenCalledWith('/payroll/sick-leave/configs', {
			year: '2025',
			pay_date: '2025-07-15'
		});
	});

	it('caches results', async () => {
		const mockConfigs = [{ provinceCode: 'BC', paidDaysPerYear: 5, unpaidDaysPerYear: 3 }];
		mockApi.get.mockResolvedValueOnce(mockConfigs);

		await getSickLeaveConfigs();
		await getSickLeaveConfigs();

		expect(mockApi.get).toHaveBeenCalledTimes(1);
	});
});

describe('getSickLeaveConfig', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		clearSickLeaveCache();
	});

	it('fetches config for specific province', async () => {
		const mockConfig = { provinceCode: 'BC', paidDaysPerYear: 5, unpaidDaysPerYear: 3 };
		mockApi.get.mockResolvedValueOnce(mockConfig);

		const result = await getSickLeaveConfig('BC');

		expect(mockApi.get).toHaveBeenCalledWith('/payroll/sick-leave/configs/BC', { year: '2025' });
		expect(result).toEqual(mockConfig);
	});

	it('uses custom year parameter', async () => {
		mockApi.get.mockResolvedValueOnce({});

		await getSickLeaveConfig('ON', 2024);

		expect(mockApi.get).toHaveBeenCalledWith('/payroll/sick-leave/configs/ON', { year: '2024' });
	});

	it('includes pay_date when provided', async () => {
		mockApi.get.mockResolvedValueOnce({});
		const payDate = new Date('2025-07-15');

		await getSickLeaveConfig('SK', 2025, payDate);

		expect(mockApi.get).toHaveBeenCalledWith('/payroll/sick-leave/configs/SK', {
			year: '2025',
			pay_date: '2025-07-15'
		});
	});

	it('returns undefined on error', async () => {
		mockApi.get.mockRejectedValueOnce(new Error('Not found'));

		const result = await getSickLeaveConfig('XX');

		expect(result).toBeUndefined();
	});

	it('caches results', async () => {
		mockApi.get.mockResolvedValueOnce({});

		await getSickLeaveConfig('AB');
		await getSickLeaveConfig('AB');

		expect(mockApi.get).toHaveBeenCalledTimes(1);
	});
});

describe('hasPaidSickLeave', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		clearSickLeaveCache();
	});

	it('returns true for province with paid sick leave', async () => {
		mockApi.get.mockResolvedValueOnce({ provinceCode: 'BC', paidDaysPerYear: 5 });

		const result = await hasPaidSickLeave('BC');

		expect(result).toBe(true);
	});

	it('returns false for province without paid sick leave', async () => {
		mockApi.get.mockResolvedValueOnce({ provinceCode: 'AB', paidDaysPerYear: 0 });

		const result = await hasPaidSickLeave('AB');

		expect(result).toBe(false);
	});

	it('returns false when config not found', async () => {
		mockApi.get.mockRejectedValueOnce(new Error('Not found'));

		const result = await hasPaidSickLeave('XX');

		expect(result).toBe(false);
	});
});

describe('getProvincesWithPaidSickLeave', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		clearSickLeaveCache();
	});

	it('returns only provinces with paid sick leave', async () => {
		const mockConfigs = [
			{ provinceCode: 'BC', paidDaysPerYear: 5 },
			{ provinceCode: 'ON', paidDaysPerYear: 3 },
			{ provinceCode: 'AB', paidDaysPerYear: 0 },
			{ provinceCode: 'SK', paidDaysPerYear: 0 }
		];
		mockApi.get.mockResolvedValueOnce(mockConfigs);

		const result = await getProvincesWithPaidSickLeave();

		expect(result).toEqual(['BC', 'ON']);
	});

	it('returns empty array when no provinces have paid leave', async () => {
		mockApi.get.mockResolvedValueOnce([
			{ provinceCode: 'AB', paidDaysPerYear: 0 },
			{ provinceCode: 'SK', paidDaysPerYear: 0 }
		]);

		const result = await getProvincesWithPaidSickLeave();

		expect(result).toEqual([]);
	});
});

describe('getEmployeeSickLeaveBalance', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('fetches and normalizes sick leave balance', async () => {
		const mockBalance = {
			employeeId: 'emp-123',
			year: 2025,
			paidDaysEntitled: 5,
			unpaidDaysEntitled: 3,
			paidDaysUsed: 2,
			unpaidDaysUsed: 0,
			paidDaysRemaining: 3,
			unpaidDaysRemaining: 3,
			carriedOverDays: 0,
			isEligible: true,
			eligibilityDate: '2024-01-01',
			accruedDaysYtd: 2.5,
			lastAccrualDate: '2025-01-15'
		};
		mockApi.get.mockResolvedValueOnce(mockBalance);

		const result = await getEmployeeSickLeaveBalance('emp-123', 2025);

		expect(mockApi.get).toHaveBeenCalledWith('/payroll/employees/emp-123/sick-leave/2025');
		expect(result).toEqual(mockBalance);
	});

	it('handles snake_case API response', async () => {
		const mockBalance = {
			employee_id: 'emp-123',
			year: 2025,
			paid_days_entitled: 5,
			unpaid_days_entitled: 3,
			paid_days_used: 1,
			unpaid_days_used: 0,
			paid_days_remaining: 4,
			unpaid_days_remaining: 3,
			carried_over_days: 1,
			is_eligible: true,
			eligibility_date: '2024-01-01',
			accrued_days_ytd: 2.0,
			last_accrual_date: '2025-01-10'
		};
		mockApi.get.mockResolvedValueOnce(mockBalance);

		const result = await getEmployeeSickLeaveBalance('emp-123', 2025);

		expect(result).toEqual({
			employeeId: 'emp-123',
			year: 2025,
			paidDaysEntitled: 5,
			unpaidDaysEntitled: 3,
			paidDaysUsed: 1,
			unpaidDaysUsed: 0,
			paidDaysRemaining: 4,
			unpaidDaysRemaining: 3,
			carriedOverDays: 1,
			isEligible: true,
			eligibilityDate: '2024-01-01',
			accruedDaysYtd: 2.0,
			lastAccrualDate: '2025-01-10'
		});
	});

	it('returns undefined on error', async () => {
		mockApi.get.mockRejectedValueOnce(new Error('Not found'));

		const result = await getEmployeeSickLeaveBalance('emp-123', 2025);

		expect(result).toBeUndefined();
	});

	it('handles missing optional fields', async () => {
		const mockBalance = {
			employeeId: 'emp-123',
			year: 2025,
			isEligible: false
			// No other fields
		};
		mockApi.get.mockResolvedValueOnce(mockBalance);

		const result = await getEmployeeSickLeaveBalance('emp-123', 2025);

		expect(result?.paidDaysEntitled).toBe(0);
		expect(result?.unpaidDaysUsed).toBe(0);
		expect(result?.eligibilityDate).toBeUndefined();
	});
});

describe('clearSickLeaveCache', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		clearSickLeaveCache();
	});

	it('clears the cache', async () => {
		mockApi.get.mockResolvedValue([]);

		// Populate cache
		await getSickLeaveConfigs();
		expect(mockApi.get).toHaveBeenCalledTimes(1);

		// Second call should use cache
		await getSickLeaveConfigs();
		expect(mockApi.get).toHaveBeenCalledTimes(1);

		// Clear cache
		clearSickLeaveCache();

		// Should fetch again
		await getSickLeaveConfigs();
		expect(mockApi.get).toHaveBeenCalledTimes(2);
	});
});

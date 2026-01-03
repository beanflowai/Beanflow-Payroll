/**
 * Tests for Payroll Run Paystub Functions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock modules
const mockApiGet = vi.fn();
const mockApiPost = vi.fn();
const mockGetCurrentUserId = vi.fn();

vi.mock('$lib/api/client', () => ({
	api: {
		get get() { return mockApiGet; },
		get post() { return mockApiPost; }
	}
}));

vi.mock('./helpers', () => ({
	get getCurrentUserId() { return mockGetCurrentUserId; }
}));

import {
	getPaystubDownloadUrl,
	sendPaystubs
} from './run-paystubs';

describe('Payroll Run Paystubs', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockGetCurrentUserId.mockReturnValue('test-user-id');
	});

	describe('getPaystubDownloadUrl', () => {
		it('returns presigned URL for paystub', async () => {
			mockApiGet.mockResolvedValue({
				storageKey: 'paystubs/2025/01/record-1.pdf',
				downloadUrl: 'https://storage.example.com/signed-url',
				expiresIn: 3600
			});

			const result = await getPaystubDownloadUrl('record-1');

			expect(mockApiGet).toHaveBeenCalledWith('/payroll/records/record-1/paystub-url');
			expect(result.data?.downloadUrl).toContain('signed-url');
		});
	});

	describe('sendPaystubs', () => {
		it('sends paystubs and returns result', async () => {
			mockApiPost.mockResolvedValue({
				sent: 5,
				sent_record_ids: ['r1', 'r2', 'r3', 'r4', 'r5'],
				errors: null
			});

			const result = await sendPaystubs('run-123');

			expect(mockApiPost).toHaveBeenCalledWith('/payroll/runs/run-123/send-paystubs', {});
			expect(result.data?.sent).toBe(5);
			expect(result.data?.errors).toBeNull();
		});

		it('returns partial success with errors', async () => {
			mockApiPost.mockResolvedValue({
				sent: 3,
				sent_record_ids: ['r1', 'r2', 'r3'],
				errors: ['Failed to send to emp-4', 'Failed to send to emp-5']
			});

			const result = await sendPaystubs('run-123');

			expect(result.data?.sent).toBe(3);
			expect(result.data?.errors).toHaveLength(2);
		});
	});
});

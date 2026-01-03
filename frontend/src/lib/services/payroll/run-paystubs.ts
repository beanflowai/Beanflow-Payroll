/**
 * Payroll Run Paystub Operations
 * Functions for managing paystubs
 */

import { api } from '$lib/api/client';
import { getCurrentUserId } from './helpers';
import type { PayrollServiceResult } from './types';

// ===========================================
// Paystub Download
// ===========================================

/**
 * Get a presigned URL for downloading a paystub PDF
 */
export async function getPaystubDownloadUrl(
	recordId: string
): Promise<PayrollServiceResult<{ storageKey: string; downloadUrl: string; expiresIn: number }>> {
	try {
		getCurrentUserId();

		const response = await api.get<{
			storageKey: string;
			downloadUrl: string;
			expiresIn: number;
		}>(`/payroll/records/${recordId}/paystub-url`);

		return {
			data: {
				storageKey: response.storageKey,
				downloadUrl: response.downloadUrl,
				expiresIn: response.expiresIn
			},
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to get paystub URL';
		console.error('getPaystubDownloadUrl error:', message);
		return { data: null, error: message };
	}
}

// ===========================================
// Send Paystubs
// ===========================================

/**
 * Send paystub emails to all employees for an approved payroll run.
 * Only works on runs in 'approved' status.
 */
export async function sendPaystubs(
	runId: string
): Promise<PayrollServiceResult<{ sent: number; sent_record_ids: string[]; errors: string[] | null }>> {
	try {
		getCurrentUserId();

		const response = await api.post<{
			sent: number;
			sent_record_ids: string[];
			errors: string[] | null;
		}>(`/payroll/runs/${runId}/send-paystubs`, {});

		return {
			data: {
				sent: response.sent,
				sent_record_ids: response.sent_record_ids,
				errors: response.errors
			},
			error: null
		};
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to send paystubs';
		console.error('sendPaystubs error:', message);
		return { data: null, error: message };
	}
}

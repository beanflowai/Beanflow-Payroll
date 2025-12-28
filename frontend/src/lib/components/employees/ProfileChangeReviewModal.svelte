<script lang="ts">
	/**
	 * ProfileChangeReviewModal - Review and approve/reject employee profile changes
	 * Used by employer to review changes submitted by employees via portal
	 */
	import BaseModal from '$lib/shared-base/BaseModal.svelte';
	import type { ProfileChangeRequest } from '$lib/types/employee-portal';
	import { formatDateTime } from '$lib/utils/dateUtils';

	interface Props {
		visible: boolean;
		changeRequest: ProfileChangeRequest;
		onclose: () => void;
		onApprove: (requestId: string) => void;
		onReject: (requestId: string, reason: string) => void;
	}

	let { visible = $bindable(), changeRequest, onclose, onApprove, onReject }: Props = $props();

	let isSubmitting = $state(false);
	let showRejectReason = $state(false);
	let rejectReason = $state('');

	const changeTypeLabels = {
		personal_info: 'Personal Information',
		tax_info: 'Tax Information',
		bank_info: 'Bank Information'
	};


	function handleApprove() {
		isSubmitting = true;
		setTimeout(() => {
			isSubmitting = false;
			onApprove(changeRequest.id);
			onclose();
		}, 500);
	}

	function handleReject() {
		if (!rejectReason.trim()) {
			return;
		}
		isSubmitting = true;
		setTimeout(() => {
			isSubmitting = false;
			onReject(changeRequest.id, rejectReason);
			onclose();
		}, 500);
	}

	function startReject() {
		showRejectReason = true;
	}

	function cancelReject() {
		showRejectReason = false;
		rejectReason = '';
	}

	// Get change fields to display
	function getChangeFields(): Array<{ label: string; current: string; requested: string }> {
		const current = changeRequest.currentValues;
		const requested = changeRequest.requestedValues;
		const fields: Array<{ label: string; current: string; requested: string }> = [];

		if (changeRequest.changeType === 'bank_info') {
			if (current.bankName !== requested.bankName) {
				fields.push({ label: 'Bank', current: String(current.bankName), requested: String(requested.bankName) });
			}
			if (current.transitNumber !== requested.transitNumber) {
				fields.push({ label: 'Transit', current: String(current.transitNumber), requested: String(requested.transitNumber) });
			}
			if (current.institutionNumber !== requested.institutionNumber) {
				fields.push({ label: 'Institution', current: String(current.institutionNumber), requested: String(requested.institutionNumber) });
			}
			if (current.accountNumber !== requested.accountNumber) {
				fields.push({ label: 'Account', current: String(current.accountNumber), requested: String(requested.accountNumber) });
			}
		} else if (changeRequest.changeType === 'tax_info') {
			if (current.federalAdditionalClaims !== requested.federalAdditionalClaims) {
				fields.push({ label: 'Federal Additional Claims', current: `$${current.federalAdditionalClaims}`, requested: `$${requested.federalAdditionalClaims}` });
			}
			if (current.provincialAdditionalClaims !== requested.provincialAdditionalClaims) {
				fields.push({ label: 'Provincial Additional Claims', current: `$${current.provincialAdditionalClaims}`, requested: `$${requested.provincialAdditionalClaims}` });
			}
			if (current.additionalTaxPerPeriod !== requested.additionalTaxPerPeriod) {
				fields.push({ label: 'Additional Tax/Period', current: `$${current.additionalTaxPerPeriod}`, requested: `$${requested.additionalTaxPerPeriod}` });
			}
		}

		return fields;
	}

	const changeFields = $derived(getChangeFields());
</script>

<BaseModal {visible} {onclose} size="medium" title="Review Profile Changes">
	<div class="review-modal">
		<!-- Header Info -->
		<div class="request-header">
			<h3 class="employee-name">{changeRequest.employeeName}</h3>
			<span class="change-type-badge">{changeTypeLabels[changeRequest.changeType]} Change</span>
			<p class="submitted-date">Submitted: {formatDateTime(changeRequest.submittedAt)}</p>
		</div>

		<!-- Changes Comparison -->
		<div class="changes-section">
			<table class="changes-table">
				<thead>
					<tr>
						<th></th>
						<th>Current</th>
						<th>Requested Change</th>
					</tr>
				</thead>
				<tbody>
					{#each changeFields as field}
						<tr>
							<td class="field-label">{field.label}</td>
							<td class="current-value">{field.current}</td>
							<td class="requested-value">{field.requested}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>

		<!-- Attachments -->
		{#if changeRequest.attachments && changeRequest.attachments.length > 0}
			<div class="attachments-section">
				<h4 class="attachments-title">Attached Documents:</h4>
				<div class="attachments-list">
					{#each changeRequest.attachments as attachment}
						<a href={attachment} target="_blank" class="attachment-link">
							<svg viewBox="0 0 20 20" fill="currentColor">
								<path
									fill-rule="evenodd"
									d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z"
									clip-rule="evenodd"
								/>
							</svg>
							View File
						</a>
					{/each}
				</div>
			</div>
		{/if}

		<!-- Reject Reason Input -->
		{#if showRejectReason}
			<div class="reject-reason-section">
				<label for="rejectReason" class="reason-label">Reason for Rejection:</label>
				<textarea
					id="rejectReason"
					class="reason-input"
					bind:value={rejectReason}
					placeholder="Please provide a reason for rejecting this change request..."
					rows="3"
				></textarea>
			</div>
		{/if}

		<!-- Actions -->
		<div class="modal-actions">
			{#if showRejectReason}
				<button type="button" class="btn-cancel" onclick={cancelReject} disabled={isSubmitting}>
					Back
				</button>
				<button
					type="button"
					class="btn-reject"
					onclick={handleReject}
					disabled={isSubmitting || !rejectReason.trim()}
				>
					{isSubmitting ? 'Rejecting...' : 'Confirm Reject'}
				</button>
			{:else}
				<button type="button" class="btn-reject-outline" onclick={startReject} disabled={isSubmitting}>
					Reject
				</button>
				<button type="button" class="btn-approve" onclick={handleApprove} disabled={isSubmitting}>
					{isSubmitting ? 'Approving...' : 'Approve'}
				</button>
			{/if}
		</div>
	</div>
</BaseModal>

<style>
	.review-modal {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-5);
	}

	.request-header {
		text-align: center;
		padding-bottom: var(--spacing-4);
		border-bottom: 1px solid var(--color-surface-200);
	}

	.employee-name {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-900);
		margin: 0 0 var(--spacing-2) 0;
	}

	.change-type-badge {
		display: inline-block;
		padding: var(--spacing-1) var(--spacing-3);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		background: var(--color-primary-100);
		color: var(--color-primary-700);
		border-radius: var(--radius-full);
		margin-bottom: var(--spacing-2);
	}

	.submitted-date {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
		margin: 0;
	}

	.changes-section {
		overflow-x: auto;
	}

	.changes-table {
		width: 100%;
		border-collapse: collapse;
	}

	.changes-table th,
	.changes-table td {
		padding: var(--spacing-3);
		text-align: left;
		border-bottom: 1px solid var(--color-surface-200);
	}

	.changes-table th {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-600);
		background: var(--color-surface-50);
	}

	.field-label {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
	}

	.current-value {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
	}

	.requested-value {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-primary-600);
		background: var(--color-primary-50);
	}

	.attachments-section {
		padding: var(--spacing-4);
		background: var(--color-surface-50);
		border-radius: var(--radius-md);
	}

	.attachments-title {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
		margin: 0 0 var(--spacing-3) 0;
	}

	.attachments-list {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-2);
	}

	.attachment-link {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-1);
		padding: var(--spacing-2) var(--spacing-3);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-primary-600);
		background: white;
		border: 1px solid var(--color-primary-300);
		border-radius: var(--radius-md);
		text-decoration: none;
		transition: all var(--transition-fast);
	}

	.attachment-link:hover {
		background: var(--color-primary-50);
	}

	.attachment-link svg {
		width: 16px;
		height: 16px;
	}

	.reject-reason-section {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.reason-label {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
	}

	.reason-input {
		padding: var(--spacing-3);
		font-size: var(--font-size-body-content);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		resize: vertical;
	}

	.reason-input:focus {
		outline: none;
		border-color: var(--color-primary-500);
		box-shadow: 0 0 0 3px var(--color-primary-100);
	}

	.modal-actions {
		display: flex;
		justify-content: flex-end;
		gap: var(--spacing-3);
		padding-top: var(--spacing-4);
		border-top: 1px solid var(--color-surface-200);
	}

	.btn-cancel,
	.btn-reject,
	.btn-reject-outline,
	.btn-approve {
		padding: var(--spacing-3) var(--spacing-6);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.btn-cancel {
		background: transparent;
		color: var(--color-surface-600);
		border: 1px solid var(--color-surface-300);
	}

	.btn-cancel:hover:not(:disabled) {
		background: var(--color-surface-100);
	}

	.btn-reject-outline {
		background: transparent;
		color: var(--color-error-600);
		border: 1px solid var(--color-error-300);
	}

	.btn-reject-outline:hover:not(:disabled) {
		background: var(--color-error-50);
	}

	.btn-reject {
		background: var(--color-error-500);
		color: white;
		border: none;
	}

	.btn-reject:hover:not(:disabled) {
		background: var(--color-error-600);
	}

	.btn-approve {
		background: var(--color-success-500);
		color: white;
		border: none;
	}

	.btn-approve:hover:not(:disabled) {
		background: var(--color-success-600);
	}

	.btn-cancel:disabled,
	.btn-reject:disabled,
	.btn-reject-outline:disabled,
	.btn-approve:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
</style>

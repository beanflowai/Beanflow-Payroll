<script lang="ts">
	/**
	 * InviteToPortalModal - Send portal invitation to employee(s)
	 * Supports single invite and bulk invite
	 */
	import BaseModal from '$lib/shared-base/BaseModal.svelte';
	import type { EmployeeWithPortalStatus } from '$lib/types/employee-portal';
	import { inviteToPortal } from '$lib/services/employeePortalService';

	interface Props {
		visible: boolean;
		employees: EmployeeWithPortalStatus[];
		onclose: () => void;
		onInvite: (employeeIds: string[]) => void;
	}

	let { visible = $bindable(), employees, onclose, onInvite }: Props = $props();

	// Track selected employees for bulk invite
	// eslint-disable-next-line svelte/prefer-writable-derived -- Need mutable state synced from props
	let selectedIds = $state<Set<string>>(new Set());

	// Sync selectedIds when employees prop changes
	$effect(() => {
		// When employees change, select all by default
		selectedIds = new Set(employees.map((e) => e.id));
	});

	// Single employee mode if only one employee passed
	const isSingleMode = $derived(employees.length === 1);
	const singleEmployee = $derived(isSingleMode ? employees[0] : null);

	let isSubmitting = $state(false);
	let error = $state<string | null>(null);
	let warning = $state<string | null>(null);

	function toggleSelection(id: string) {
		if (selectedIds.has(id)) {
			selectedIds.delete(id);
		} else {
			selectedIds.add(id);
		}
		selectedIds = new Set(selectedIds); // Trigger reactivity
	}

	function toggleAll() {
		if (selectedIds.size === employees.length) {
			selectedIds = new Set();
		} else {
			selectedIds = new Set(employees.map((e) => e.id));
		}
	}

	async function handleSendInvitations() {
		if (selectedIds.size === 0) return;

		isSubmitting = true;
		error = null;
		warning = null;

		const ids = Array.from(selectedIds);
		const successfulIds: string[] = [];
		let failedCount = 0;

		try {
			// Send invitations to all selected employees
			const results = await Promise.allSettled(ids.map((id) => inviteToPortal(id, true)));

			// Track successes and failures
			results.forEach((result, index) => {
				if (result.status === 'fulfilled') {
					successfulIds.push(ids[index]);
				} else {
					failedCount++;
				}
			});

			if (failedCount > 0 && successfulIds.length === 0) {
				// All failed
				error = 'Failed to send invitations. Please try again.';
			} else if (failedCount > 0 && successfulIds.length > 0) {
				// Partial success - show warning but still notify parent of successful invites
				warning = `${successfulIds.length} invitation(s) sent successfully, ${failedCount} failed.`;
				onInvite(successfulIds);
				// Delay close to show the message
				setTimeout(() => onclose(), 2000);
			} else {
				// All succeeded
				onInvite(successfulIds);
				onclose();
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to send invitations';
		} finally {
			isSubmitting = false;
		}
	}
</script>

<BaseModal
	{visible}
	{onclose}
	size={isSingleMode ? 'small' : 'medium'}
	title={isSingleMode ? 'Invite to Portal' : 'Invite Employees to Portal'}
>
	<div class="invite-modal">
		{#if error}
			<div class="error-banner">{error}</div>
		{/if}
		{#if warning}
			<div class="warning-banner">{warning}</div>
		{/if}
		{#if isSingleMode && singleEmployee}
			<!-- Single Employee Mode -->
			<div class="single-employee-info">
				<p class="invite-description">
					Send a portal invitation to <strong
						>{singleEmployee.firstName} {singleEmployee.lastName}</strong
					>?
				</p>
				<p class="invite-email">
					An email will be sent to: <strong>{singleEmployee.email}</strong>
				</p>
			</div>
		{:else}
			<!-- Bulk Invite Mode -->
			<div class="bulk-select">
				<label class="select-all-option">
					<input
						type="checkbox"
						checked={selectedIds.size === employees.length}
						indeterminate={selectedIds.size > 0 && selectedIds.size < employees.length}
						onchange={toggleAll}
					/>
					<span class="select-label">
						Select All ({employees.filter((e) => e.portalStatus === 'not_set').length} without portal
						access)
					</span>
				</label>

				<div class="employee-list-divider"></div>

				<div class="employee-list">
					{#each employees as employee (employee.id)}
						<label class="employee-option">
							<input
								type="checkbox"
								checked={selectedIds.has(employee.id)}
								onchange={() => toggleSelection(employee.id)}
							/>
							<span class="employee-info">
								<span class="employee-name">{employee.firstName} {employee.lastName}</span>
								<span class="employee-email">{employee.email}</span>
							</span>
						</label>
					{/each}
				</div>
			</div>
		{/if}

		<!-- Email Preview -->
		<div class="email-preview">
			<h4 class="preview-title">Email Preview:</h4>
			<div class="preview-content">
				<p class="preview-subject">
					<strong>Subject:</strong> Access Your Employee Portal - [Company Name]
				</p>
				<div class="preview-body">
					<p>Hi [First Name],</p>
					<p>
						You've been invited to access your employee portal. Click the link below to view your
						payroll information, update your personal details, and download paystubs.
					</p>
					<div class="preview-button">[Access Portal Button]</div>
					<p class="preview-note">This link will expire in 7 days.</p>
				</div>
			</div>
		</div>

		<!-- Actions -->
		<div class="modal-actions">
			<button type="button" class="btn-cancel" onclick={onclose} disabled={isSubmitting}>
				Cancel
			</button>
			<button
				type="button"
				class="btn-send"
				onclick={handleSendInvitations}
				disabled={isSubmitting || selectedIds.size === 0}
			>
				{#if isSubmitting}
					Sending...
				{:else if isSingleMode}
					Send Invitation
				{:else}
					Send Invitations ({selectedIds.size})
				{/if}
			</button>
		</div>
	</div>
</BaseModal>

<style>
	.invite-modal {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-5);
	}

	.error-banner {
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-error-50);
		border: 1px solid var(--color-error-200);
		border-radius: var(--radius-md);
		color: var(--color-error-700);
		font-size: var(--font-size-auxiliary-text);
	}

	.warning-banner {
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-warning-50);
		border: 1px solid var(--color-warning-200);
		border-radius: var(--radius-md);
		color: var(--color-warning-700);
		font-size: var(--font-size-auxiliary-text);
	}

	.single-employee-info {
		text-align: center;
	}

	.invite-description {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
		margin: 0 0 var(--spacing-2) 0;
	}

	.invite-email {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
		margin: 0;
	}

	.bulk-select {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.select-all-option {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		cursor: pointer;
		padding: var(--spacing-2) 0;
	}

	.select-label {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.employee-list-divider {
		height: 1px;
		background: var(--color-surface-200);
	}

	.employee-list {
		max-height: 200px;
		overflow-y: auto;
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.employee-option {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-2);
		cursor: pointer;
		border-radius: var(--radius-md);
		transition: background var(--transition-fast);
	}

	.employee-option:hover {
		background: var(--color-surface-50);
	}

	.employee-info {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.employee-name {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-800);
	}

	.employee-email {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	.email-preview {
		background: var(--color-surface-50);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-md);
		padding: var(--spacing-4);
	}

	.preview-title {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
		margin: 0 0 var(--spacing-3) 0;
	}

	.preview-content {
		background: white;
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-sm);
		padding: var(--spacing-4);
	}

	.preview-subject {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-700);
		margin: 0 0 var(--spacing-3) 0;
		padding-bottom: var(--spacing-3);
		border-bottom: 1px solid var(--color-surface-200);
	}

	.preview-body {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
		line-height: 1.6;
	}

	.preview-body p {
		margin: 0 0 var(--spacing-2) 0;
	}

	.preview-button {
		display: inline-block;
		padding: var(--spacing-2) var(--spacing-4);
		background: var(--color-primary-100);
		color: var(--color-primary-600);
		border-radius: var(--radius-md);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		margin: var(--spacing-2) 0;
	}

	.preview-note {
		font-size: var(--font-size-caption-text);
		font-style: italic;
	}

	.modal-actions {
		display: flex;
		justify-content: flex-end;
		gap: var(--spacing-3);
		padding-top: var(--spacing-4);
		border-top: 1px solid var(--color-surface-200);
	}

	.btn-cancel,
	.btn-send {
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

	.btn-send {
		background: var(--color-primary-500);
		color: white;
		border: none;
	}

	.btn-send:hover:not(:disabled) {
		background: var(--color-primary-600);
	}

	.btn-cancel:disabled,
	.btn-send:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
</style>

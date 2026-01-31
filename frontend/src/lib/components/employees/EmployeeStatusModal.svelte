<script lang="ts">
	// EmployeeStatusModal - Change employee status modal
	import type { Employee, EmployeeStatus } from '$lib/types/employee';
	import { EMPLOYEE_STATUS_LABELS } from '$lib/types/employee';
	import { getCurrentLocalDate } from '$lib/utils/dateUtils';

	interface Props {
		employee: Employee;
		onClose: () => void;
		onConfirm: (newStatus: EmployeeStatus, terminationDate?: string) => void;
		isProcessing?: boolean;
	}

	let { employee, onClose, onConfirm, isProcessing = false }: Props = $props();

	// Determine target status based on current status
	const isTerminating = $derived(employee.status === 'active' || employee.status === 'draft');
	const targetStatus = $derived<EmployeeStatus>(isTerminating ? 'terminated' : 'active');

	// Termination date for terminating employees
	// Use getCurrentLocalDate() to avoid UTC offset issues (e.g., 10 PM local showing next day in UTC)
	let terminationDate = $state(getCurrentLocalDate());

	function handleConfirm() {
		if (isTerminating) {
			onConfirm(targetStatus, terminationDate);
		} else {
			onConfirm(targetStatus);
		}
	}

	function handleOverlayClick(event: MouseEvent) {
		if (event.target === event.currentTarget && !isProcessing) {
			onClose();
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && !isProcessing) {
			onClose();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<div class="modal-overlay" onclick={handleOverlayClick} role="presentation">
	<div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title" tabindex="-1">
		<div class="modal-header">
			<h2 id="modal-title" class="modal-title">Change Employee Status</h2>
			<button
				type="button"
				class="close-button"
				onclick={onClose}
				disabled={isProcessing}
				aria-label="Close"
			>
				<i class="fas fa-times"></i>
			</button>
		</div>

		<div class="modal-body">
			<div class="icon-container" class:terminate={isTerminating} class:reactivate={!isTerminating}>
				<i class="fas" class:fa-user-slash={isTerminating} class:fa-user-check={!isTerminating}></i>
			</div>

			<h3 class="confirm-title">
				{isTerminating ? 'Terminate' : 'Reactivate'} this employee?
			</h3>

			<div class="employee-info">
				<span class="employee-name">{employee.firstName} {employee.lastName}</span>
				<div class="status-change">
					<span
						class="status-badge"
						class:active={employee.status === 'active'}
						class:draft={employee.status === 'draft'}
						class:terminated={employee.status === 'terminated'}
					>
						{EMPLOYEE_STATUS_LABELS[employee.status]}
					</span>
					<i class="fas fa-arrow-right"></i>
					<span
						class="status-badge"
						class:active={targetStatus === 'active'}
						class:terminated={targetStatus === 'terminated'}
					>
						{EMPLOYEE_STATUS_LABELS[targetStatus]}
					</span>
				</div>
			</div>

			{#if isTerminating}
				<div class="form-field">
					<label for="termination-date">Termination Date</label>
					<input
						type="date"
						id="termination-date"
						bind:value={terminationDate}
						disabled={isProcessing}
					/>
				</div>
			{:else}
				<p class="info-text">
					Reactivating this employee will clear their termination date and restore them to active
					status.
				</p>
			{/if}
		</div>

		<div class="modal-footer">
			<button type="button" class="btn-secondary" onclick={onClose} disabled={isProcessing}>
				Cancel
			</button>
			<button
				type="button"
				class="btn-action"
				class:terminate={isTerminating}
				class:reactivate={!isTerminating}
				onclick={handleConfirm}
				disabled={isProcessing}
			>
				{#if isProcessing}
					<i class="fas fa-spinner fa-spin"></i>
					<span>Processing...</span>
				{:else if isTerminating}
					<i class="fas fa-user-slash"></i>
					<span>Terminate Employee</span>
				{:else}
					<i class="fas fa-user-check"></i>
					<span>Reactivate Employee</span>
				{/if}
			</button>
		</div>
	</div>
</div>

<style>
	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: var(--spacing-4);
	}

	.modal {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-3);
		width: 100%;
		max-width: 450px;
		overflow: hidden;
	}

	.modal-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--spacing-5) var(--spacing-6);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.modal-title {
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0;
	}

	.close-button {
		width: 32px;
		height: 32px;
		border: none;
		background: none;
		color: var(--color-surface-500);
		border-radius: var(--radius-md);
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: var(--transition-fast);
	}

	.close-button:hover:not(:disabled) {
		background: var(--color-surface-100);
		color: var(--color-surface-700);
	}

	.close-button:disabled {
		cursor: not-allowed;
		opacity: 0.5;
	}

	.modal-body {
		padding: var(--spacing-6);
		text-align: center;
	}

	.icon-container {
		width: 64px;
		height: 64px;
		border-radius: var(--radius-full);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 28px;
		margin: 0 auto var(--spacing-4);
	}

	.icon-container.terminate {
		background: var(--color-warning-100);
		color: var(--color-warning-600);
	}

	.icon-container.reactivate {
		background: var(--color-success-100);
		color: var(--color-success-600);
	}

	.confirm-title {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-4);
	}

	.employee-info {
		background: var(--color-surface-50);
		border: 1px solid var(--color-surface-100);
		border-radius: var(--radius-lg);
		padding: var(--spacing-4);
		margin-bottom: var(--spacing-4);
	}

	.employee-name {
		display: block;
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin-bottom: var(--spacing-3);
	}

	.status-change {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-3);
	}

	.status-change > i {
		color: var(--color-surface-400);
	}

	.status-badge {
		display: inline-block;
		padding: var(--spacing-1) var(--spacing-3);
		border-radius: var(--radius-full);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
	}

	.status-badge.active {
		background: var(--color-success-100);
		color: var(--color-success-700);
	}

	.status-badge.draft {
		background: var(--color-warning-100);
		color: var(--color-warning-700);
	}

	.status-badge.terminated {
		background: var(--color-surface-100);
		color: var(--color-surface-600);
	}

	.form-field {
		text-align: left;
	}

	.form-field label {
		display: block;
		font-size: var(--font-size-body-small);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
		margin-bottom: var(--spacing-2);
	}

	.form-field input {
		width: 100%;
		padding: var(--spacing-3);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-800);
		transition: var(--transition-fast);
	}

	.form-field input:focus {
		outline: none;
		border-color: var(--color-primary-400);
		box-shadow: 0 0 0 3px var(--color-primary-100);
	}

	.form-field input:disabled {
		background: var(--color-surface-50);
		cursor: not-allowed;
	}

	.info-text {
		font-size: var(--font-size-body-small);
		color: var(--color-surface-600);
		margin: 0;
		padding: var(--spacing-3);
		background: var(--color-info-50);
		border: 1px solid var(--color-info-200);
		border-radius: var(--radius-md);
	}

	.modal-footer {
		display: flex;
		justify-content: center;
		gap: var(--spacing-3);
		padding: var(--spacing-4) var(--spacing-6);
		border-top: 1px solid var(--color-surface-100);
		background: var(--color-surface-50);
	}

	/* Buttons */
	.btn-secondary,
	.btn-action {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-5);
		border: none;
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-secondary {
		background: white;
		color: var(--color-surface-700);
		border: 1px solid var(--color-surface-200);
	}

	.btn-secondary:hover:not(:disabled) {
		background: var(--color-surface-50);
		border-color: var(--color-surface-300);
	}

	.btn-secondary:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-action.terminate {
		background: var(--color-warning-500);
		color: white;
		box-shadow: var(--shadow-md3-1);
	}

	.btn-action.terminate:hover:not(:disabled) {
		background: var(--color-warning-600);
	}

	.btn-action.reactivate {
		background: var(--color-success-500);
		color: white;
		box-shadow: var(--shadow-md3-1);
	}

	.btn-action.reactivate:hover:not(:disabled) {
		background: var(--color-success-600);
	}

	.btn-action:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	@media (max-width: 640px) {
		.modal-footer {
			flex-direction: column;
		}

		.modal-footer button {
			width: 100%;
		}
	}
</style>

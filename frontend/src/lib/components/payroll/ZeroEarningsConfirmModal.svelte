<script lang="ts">
	interface ZeroEarningsEmployee {
		name: string;
		reason: string;
	}

	interface Props {
		employees: ZeroEarningsEmployee[];
		onClose: () => void;
		onConfirm: () => void;
		isConfirming?: boolean;
	}

	let { employees, onClose, onConfirm, isConfirming = false }: Props = $props();

	function handleOverlayClick(event: MouseEvent) {
		if (event.target === event.currentTarget && !isConfirming) {
			onClose();
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && !isConfirming) {
			onClose();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<div class="modal-overlay" onclick={handleOverlayClick} role="presentation">
	<div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title" tabindex="-1">
		<div class="modal-header">
			<h2 id="modal-title" class="modal-title">Employees with $0 Earnings</h2>
			<button
				type="button"
				class="close-button"
				onclick={onClose}
				disabled={isConfirming}
				aria-label="Close"
			>
				<i class="fas fa-times"></i>
			</button>
		</div>

		<div class="modal-body">
			<div class="icon-container">
				<i class="fas fa-exclamation-triangle"></i>
			</div>

			<h3 class="confirm-title">Some employees will be finalized with $0 earnings</h3>

			<p class="confirm-text">
				Review the list below. You can continue anyway or go back to update hours and earnings.
			</p>

			<div class="employee-list">
				{#if employees.length === 0}
					<div class="employee-empty">No employees found.</div>
				{:else}
					{#each employees as employee, index (index)}
						<div class="employee-row">
							<span class="employee-name">{employee.name}</span>
							<span class="employee-reason">{employee.reason}</span>
						</div>
					{/each}
				{/if}
			</div>
		</div>

		<div class="modal-footer">
			<button type="button" class="btn-secondary" onclick={onClose} disabled={isConfirming}>
				Cancel
			</button>
			<button type="button" class="btn-primary" onclick={onConfirm} disabled={isConfirming}>
				{#if isConfirming}
					<i class="fas fa-spinner fa-spin"></i>
					<span>Finalizing...</span>
				{:else}
					<span>Continue Anyway</span>
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
		max-width: 520px;
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
		background: var(--color-warning-100);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 28px;
		color: var(--color-warning-600);
		margin: 0 auto var(--spacing-4);
	}

	.confirm-title {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-3);
	}

	.confirm-text {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0 0 var(--spacing-4);
	}

	.employee-list {
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-lg);
		overflow: hidden;
		text-align: left;
		max-height: 220px;
		overflow-y: auto;
	}

	.employee-row {
		display: flex;
		justify-content: space-between;
		gap: var(--spacing-3);
		padding: var(--spacing-3) var(--spacing-4);
		border-bottom: 1px solid var(--color-surface-100);
		font-size: var(--font-size-body-small);
	}

	.employee-row:last-child {
		border-bottom: none;
	}

	.employee-name {
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.employee-reason {
		color: var(--color-surface-600);
		text-align: right;
	}

	.employee-empty {
		padding: var(--spacing-4);
		font-size: var(--font-size-body-small);
		color: var(--color-surface-500);
		text-align: center;
	}

	.modal-footer {
		display: flex;
		justify-content: center;
		gap: var(--spacing-3);
		padding: var(--spacing-4) var(--spacing-6);
		border-top: 1px solid var(--color-surface-100);
		background: var(--color-surface-50);
	}

	.btn-secondary,
	.btn-primary {
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

	.btn-primary {
		background: var(--color-primary-600);
		color: white;
		box-shadow: var(--shadow-md3-1);
	}

	.btn-primary:hover:not(:disabled) {
		background: var(--color-primary-700);
	}

	.btn-primary:disabled {
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

		.employee-row {
			flex-direction: column;
			align-items: flex-start;
		}

		.employee-reason {
			text-align: left;
		}
	}
</style>

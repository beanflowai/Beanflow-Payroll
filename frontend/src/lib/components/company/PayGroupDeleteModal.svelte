<script lang="ts">
	// PayGroupDeleteModal - Smart delete/deactivate modal
	// Checks for associated data and shows appropriate UI:
	// - Has data: Deactivate (soft delete)
	// - No data: Delete permanently (hard delete)

	import { onMount } from 'svelte';
	import type { PayGroup } from '$lib/types/pay-group';
	import { checkPayGroupHasAssociatedData } from '$lib/services/payGroupService';

	interface Props {
		payGroup: PayGroup;
		onClose: () => void;
		onConfirm: (action: 'hard_delete' | 'soft_delete') => void;
	}

	let { payGroup, onClose, onConfirm }: Props = $props();

	// State
	let isChecking = $state(true);
	let hasAssociatedData = $state(false);
	let employeeCount = $state(0);
	let payrollRunCount = $state(0);
	let checkError = $state<string | null>(null);
	let isProcessing = $state(false);

	onMount(async () => {
		const result = await checkPayGroupHasAssociatedData(payGroup.id);
		isChecking = false;

		if (result.error) {
			checkError = result.error;
			return;
		}

		hasAssociatedData = result.hasData;
		employeeCount = result.employeeCount;
		payrollRunCount = result.payrollRunCount;
	});

	function handleAction(action: 'hard_delete' | 'soft_delete') {
		isProcessing = true;
		onConfirm(action);
	}

	function handleOverlayClick(event: MouseEvent) {
		if (event.target === event.currentTarget && !isProcessing) {
			onClose();
		}
	}
</script>

<div class="modal-overlay" onclick={handleOverlayClick} role="presentation">
	<div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title" tabindex="-1">
		<div class="modal-header">
			<h2 id="modal-title" class="modal-title">
				{#if isChecking}
					Checking Pay Group...
				{:else if hasAssociatedData}
					Deactivate Pay Group
				{:else}
					Delete Pay Group
				{/if}
			</h2>
			<button class="close-button" onclick={onClose} aria-label="Close" disabled={isProcessing}>
				<i class="fas fa-times"></i>
			</button>
		</div>

		<div class="modal-body">
			{#if isChecking}
				<!-- Loading state -->
				<div class="checking-state">
					<div class="spinner-container">
						<i class="fas fa-spinner fa-spin"></i>
					</div>
					<p class="checking-text">Checking for associated data...</p>
				</div>
			{:else if checkError}
				<!-- Error state -->
				<div class="error-state">
					<div class="icon-container error">
						<i class="fas fa-exclamation-circle"></i>
					</div>
					<h3 class="confirm-title">Error Checking Data</h3>
					<p class="confirm-text">{checkError}</p>
				</div>
			{:else if hasAssociatedData}
				<!-- Soft delete UI -->
				<div class="icon-container warning">
					<i class="fas fa-archive"></i>
				</div>

				<h3 class="confirm-title">Deactivate "{payGroup.name}"?</h3>

				<p class="confirm-text">
					This pay group has associated data and cannot be permanently deleted.
				</p>

				<div class="associated-data-info">
					{#if employeeCount > 0}
						<div class="data-item">
							<i class="fas fa-users"></i>
							<span>{employeeCount} employee{employeeCount !== 1 ? 's' : ''} assigned</span>
						</div>
					{/if}
					{#if payrollRunCount > 0}
						<div class="data-item">
							<i class="fas fa-file-invoice-dollar"></i>
							<span>{payrollRunCount} payroll run{payrollRunCount !== 1 ? 's' : ''}</span>
						</div>
					{/if}
				</div>

				<div class="info-box">
					<i class="fas fa-info-circle"></i>
					<div class="info-content">
						<strong>What happens when deactivated?</strong>
						<ul>
							<li>Won't appear in employee dropdowns</li>
							<li>Won't be available for new payroll runs</li>
							<li>Historical data remains intact</li>
							<li>You can reactivate it anytime</li>
						</ul>
					</div>
				</div>
			{:else}
				<!-- Hard delete UI -->
				<div class="icon-container error">
					<i class="fas fa-trash"></i>
				</div>

				<h3 class="confirm-title">Delete "{payGroup.name}"?</h3>

				<p class="confirm-text">
					This pay group has no associated data and can be permanently deleted.
				</p>

				<div class="warning-box">
					<i class="fas fa-exclamation-triangle"></i>
					<div class="warning-content">
						<strong>This action cannot be undone</strong>
						<p>All policy configurations will be permanently removed.</p>
					</div>
				</div>
			{/if}
		</div>

		<div class="modal-footer">
			{#if isChecking}
				<button class="btn-secondary" onclick={onClose}>Cancel</button>
			{:else if checkError}
				<button class="btn-secondary" onclick={onClose}>Close</button>
			{:else if hasAssociatedData}
				<button class="btn-secondary" onclick={onClose} disabled={isProcessing}>Cancel</button>
				<button
					class="btn-warning"
					onclick={() => handleAction('soft_delete')}
					disabled={isProcessing}
				>
					{#if isProcessing}
						<i class="fas fa-spinner fa-spin"></i>
						<span>Deactivating...</span>
					{:else}
						<i class="fas fa-archive"></i>
						<span>Deactivate</span>
					{/if}
				</button>
			{:else}
				<button class="btn-secondary" onclick={onClose} disabled={isProcessing}>Cancel</button>
				<button
					class="btn-destructive"
					onclick={() => handleAction('hard_delete')}
					disabled={isProcessing}
				>
					{#if isProcessing}
						<i class="fas fa-spinner fa-spin"></i>
						<span>Deleting...</span>
					{:else}
						<span>Delete Permanently</span>
					{/if}
				</button>
			{/if}
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
		max-width: 480px;
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
		opacity: 0.5;
		cursor: not-allowed;
	}

	.modal-body {
		padding: var(--spacing-6);
		text-align: center;
	}

	/* Checking state */
	.checking-state {
		padding: var(--spacing-8) 0;
	}

	.spinner-container {
		width: 64px;
		height: 64px;
		margin: 0 auto var(--spacing-4);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 32px;
		color: var(--color-primary-500);
	}

	.checking-text {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0;
	}

	/* Error state */
	.error-state {
		padding: var(--spacing-4) 0;
	}

	/* Icon containers */
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

	.icon-container.error {
		background: var(--color-error-100);
		color: var(--color-error-500);
	}

	.icon-container.warning {
		background: var(--color-warning-100);
		color: var(--color-warning-600);
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

	/* Associated data info */
	.associated-data-info {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-surface-50);
		border-radius: var(--radius-lg);
		margin-bottom: var(--spacing-4);
	}

	.data-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-700);
	}

	.data-item i {
		width: 20px;
		color: var(--color-surface-500);
	}

	/* Info box (for soft delete) */
	.info-box {
		display: flex;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		background: var(--color-primary-50);
		border: 1px solid var(--color-primary-200);
		border-radius: var(--radius-lg);
		text-align: left;
	}

	.info-box > i {
		color: var(--color-primary-500);
		font-size: 18px;
		margin-top: 2px;
		flex-shrink: 0;
	}

	.info-content {
		flex: 1;
	}

	.info-content strong {
		display: block;
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-primary-700);
		margin-bottom: var(--spacing-2);
	}

	.info-content ul {
		margin: 0;
		padding-left: var(--spacing-4);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-700);
	}

	.info-content ul li {
		margin-bottom: var(--spacing-1);
	}

	/* Warning box (for hard delete) */
	.warning-box {
		display: flex;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		background: var(--color-warning-50);
		border: 1px solid var(--color-warning-200);
		border-radius: var(--radius-lg);
		text-align: left;
	}

	.warning-box > i {
		color: var(--color-warning-500);
		font-size: 18px;
		margin-top: 2px;
		flex-shrink: 0;
	}

	.warning-content {
		flex: 1;
	}

	.warning-content strong {
		display: block;
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-warning-700);
		margin-bottom: var(--spacing-2);
	}

	.warning-content p {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-700);
		margin: 0;
	}

	/* Footer */
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
	.btn-destructive,
	.btn-warning {
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

	.btn-destructive {
		background: var(--color-error-500);
		color: white;
		box-shadow: var(--shadow-md3-1);
	}

	.btn-destructive:hover:not(:disabled) {
		background: var(--color-error-600);
	}

	.btn-destructive:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-warning {
		background: var(--color-warning-500);
		color: white;
		box-shadow: var(--shadow-md3-1);
	}

	.btn-warning:hover:not(:disabled) {
		background: var(--color-warning-600);
	}

	.btn-warning:disabled {
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

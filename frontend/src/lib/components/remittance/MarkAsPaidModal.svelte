<script lang="ts">
	import { PAYMENT_METHOD_INFO } from '$lib/types/remittance';
	import type { RemittancePeriod, PaymentMethod } from '$lib/types/remittance';

	interface Props {
		remittance: RemittancePeriod;
		onClose: () => void;
		onSubmit: (data: {
			paymentDate: string;
			paymentMethod: PaymentMethod;
			confirmationNumber: string;
		}) => void;
	}

	let { remittance, onClose, onSubmit }: Props = $props();

	// Form state
	let paymentDate = $state(new Date().toISOString().split('T')[0]);
	let paymentMethod = $state<PaymentMethod>('my_payment');
	let confirmationNumber = $state('');

	// Helpers
	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			minimumFractionDigits: 2
		}).format(amount);
	}

	function formatDate(dateStr: string): string {
		return new Date(dateStr).toLocaleDateString('en-CA', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	function handleSubmit() {
		onSubmit({
			paymentDate,
			paymentMethod,
			confirmationNumber
		});
	}
</script>

<div class="modal-overlay" onclick={onClose} role="dialog" aria-modal="true">
	<div class="modal" onclick={(e) => e.stopPropagation()}>
		<div class="modal-header">
			<h2 class="modal-title">Record Remittance Payment</h2>
			<button class="modal-close" onclick={onClose} aria-label="Close">
				<i class="fas fa-times"></i>
			</button>
		</div>

		<div class="modal-body">
			<p class="modal-intro">You are recording payment for:</p>

			<div class="modal-summary">
				<div class="summary-row">
					<span class="summary-label">Period:</span>
					<span class="summary-value">{remittance.periodLabel}</span>
				</div>
				<div class="summary-row">
					<span class="summary-label">Amount:</span>
					<span class="summary-value">{formatCurrency(remittance.totalAmount)}</span>
				</div>
				<div class="summary-row">
					<span class="summary-label">Due Date:</span>
					<span class="summary-value">{formatDate(remittance.dueDate)}</span>
				</div>
			</div>

			<div class="modal-form">
				<div class="form-group">
					<label class="form-label" for="payment-date">Payment Date *</label>
					<input type="date" id="payment-date" class="form-input" bind:value={paymentDate} />
				</div>

				<div class="form-group">
					<label class="form-label" for="payment-method">Payment Method *</label>
					<select id="payment-method" class="form-select" bind:value={paymentMethod}>
						{#each Object.entries(PAYMENT_METHOD_INFO) as [value, info] (value)}
							<option {value}>{info.label}</option>
						{/each}
					</select>
				</div>

				<div class="form-group">
					<label class="form-label" for="confirmation">Confirmation Number (Optional)</label>
					<input
						type="text"
						id="confirmation"
						class="form-input"
						bind:value={confirmationNumber}
						placeholder="e.g., PAY-2025-12-001234"
					/>
				</div>
			</div>
		</div>

		<div class="modal-footer">
			<button class="btn-secondary" onclick={onClose}>Cancel</button>
			<button class="btn-primary" onclick={handleSubmit}>
				<i class="fas fa-check"></i>
				<span>Record Payment</span>
			</button>
		</div>
	</div>
</div>

<style>
	/* Modal Overlay */
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
		max-height: 90vh;
		overflow: auto;
	}

	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-5) var(--spacing-6);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.modal-title {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0;
	}

	.modal-close {
		width: 32px;
		height: 32px;
		border: none;
		background: none;
		color: var(--color-surface-500);
		cursor: pointer;
		border-radius: var(--radius-md);
		transition: var(--transition-fast);
	}

	.modal-close:hover {
		background: var(--color-surface-100);
		color: var(--color-surface-700);
	}

	.modal-body {
		padding: var(--spacing-6);
	}

	.modal-intro {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0 0 var(--spacing-4);
	}

	/* Summary */
	.modal-summary {
		background: var(--color-surface-50);
		border-radius: var(--radius-lg);
		padding: var(--spacing-4);
		margin-bottom: var(--spacing-6);
	}

	.summary-row {
		display: flex;
		justify-content: space-between;
		padding: var(--spacing-2) 0;
	}

	.summary-row:not(:last-child) {
		border-bottom: 1px solid var(--color-surface-100);
	}

	.summary-label {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
	}

	.summary-value {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	/* Form */
	.modal-form {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
	}

	.form-group {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.form-label {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
	}

	.form-input,
	.form-select {
		padding: var(--spacing-3) var(--spacing-4);
		background: white;
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-800);
		transition: var(--transition-fast);
	}

	.form-input:focus,
	.form-select:focus {
		outline: none;
		border-color: var(--color-primary-400);
		box-shadow: 0 0 0 3px var(--color-primary-100);
	}

	/* Footer */
	.modal-footer {
		display: flex;
		justify-content: flex-end;
		gap: var(--spacing-3);
		padding: var(--spacing-4) var(--spacing-6);
		border-top: 1px solid var(--color-surface-100);
	}

	/* Buttons */
	.btn-primary,
	.btn-secondary {
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

	.btn-primary {
		background: var(--gradient-primary);
		color: white;
		box-shadow: var(--shadow-md3-1);
	}

	.btn-primary:hover {
		opacity: 0.9;
		transform: translateY(-1px);
	}

	.btn-secondary {
		background: white;
		color: var(--color-surface-700);
		border: 1px solid var(--color-surface-200);
	}

	.btn-secondary:hover {
		background: var(--color-surface-50);
		border-color: var(--color-surface-300);
	}
</style>

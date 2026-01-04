<script lang="ts">
	// ConnectBookkeepingModal - Connect to bookkeeping ledger
	import type { BookkeepingLedger } from '$lib/types/company';

	interface Props {
		ledgers: BookkeepingLedger[];
		onClose: () => void;
		onConnect: (ledgerId: string) => void;
	}

	let { ledgers, onClose, onConnect }: Props = $props();

	let selectedLedgerId = $state('');
	let isConnecting = $state(false);
	let error = $state('');

	function handleConnect() {
		if (!selectedLedgerId) {
			error = 'Please select a company to connect';
			return;
		}

		isConnecting = true;
		error = '';

		// Simulate connection
		setTimeout(() => {
			isConnecting = false;
			onConnect(selectedLedgerId);
		}, 500);
	}

	function handleOverlayClick(event: MouseEvent) {
		if (event.target === event.currentTarget) {
			onClose();
		}
	}
</script>

<div class="modal-overlay" onclick={handleOverlayClick} role="presentation">
	<div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title" tabindex="-1">
		<div class="modal-header">
			<h2 id="modal-title" class="modal-title">Connect to Bookkeeping</h2>
			<button class="close-button" onclick={onClose} aria-label="Close">
				<i class="fas fa-times"></i>
			</button>
		</div>

		<div class="modal-body">
			<p class="description">Select a BeanFlow Bookkeeping company to link with your payroll.</p>

			<div class="form-group">
				<label class="form-label" for="ledger-select">Select Company *</label>
				<select
					id="ledger-select"
					class="form-select"
					class:error={!!error}
					bind:value={selectedLedgerId}
					onchange={() => (error = '')}
				>
					<option value="">Select a company...</option>
					{#each ledgers as ledger (ledger.id)}
						<option value={ledger.id}>{ledger.name}</option>
					{/each}
				</select>
				{#if error}
					<span class="form-error"><i class="fas fa-exclamation-circle"></i> {error}</span>
				{/if}
			</div>

			{#if selectedLedgerId}
				{@const selected = ledgers.find((l) => l.id === selectedLedgerId)}
				{#if selected}
					<div class="selected-ledger">
						<div class="ledger-icon">
							<i class="fas fa-book"></i>
						</div>
						<div class="ledger-details">
							<span class="ledger-name">{selected.name}</span>
							<span class="ledger-updated">Last updated: {selected.lastUpdated}</span>
						</div>
					</div>
				{/if}
			{/if}

			<div class="info-box">
				<i class="fas fa-info-circle"></i>
				<span> Only companies you have access to in BeanFlow Bookkeeping are shown here. </span>
			</div>
		</div>

		<div class="modal-footer">
			<button class="btn-secondary" onclick={onClose} disabled={isConnecting}>Cancel</button>
			<button class="btn-primary" onclick={handleConnect} disabled={isConnecting}>
				{#if isConnecting}
					<i class="fas fa-spinner fa-spin"></i>
					<span>Connecting...</span>
				{:else}
					<span>Connect</span>
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
		max-width: 500px;
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

	.close-button:hover {
		background: var(--color-surface-100);
		color: var(--color-surface-700);
	}

	.modal-body {
		padding: var(--spacing-6);
	}

	.description {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0 0 var(--spacing-5);
	}

	.modal-footer {
		display: flex;
		justify-content: flex-end;
		gap: var(--spacing-3);
		padding: var(--spacing-4) var(--spacing-6);
		border-top: 1px solid var(--color-surface-100);
		background: var(--color-surface-50);
	}

	/* Form */
	.form-group {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
		margin-bottom: var(--spacing-4);
	}

	.form-label {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
	}

	.form-select {
		padding: var(--spacing-3) var(--spacing-4);
		background: white;
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-800);
		transition: var(--transition-fast);
	}

	.form-select:focus {
		outline: none;
		border-color: var(--color-primary-400);
		box-shadow: 0 0 0 3px var(--color-primary-100);
	}

	.form-select.error {
		border-color: var(--color-error-400);
	}

	.form-error {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-error-600);
		display: flex;
		align-items: center;
		gap: var(--spacing-1);
	}

	/* Selected Ledger Preview */
	.selected-ledger {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		background: var(--color-primary-50);
		border: 1px solid var(--color-primary-200);
		border-radius: var(--radius-lg);
		margin-bottom: var(--spacing-4);
	}

	.ledger-icon {
		width: 40px;
		height: 40px;
		border-radius: var(--radius-md);
		background: var(--color-primary-100);
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--color-primary-600);
	}

	.ledger-details {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.ledger-name {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.ledger-updated {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	/* Info Box */
	.info-box {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-2);
		padding: var(--spacing-3);
		background: var(--color-surface-50);
		border-radius: var(--radius-md);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	.info-box i {
		color: var(--color-primary-500);
		margin-top: 2px;
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

	.btn-primary:hover:not(:disabled) {
		opacity: 0.9;
		transform: translateY(-1px);
	}

	.btn-primary:disabled {
		opacity: 0.6;
		cursor: not-allowed;
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

	@media (max-width: 640px) {
		.modal-footer {
			flex-direction: column;
		}

		.modal-footer button {
			width: 100%;
		}
	}
</style>

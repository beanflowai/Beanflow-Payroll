<script lang="ts">
	import { PROVINCES } from '$lib/types/company';
	import type { Province } from '$lib/types/employee';
	import { addCompany } from '$lib/stores/company.svelte';

	interface Props {
		isOpen: boolean;
		onClose: () => void;
		onSuccess?: () => void;
	}

	let { isOpen, onClose, onSuccess }: Props = $props();

	// Form state
	let companyName = $state('');
	let province = $state<Province>('ON');
	let businessNumber = $state('');
	let payrollAccountNumber = $state('');

	// UI state
	let isSubmitting = $state(false);
	let error = $state<string | null>(null);

	function resetForm() {
		companyName = '';
		province = 'ON';
		businessNumber = '';
		payrollAccountNumber = '';
		error = null;
	}

	function handleClose() {
		if (!isSubmitting) {
			resetForm();
			onClose();
		}
	}

	async function handleSubmit(event: Event) {
		event.preventDefault();

		if (!companyName.trim()) {
			error = 'Company name is required';
			return;
		}

		// Validate BN length if provided
		const bnTrimmed = businessNumber.trim();
		if (bnTrimmed && bnTrimmed.length !== 9) {
			error = 'Business number must be 9 digits';
			return;
		}

		// Validate Payroll Account length if provided
		const paTrimmed = payrollAccountNumber.trim();
		if (paTrimmed && paTrimmed.length !== 15) {
			error = 'Payroll account number must be 15 characters';
			return;
		}

		isSubmitting = true;
		error = null;

		const result = await addCompany({
			company_name: companyName.trim(),
			province,
			business_number: bnTrimmed,
			payroll_account_number: paTrimmed
		});

		isSubmitting = false;

		if (result.success) {
			resetForm();
			onSuccess?.();
			onClose();
		} else {
			error = result.error ?? 'Failed to create company';
		}
	}

	function handleBackdropClick(event: MouseEvent) {
		if (event.target === event.currentTarget) {
			handleClose();
		}
	}
</script>

{#if isOpen}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div class="modal-backdrop" onclick={handleBackdropClick} role="presentation">
		<div class="modal" role="dialog" aria-modal="true" aria-labelledby="add-company-title" tabindex="-1">
			<div class="modal-header">
				<h2 id="add-company-title" class="modal-title">Add New Company</h2>
				<button class="close-btn" onclick={handleClose} disabled={isSubmitting} aria-label="Close">
					<i class="fas fa-times"></i>
				</button>
			</div>

			<form onsubmit={handleSubmit}>
				<div class="modal-body">
					{#if error}
						<div class="error-alert">
							<i class="fas fa-exclamation-circle"></i>
							<span>{error}</span>
						</div>
					{/if}

					<div class="form-group">
						<label for="companyName" class="form-label">
							Company Name <span class="required">*</span>
						</label>
						<input
							type="text"
							id="companyName"
							class="form-input"
							bind:value={companyName}
							placeholder="Enter company name"
							disabled={isSubmitting}
							required
						/>
					</div>

					<div class="form-group">
						<label for="province" class="form-label">
							Province <span class="required">*</span>
						</label>
						<select
							id="province"
							class="form-select"
							bind:value={province}
							disabled={isSubmitting}
						>
							{#each PROVINCES as p (p.code)}
								<option value={p.code}>{p.name}</option>
							{/each}
						</select>
						<span class="form-hint">Primary province for payroll calculations</span>
					</div>

					<div class="form-group">
						<label for="businessNumber" class="form-label">Business Number (BN)</label>
						<input
							type="text"
							id="businessNumber"
							class="form-input"
							bind:value={businessNumber}
							placeholder="123456789"
							maxlength="9"
							disabled={isSubmitting}
						/>
						<span class="form-hint">9-digit CRA Business Number</span>
					</div>

					<div class="form-group">
						<label for="payrollAccountNumber" class="form-label">Payroll Account Number</label>
						<input
							type="text"
							id="payrollAccountNumber"
							class="form-input"
							bind:value={payrollAccountNumber}
							placeholder="123456789RP0001"
							maxlength="15"
							disabled={isSubmitting}
						/>
						<span class="form-hint">15-character CRA Payroll Account (e.g., 123456789RP0001)</span>
					</div>
				</div>

				<div class="modal-footer">
					<button type="button" class="btn btn-secondary" onclick={handleClose} disabled={isSubmitting}>
						Cancel
					</button>
					<button type="submit" class="btn btn-primary" disabled={isSubmitting}>
						{#if isSubmitting}
							<i class="fas fa-spinner fa-spin"></i>
							Creating...
						{:else}
							Create Company
						{/if}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}

<style>
	.modal-backdrop {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.4);
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
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}

	.modal-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--spacing-4) var(--spacing-5);
		border-bottom: 1px solid var(--color-surface-200);
	}

	.modal-title {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0;
	}

	.close-btn {
		width: 32px;
		height: 32px;
		border-radius: var(--radius-full);
		border: none;
		background: var(--color-surface-100);
		color: var(--color-surface-600);
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: var(--transition-fast);
	}

	.close-btn:hover:not(:disabled) {
		background: var(--color-surface-200);
		color: var(--color-surface-800);
	}

	.close-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.modal-body {
		padding: var(--spacing-5);
		overflow-y: auto;
	}

	.error-alert {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3);
		background: var(--color-error-50);
		border: 1px solid var(--color-error-200);
		border-radius: var(--radius-md);
		color: var(--color-error-700);
		font-size: var(--font-size-body-content);
		margin-bottom: var(--spacing-4);
	}

	.form-group {
		margin-bottom: var(--spacing-4);
	}

	.form-group:last-child {
		margin-bottom: 0;
	}

	.form-label {
		display: block;
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
		margin-bottom: var(--spacing-2);
	}

	.required {
		color: var(--color-error-500);
	}

	.form-input,
	.form-select {
		width: 100%;
		padding: var(--spacing-3);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-800);
		background: white;
		transition: var(--transition-fast);
	}

	.form-input:focus,
	.form-select:focus {
		outline: none;
		border-color: var(--color-primary-400);
		box-shadow: 0 0 0 3px var(--color-primary-100);
	}

	.form-input:disabled,
	.form-select:disabled {
		background: var(--color-surface-100);
		cursor: not-allowed;
	}

	.form-hint {
		display: block;
		font-size: var(--font-size-caption);
		color: var(--color-surface-500);
		margin-top: var(--spacing-1);
	}

	.modal-footer {
		display: flex;
		justify-content: flex-end;
		gap: var(--spacing-3);
		padding: var(--spacing-4) var(--spacing-5);
		border-top: 1px solid var(--color-surface-200);
		background: var(--color-surface-50);
	}

	.btn {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
		border: none;
	}

	.btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-secondary {
		background: white;
		color: var(--color-surface-700);
		border: 1px solid var(--color-surface-300);
	}

	.btn-secondary:hover:not(:disabled) {
		background: var(--color-surface-50);
		border-color: var(--color-surface-400);
	}

	.btn-primary {
		background: var(--gradient-primary);
		color: white;
	}

	.btn-primary:hover:not(:disabled) {
		box-shadow: var(--shadow-md3-2);
	}
</style>

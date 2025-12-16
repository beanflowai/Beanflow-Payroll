<script lang="ts">
	/**
	 * EditTaxInfoModal - Edit tax information form (TD1)
	 * Changes require employer approval
	 */
	import BaseModal from '$lib/shared-base/BaseModal.svelte';
	import type { TaxInfoFormData } from '$lib/types/employee-portal';
	import { TAX_CONSTANTS_2025 } from '$lib/types/employee-portal';

	interface Props {
		visible: boolean;
		initialData: {
			sin: string;
			federalClaimAmount: number;
			provincialClaimAmount: number;
			additionalTaxPerPeriod: number;
			provinceOfEmployment: string;
		};
		onclose: () => void;
		onSubmit: (data: TaxInfoFormData) => void;
	}

	let { visible = $bindable(), initialData, onclose, onSubmit }: Props = $props();

	// Get provincial BPA based on province
	const provincialBPA = TAX_CONSTANTS_2025.provincialBPA[initialData.provinceOfEmployment as keyof typeof TAX_CONSTANTS_2025.provincialBPA] || TAX_CONSTANTS_2025.provincialBPA.ON;

	// Form state
	let useBasicFederal = $state(initialData.federalClaimAmount === TAX_CONSTANTS_2025.federalBPA);
	let customFederalAmount = $state(initialData.federalClaimAmount);
	let useBasicProvincial = $state(initialData.provincialClaimAmount === provincialBPA);
	let customProvincialAmount = $state(initialData.provincialClaimAmount);
	let requestAdditionalTax = $state(initialData.additionalTaxPerPeriod > 0);
	let additionalTaxAmount = $state(initialData.additionalTaxPerPeriod);

	let isSubmitting = $state(false);

	const federalAmount = $derived(useBasicFederal ? TAX_CONSTANTS_2025.federalBPA : customFederalAmount);
	const provincialAmount = $derived(useBasicProvincial ? provincialBPA : customProvincialAmount);

	function formatMoney(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		}).format(amount);
	}

	function handleSubmit() {
		isSubmitting = true;

		const data: TaxInfoFormData = {
			federalClaimAmount: federalAmount,
			provincialClaimAmount: provincialAmount,
			additionalTaxPerPeriod: requestAdditionalTax ? additionalTaxAmount : 0,
			useBasicFederalAmount: useBasicFederal,
			useBasicProvincialAmount: useBasicProvincial
		};

		setTimeout(() => {
			isSubmitting = false;
			onSubmit(data);
			onclose();
		}, 500);
	}
</script>

<BaseModal {visible} {onclose} size="medium" title="Edit Tax Information">
	<form class="edit-form" onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
		<!-- Warning Banner -->
		<div class="warning-banner">
			<svg class="warning-icon" viewBox="0 0 20 20" fill="currentColor">
				<path
					fill-rule="evenodd"
					d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
					clip-rule="evenodd"
				/>
			</svg>
			<span>Changes to tax information will be reviewed by your employer before taking effect.</span>
		</div>

		<!-- SIN Display (read-only) -->
		<div class="form-group">
			<label class="form-label">Social Insurance Number (SIN)</label>
			<div class="sin-display">
				<span class="sin-value">{initialData.sin}</span>
				<span class="sin-note">Your SIN is encrypted and only visible to your employer.</span>
			</div>
		</div>

		<div class="form-divider"></div>

		<!-- Federal TD1 Claim Amount -->
		<div class="form-group">
			<label class="form-label">Federal TD1 Claim Amount</label>
			<div class="radio-group">
				<label class="radio-option">
					<input type="radio" bind:group={useBasicFederal} value={true} />
					<span class="radio-label">
						Basic Personal Amount: {formatMoney(TAX_CONSTANTS_2025.federalBPA)}
						<span class="radio-hint">(most employees)</span>
					</span>
				</label>
				<label class="radio-option">
					<input type="radio" bind:group={useBasicFederal} value={false} />
					<span class="radio-label">Custom amount from TD1 form:</span>
				</label>
				{#if !useBasicFederal}
					<div class="custom-amount-input">
						<span class="currency-prefix">$</span>
						<input
							type="number"
							class="form-input amount-input"
							bind:value={customFederalAmount}
							min="0"
							step="1"
						/>
					</div>
				{/if}
			</div>
			<p class="form-hint">
				Enter the total from Line 13 of your Federal TD1 form if different from the Basic Personal Amount.
			</p>
		</div>

		<!-- Provincial TD1 Claim Amount -->
		<div class="form-group">
			<label class="form-label">Provincial TD1 Claim Amount ({initialData.provinceOfEmployment})</label>
			<div class="radio-group">
				<label class="radio-option">
					<input type="radio" bind:group={useBasicProvincial} value={true} />
					<span class="radio-label">
						Basic Personal Amount: {formatMoney(provincialBPA)}
						<span class="radio-hint">(most employees)</span>
					</span>
				</label>
				<label class="radio-option">
					<input type="radio" bind:group={useBasicProvincial} value={false} />
					<span class="radio-label">Custom amount from TD1 form:</span>
				</label>
				{#if !useBasicProvincial}
					<div class="custom-amount-input">
						<span class="currency-prefix">$</span>
						<input
							type="number"
							class="form-input amount-input"
							bind:value={customProvincialAmount}
							min="0"
							step="1"
						/>
					</div>
				{/if}
			</div>
		</div>

		<div class="form-divider"></div>

		<!-- Additional Tax Deductions -->
		<div class="form-group">
			<label class="checkbox-option">
				<input type="checkbox" bind:checked={requestAdditionalTax} />
				<span class="checkbox-label">Request additional tax deductions each pay period</span>
			</label>
			{#if requestAdditionalTax}
				<div class="custom-amount-input" style="margin-top: var(--spacing-3)">
					<span class="currency-prefix">CA$</span>
					<input
						type="number"
						class="form-input amount-input"
						bind:value={additionalTaxAmount}
						min="0"
						step="1"
						placeholder="0"
					/>
				</div>
				<p class="form-hint">
					Some employees request extra tax be withheld to avoid owing at tax time.
				</p>
			{/if}
		</div>

		<!-- Actions -->
		<div class="form-actions">
			<button type="button" class="btn-cancel" onclick={onclose} disabled={isSubmitting}>
				Cancel
			</button>
			<button type="submit" class="btn-submit" disabled={isSubmitting}>
				{#if isSubmitting}
					Submitting...
				{:else}
					Submit for Review
				{/if}
			</button>
		</div>
	</form>
</BaseModal>

<style>
	.edit-form {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
	}

	.warning-banner {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		background: var(--color-warning-50);
		border: 1px solid var(--color-warning-200);
		border-radius: var(--radius-md);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-warning-800);
	}

	.warning-icon {
		width: 20px;
		height: 20px;
		flex-shrink: 0;
		color: var(--color-warning-500);
	}

	.form-group {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.form-label {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.sin-display {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.sin-value {
		font-family: monospace;
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
		padding: var(--spacing-3);
		background: var(--color-surface-100);
		border-radius: var(--radius-md);
	}

	.sin-note {
		display: flex;
		align-items: center;
		gap: var(--spacing-1);
		font-size: var(--font-size-caption-text);
		color: var(--color-surface-600);
	}

	.radio-group {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.radio-option {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-2);
		cursor: pointer;
	}

	.radio-option input[type='radio'] {
		margin-top: 3px;
	}

	.radio-label {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
	}

	.radio-hint {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.custom-amount-input {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		margin-left: var(--spacing-6);
	}

	.currency-prefix {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
	}

	.amount-input {
		max-width: 150px;
	}

	.form-input {
		padding: var(--spacing-3) var(--spacing-4);
		font-size: var(--font-size-body-content);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		transition: all var(--transition-fast);
	}

	.form-input:focus {
		outline: none;
		border-color: var(--color-primary-500);
		box-shadow: 0 0 0 3px var(--color-primary-100);
	}

	.form-hint {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
		margin: 0;
		line-height: 1.5;
	}

	.checkbox-option {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		cursor: pointer;
	}

	.checkbox-label {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
	}

	.form-divider {
		height: 1px;
		background: var(--color-surface-200);
		margin: var(--spacing-2) 0;
	}

	.form-actions {
		display: flex;
		justify-content: flex-end;
		gap: var(--spacing-3);
		margin-top: var(--spacing-4);
		padding-top: var(--spacing-4);
		border-top: 1px solid var(--color-surface-200);
	}

	.btn-cancel,
	.btn-submit {
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

	.btn-submit {
		background: var(--color-primary-500);
		color: white;
		border: none;
	}

	.btn-submit:hover:not(:disabled) {
		background: var(--color-primary-600);
	}

	.btn-cancel:disabled,
	.btn-submit:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
</style>

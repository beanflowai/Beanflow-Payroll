<script lang="ts">
	/**
	 * EditTaxInfoModal - Edit tax information form (TD1)
	 * Changes require employer approval
	 *
	 * UI follows BPA + Additional Claims pattern:
	 * - BPA is read-only (set by province)
	 * - User inputs only Additional Claims
	 * - Total = BPA + Additional Claims (auto-calculated)
	 */
	import BaseModal from '$lib/shared-base/BaseModal.svelte';
	import type { TaxInfoFormData } from '$lib/types/employee-portal';
	import { FEDERAL_BPA_2025, PROVINCIAL_BPA_2025, PROVINCE_LABELS, type Province } from '$lib/types/employee';

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

	// Get provincial BPA based on province (with fallback to ON for unsupported provinces like QC)
	const province = initialData.provinceOfEmployment as Province;
	const provincialBPA = PROVINCIAL_BPA_2025[province] ?? PROVINCIAL_BPA_2025.ON;
	const provinceName = PROVINCE_LABELS[province] ?? initialData.provinceOfEmployment;

	// Reverse-calculate additional claims from stored total
	function calculateAdditionalClaims(storedTotal: number, bpa: number): number {
		const additional = storedTotal - bpa;
		return additional > 0 ? additional : 0;
	}

	// Form state - user inputs Additional Claims only
	let federalAdditionalClaims = $state(calculateAdditionalClaims(initialData.federalClaimAmount, FEDERAL_BPA_2025));
	let provincialAdditionalClaims = $state(calculateAdditionalClaims(initialData.provincialClaimAmount, provincialBPA));
	let requestAdditionalTax = $state(initialData.additionalTaxPerPeriod > 0);
	let additionalTaxAmount = $state(initialData.additionalTaxPerPeriod);

	let isSubmitting = $state(false);

	// Derived: Total claim amounts (BPA + additional claims)
	const federalTotalClaim = $derived(FEDERAL_BPA_2025 + federalAdditionalClaims);
	const provincialTotalClaim = $derived(provincialBPA + provincialAdditionalClaims);

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
			federalClaimAmount: federalTotalClaim,
			provincialClaimAmount: provincialTotalClaim,
			additionalTaxPerPeriod: requestAdditionalTax ? additionalTaxAmount : 0,
			useBasicFederalAmount: federalAdditionalClaims === 0,
			useBasicProvincialAmount: provincialAdditionalClaims === 0
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

		<!-- Federal TD1 -->
		<div class="form-group">
			<label class="form-label">Federal TD1</label>
			<div class="claim-grid">
				<div class="claim-item">
					<span class="claim-sublabel">Basic Personal Amount (2025)</span>
					<div class="claim-value readonly">{formatMoney(FEDERAL_BPA_2025)}</div>
				</div>
				<div class="claim-item">
					<span class="claim-sublabel">Additional Claims</span>
					<div class="custom-amount-input">
						<span class="currency-prefix">$</span>
						<input
							type="number"
							class="form-input amount-input"
							bind:value={federalAdditionalClaims}
							min="0"
							step="1"
						/>
					</div>
				</div>
				<div class="claim-item">
					<span class="claim-sublabel">Total Claim Amount</span>
					<div class="claim-value total">{formatMoney(federalTotalClaim)}</div>
				</div>
			</div>
			<p class="form-hint">
				Enter additional claims from your TD1 form (spouse, dependants, disability, etc.) - the amount above the Basic Personal Amount.
			</p>
		</div>

		<!-- Provincial TD1 -->
		<div class="form-group">
			<label class="form-label">Provincial TD1 ({provinceName})</label>
			<div class="claim-grid">
				<div class="claim-item">
					<span class="claim-sublabel">Basic Personal Amount (2025)</span>
					<div class="claim-value readonly">{formatMoney(provincialBPA)}</div>
				</div>
				<div class="claim-item">
					<span class="claim-sublabel">Additional Claims</span>
					<div class="custom-amount-input">
						<span class="currency-prefix">$</span>
						<input
							type="number"
							class="form-input amount-input"
							bind:value={provincialAdditionalClaims}
							min="0"
							step="1"
						/>
					</div>
				</div>
				<div class="claim-item">
					<span class="claim-sublabel">Total Claim Amount</span>
					<div class="claim-value total">{formatMoney(provincialTotalClaim)}</div>
				</div>
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

	.claim-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: var(--spacing-3);
	}

	@media (max-width: 640px) {
		.claim-grid {
			grid-template-columns: 1fr;
		}
	}

	.claim-item {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.claim-sublabel {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	.claim-value {
		padding: var(--spacing-3);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
	}

	.claim-value.readonly {
		background: var(--color-surface-100);
		color: var(--color-surface-600);
	}

	.claim-value.total {
		background: var(--color-primary-50);
		border: 1px solid var(--color-primary-200);
		color: var(--color-primary-700);
		font-weight: var(--font-weight-semibold);
	}

	.custom-amount-input {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
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

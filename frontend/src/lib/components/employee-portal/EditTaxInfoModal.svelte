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
	import {
		FEDERAL_BPA_2025,
		PROVINCIAL_BPA_2025,
		PROVINCE_LABELS,
		PROVINCES_WITH_EDITION_DIFF,
		type Province
	} from '$lib/types/employee';
	import { getBPADefaults, type BPADefaults } from '$lib/services/taxConfigService';
	import { submitTaxChange } from '$lib/services/employeePortalService';
	import { formatCurrency } from '$lib/utils/formatUtils';

	interface Props {
		visible: boolean;
		initialData: {
			sin: string;
			federalAdditionalClaims: number;
			provincialAdditionalClaims: number;
			provinceOfEmployment: string;
		};
		onclose: () => void;
		onSubmit: (data: TaxInfoFormData) => void;
	}

	let { visible = $bindable(), initialData, onclose, onSubmit }: Props = $props();

	// Extract initial values once at component creation (form snapshot pattern)
	const initial = (() => {
		const data = initialData;
		return {
			province: data.provinceOfEmployment as Province,
			provinceName:
				PROVINCE_LABELS[data.provinceOfEmployment as Province] ?? data.provinceOfEmployment,
			federalAdditionalClaims: data.federalAdditionalClaims,
			provincialAdditionalClaims: data.provincialAdditionalClaims
		};
	})();

	// Get provincial BPA based on province (with fallback to ON for unsupported provinces like QC)
	const province = initial.province;
	const provinceName = initial.provinceName;

	// Dynamic BPA from API (with fallback to hardcoded values)
	let bpaDefaults = $state<BPADefaults | null>(null);
	let bpaLoading = $state(true);

	// Derived: Current BPA values (from API or fallback)
	const federalBPA = $derived(bpaDefaults?.federalBPA ?? FEDERAL_BPA_2025);
	const provincialBPA = $derived(
		bpaDefaults?.provincialBPA ?? PROVINCIAL_BPA_2025[province] ?? PROVINCIAL_BPA_2025.ON
	);

	// Form state - additional claims are now stored directly (no reverse calculation needed)
	let federalAdditionalClaims = $state(initial.federalAdditionalClaims);
	let provincialAdditionalClaims = $state(initial.provincialAdditionalClaims);

	// Track if BPA has been fetched (non-reactive to avoid loops)
	let bpaFetched = false;

	// Fetch BPA on mount for display purposes
	$effect(() => {
		if (province && !bpaFetched) {
			bpaFetched = true;
			bpaLoading = true;
			getBPADefaults(province)
				.then((defaults) => {
					bpaDefaults = defaults;
					bpaLoading = false;
				})
				.catch(() => {
					// Fallback values are already set via $derived
					bpaLoading = false;
				});
		}
	});

	let isSubmitting = $state(false);
	let error = $state<string | null>(null);
	let successMessage = $state<string | null>(null);

	// Derived: Total claim amounts (BPA + additional claims)
	const federalTotalClaim = $derived(federalBPA + federalAdditionalClaims);
	const provincialTotalClaim = $derived(provincialBPA + provincialAdditionalClaims);

	// Format currency with no decimals for cleaner display
	function formatCurrencyNoDecimals(amount: number): string {
		return formatCurrency(amount, { maximumFractionDigits: 0 });
	}

	async function handleSubmit() {
		isSubmitting = true;
		error = null;

		const data: TaxInfoFormData = {
			federalAdditionalClaims,
			provincialAdditionalClaims
		};

		try {
			await submitTaxChange(data);
			successMessage = 'Change request submitted for employer approval';
			onSubmit(data);
			// Delay close to show success message
			setTimeout(() => onclose(), 1500);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to submit change request';
			isSubmitting = false;
		}
	}
</script>

<BaseModal {visible} {onclose} size="medium" title="Edit Tax Information">
	<form
		class="edit-form"
		onsubmit={(e) => {
			e.preventDefault();
			handleSubmit();
		}}
	>
		{#if error}
			<div class="error-banner">{error}</div>
		{/if}
		{#if successMessage}
			<div class="success-banner">{successMessage}</div>
		{/if}
		<!-- Warning Banner -->
		<div class="warning-banner">
			<svg class="warning-icon" viewBox="0 0 20 20" fill="currentColor">
				<path
					fill-rule="evenodd"
					d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
					clip-rule="evenodd"
				/>
			</svg>
			<span>Changes to tax information will be reviewed by your employer before taking effect.</span
			>
		</div>

		<!-- SIN Display (read-only) -->
		<div class="form-group">
			<span class="form-label">Social Insurance Number (SIN)</span>
			<div class="sin-display">
				<span class="sin-value">{initialData.sin}</span>
				<span class="sin-note">Your SIN is encrypted and only visible to your employer.</span>
			</div>
		</div>

		<div class="form-divider"></div>

		<!-- Federal TD1 -->
		<div class="form-group">
			<span class="form-label">Federal TD1</span>
			<div class="claim-grid">
				<div class="claim-item">
					<span class="claim-sublabel">
						Basic Personal Amount
						{#if bpaDefaults}
							({bpaDefaults.year})
						{/if}
					</span>
					<div class="claim-value readonly">
						{#if bpaLoading}
							<span class="loading">Loading...</span>
						{:else}
							{formatCurrencyNoDecimals(federalBPA)}
						{/if}
					</div>
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
					<div class="claim-value total">{formatCurrencyNoDecimals(federalTotalClaim)}</div>
				</div>
			</div>
			<p class="form-hint">
				Enter additional claims from your TD1 form (spouse, dependants, disability, etc.) - the
				amount above the Basic Personal Amount.
			</p>
		</div>

		<!-- Provincial TD1 -->
		<div class="form-group">
			<span class="form-label">Provincial TD1 ({provinceName})</span>
			<div class="claim-grid">
				<div class="claim-item">
					<span class="claim-sublabel">
						Basic Personal Amount
						{#if bpaDefaults}
							({bpaDefaults.year})
						{/if}
					</span>
					<div class="claim-value readonly">
						{#if bpaLoading}
							<span class="loading">Loading...</span>
						{:else}
							{formatCurrencyNoDecimals(provincialBPA)}
							{#if bpaDefaults && PROVINCES_WITH_EDITION_DIFF.includes(province as (typeof PROVINCES_WITH_EDITION_DIFF)[number])}
								<span class="edition-note"
									>Edition: {bpaDefaults.edition === 'jan' ? 'January' : 'July'}</span
								>
							{/if}
						{/if}
					</div>
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
					<div class="claim-value total">{formatCurrencyNoDecimals(provincialTotalClaim)}</div>
				</div>
			</div>
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

	.error-banner {
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-error-50);
		border: 1px solid var(--color-error-200);
		border-radius: var(--radius-md);
		color: var(--color-error-700);
		font-size: var(--font-size-auxiliary-text);
	}

	.success-banner {
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-success-50);
		border: 1px solid var(--color-success-200);
		border-radius: var(--radius-md);
		color: var(--color-success-700);
		font-size: var(--font-size-auxiliary-text);
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

	.claim-value .loading {
		color: var(--color-surface-400);
		font-style: italic;
	}

	.edition-note {
		display: block;
		font-size: var(--font-size-caption-text);
		color: var(--color-surface-500);
		margin-top: var(--spacing-1);
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

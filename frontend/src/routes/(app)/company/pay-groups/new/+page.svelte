<script lang="ts">
	// Pay Group New Page - Create a new pay group
	import { goto } from '$app/navigation';
	import type { PayGroup } from '$lib/types/pay-group';
	import { createDefaultPayGroup } from '$lib/types/pay-group';
	import { createPayGroup, type PayGroupCreateInput } from '$lib/services/payGroupService';
	import { getOrCreateDefaultCompany } from '$lib/services/companyService';
	import PayGroupDetailHeader from '$lib/components/company/pay-group-detail/PayGroupDetailHeader.svelte';
	import PayGroupBasicInfoSection from '$lib/components/company/pay-group-detail/PayGroupBasicInfoSection.svelte';
	import PayGroupStatutorySection from '$lib/components/company/pay-group-detail/PayGroupStatutorySection.svelte';
	import PayGroupOvertimeSection from '$lib/components/company/pay-group-detail/PayGroupOvertimeSection.svelte';
	import PayGroupWcbSection from '$lib/components/company/pay-group-detail/PayGroupWcbSection.svelte';
	import PayGroupBenefitsSection from '$lib/components/company/pay-group-detail/PayGroupBenefitsSection.svelte';
	import PayGroupDeductionsSection from '$lib/components/company/pay-group-detail/PayGroupDeductionsSection.svelte';

	// State
	let companyId = $state<string | null>(null);
	let isLoadingCompany = $state(true);
	let isSaving = $state(false);
	let validationError = $state<string | null>(null);
	let error = $state<string | null>(null);

	// Create a new pay group with default values (temporary ID, will be replaced by server)
	const tempId = `temp-${Date.now()}`;
	const now = new Date().toISOString();

	let payGroup = $state<PayGroup>({
		...createDefaultPayGroup(''),
		id: tempId,
		createdAt: now,
		updatedAt: now
	});

	// Load company on mount
	$effect(() => {
		loadCompany();
	});

	async function loadCompany() {
		isLoadingCompany = true;
		error = null;

		try {
			const result = await getOrCreateDefaultCompany();
			if (result.error) {
				error = result.error;
				return;
			}
			if (!result.data) {
				error = 'No company found. Please create a company first.';
				return;
			}
			companyId = result.data.id;
			// Update payGroup with real companyId
			payGroup = { ...payGroup, companyId: result.data.id };
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load company';
		} finally {
			isLoadingCompany = false;
		}
	}

	// Handle back navigation
	function handleBack() {
		goto('/company?tab=pay-groups');
	}

	// Handle pay group updates from sections
	function handleUpdate(updatedPayGroup: PayGroup) {
		payGroup = updatedPayGroup;
		// Clear validation error when user makes changes
		validationError = null;
	}

	// Validate required fields
	function validate(): boolean {
		if (!payGroup.name.trim()) {
			validationError = 'Pay group name is required';
			return false;
		}
		if (!payGroup.nextPayDate) {
			validationError = 'Next pay date is required';
			return false;
		}
		// Check if next pay date is in the future
		const nextPayDateValue = new Date(payGroup.nextPayDate);
		const today = new Date();
		today.setHours(0, 0, 0, 0);
		if (nextPayDateValue <= today) {
			validationError = 'Next pay date must be in the future';
			return false;
		}
		return true;
	}

	// Handle save
	async function handleSave() {
		if (!validate()) return;
		if (!companyId) {
			error = 'No company found. Please create a company first.';
			return;
		}

		isSaving = true;
		error = null;

		// Build create input
		const createInput: PayGroupCreateInput = {
			company_id: companyId,
			name: payGroup.name,
			description: payGroup.description,
			pay_frequency: payGroup.payFrequency,
			employment_type: payGroup.employmentType,
			next_pay_date: payGroup.nextPayDate,
			period_start_day: payGroup.periodStartDay,
			leave_enabled: payGroup.leaveEnabled,
			statutory_defaults: payGroup.statutoryDefaults,
			overtime_policy: payGroup.overtimePolicy,
			wcb_config: payGroup.wcbConfig,
			group_benefits: payGroup.groupBenefits,
			earnings_config: payGroup.earningsConfig,
			taxable_benefits_config: payGroup.taxableBenefitsConfig,
			deductions_config: payGroup.deductionsConfig
		};

		try {
			const result = await createPayGroup(createInput);
			if (result.error) {
				error = result.error;
				return;
			}
			if (result.data) {
				// Navigate to the detail page
				goto(`/company/pay-groups/${result.data.id}`);
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to create pay group';
		} finally {
			isSaving = false;
		}
	}

	// Handle cancel
	function handleCancel() {
		goto('/company?tab=pay-groups');
	}
</script>

<svelte:head>
	<title>New Pay Group - BeanFlow Payroll</title>
</svelte:head>

<div class="pay-group-new-page">
	{#if isLoadingCompany}
		<!-- Loading State -->
		<div class="loading-container">
			<div class="loading-spinner"></div>
			<p>Loading...</p>
		</div>
	{:else if error && !companyId}
		<!-- No Company Error -->
		<div class="error-state">
			<i class="fas fa-building"></i>
			<h2>No Company Found</h2>
			<p>{error}</p>
			<button class="btn-primary" onclick={() => goto('/company?tab=profile')}>
				<i class="fas fa-arrow-left"></i>
				Go to Profile
			</button>
		</div>
	{:else}
		<!-- Header -->
		<PayGroupDetailHeader {payGroup} isNew={true} onBack={handleBack} onDelete={() => {}} />

		<!-- API Error -->
		{#if error}
			<div class="error-banner">
				<i class="fas fa-exclamation-circle"></i>
				<span>{error}</span>
				<button class="error-dismiss" onclick={() => error = null}>
					<i class="fas fa-times"></i>
				</button>
			</div>
		{/if}

		<!-- Validation Error -->
		{#if validationError}
			<div class="validation-error">
				<i class="fas fa-exclamation-circle"></i>
				<span>{validationError}</span>
			</div>
		{/if}

		<!-- Sections -->
		<div class="sections">
			<PayGroupBasicInfoSection {payGroup} onUpdate={handleUpdate} startInEditMode={true} />

			<PayGroupStatutorySection {payGroup} onUpdate={handleUpdate} />

			<PayGroupOvertimeSection {payGroup} onUpdate={handleUpdate} />

			<PayGroupWcbSection {payGroup} onUpdate={handleUpdate} />

			<PayGroupBenefitsSection {payGroup} onUpdate={handleUpdate} />

			<PayGroupDeductionsSection {payGroup} onUpdate={handleUpdate} />
		</div>

		<!-- Bottom Action Bar -->
		<div class="action-bar">
			<div class="action-bar-content">
				<button class="btn-cancel" onclick={handleCancel} disabled={isSaving}> Cancel </button>
				<button class="btn-save" onclick={handleSave} disabled={isSaving}>
					{#if isSaving}
						<i class="fas fa-spinner fa-spin"></i>
						<span>Creating...</span>
					{:else}
						<i class="fas fa-check"></i>
						<span>Create Pay Group</span>
					{/if}
				</button>
			</div>
		</div>
	{/if}
</div>

<style>
	.pay-group-new-page {
		max-width: 1000px;
		margin: 0 auto;
		padding: var(--spacing-6);
		padding-bottom: 100px; /* Space for action bar */
	}

	.validation-error {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-4);
		background: var(--color-error-50);
		border: 1px solid var(--color-error-200);
		border-radius: var(--radius-lg);
		color: var(--color-error-700);
		font-size: var(--font-size-body-content);
		margin-top: var(--spacing-4);
	}

	.validation-error i {
		color: var(--color-error-500);
	}

	.sections {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-6);
		margin-top: var(--spacing-6);
	}

	.action-bar {
		position: fixed;
		bottom: 0;
		left: 0;
		right: 0;
		background: white;
		border-top: 1px solid var(--color-surface-200);
		box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.1);
		padding: var(--spacing-4) var(--spacing-6);
		z-index: 100;
	}

	.action-bar-content {
		max-width: 1000px;
		margin: 0 auto;
		display: flex;
		justify-content: flex-end;
		gap: var(--spacing-3);
	}

	.btn-cancel,
	.btn-save {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-6);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-cancel {
		background: white;
		color: var(--color-surface-700);
		border: 1px solid var(--color-surface-300);
	}

	.btn-cancel:hover:not(:disabled) {
		background: var(--color-surface-50);
		border-color: var(--color-surface-400);
	}

	.btn-cancel:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.btn-save {
		background: var(--gradient-primary);
		color: white;
		border: none;
		box-shadow: var(--shadow-md3-1);
	}

	.btn-save:hover:not(:disabled) {
		opacity: 0.9;
		transform: translateY(-1px);
	}

	.btn-save:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	/* Loading State */
	.loading-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 400px;
		gap: var(--spacing-4);
	}

	.loading-spinner {
		width: 40px;
		height: 40px;
		border: 3px solid var(--color-surface-200);
		border-top-color: var(--color-primary-500);
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.loading-container p {
		color: var(--color-surface-500);
		margin: 0;
	}

	/* Error State */
	.error-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 400px;
		text-align: center;
		gap: var(--spacing-4);
	}

	.error-state i {
		font-size: 48px;
		color: var(--color-surface-400);
	}

	.error-state h2 {
		font-size: var(--font-size-title-large);
		color: var(--color-surface-800);
		margin: 0;
	}

	.error-state p {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0;
	}

	.btn-primary {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-5);
		background: var(--gradient-primary);
		color: white;
		border: none;
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-primary:hover {
		opacity: 0.9;
	}

	/* Error Banner */
	.error-banner {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		background: var(--color-error-50, #fef2f2);
		border: 1px solid var(--color-error-200, #fecaca);
		border-radius: var(--radius-lg);
		color: var(--color-error-700, #b91c1c);
		margin-top: var(--spacing-4);
	}

	.error-banner i:first-child {
		font-size: 1.25rem;
	}

	.error-banner span {
		flex: 1;
	}

	.error-dismiss {
		background: none;
		border: none;
		color: var(--color-error-500, #ef4444);
		cursor: pointer;
		padding: var(--spacing-1);
		opacity: 0.7;
	}

	.error-dismiss:hover {
		opacity: 1;
	}

	@media (max-width: 768px) {
		.pay-group-new-page {
			padding: var(--spacing-4);
			padding-bottom: 100px;
		}

		.action-bar-content {
			flex-direction: column;
		}

		.btn-cancel,
		.btn-save {
			width: 100%;
		}
	}
</style>

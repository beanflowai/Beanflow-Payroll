<script lang="ts">
	// Pay Group New Page - Create a new pay group
	import { goto } from '$app/navigation';
	import type { PayGroup } from '$lib/types/pay-group';
	import { createDefaultPayGroup } from '$lib/types/pay-group';
	import { createPayGroup, type PayGroupCreateInput } from '$lib/services/payGroupService';
	import { companyState } from '$lib/stores/company.svelte';
	import PayGroupDetailHeader from '$lib/components/company/pay-group-detail/PayGroupDetailHeader.svelte';
	import PayGroupBasicInfoSection from '$lib/components/company/pay-group-detail/PayGroupBasicInfoSection.svelte';
	import PayGroupOvertimeSection from '$lib/components/company/pay-group-detail/PayGroupOvertimeSection.svelte';
	import PayGroupWcbSection from '$lib/components/company/pay-group-detail/PayGroupWcbSection.svelte';
	import PayGroupBenefitsSection from '$lib/components/company/pay-group-detail/PayGroupBenefitsSection.svelte';
	import PayGroupDeductionsSection from '$lib/components/company/pay-group-detail/PayGroupDeductionsSection.svelte';
	import { Skeleton, AlertBanner, EmptyState } from '$lib/components/shared';

	// State
	let isSaving = $state(false);
	let validationError = $state<string | null>(null);
	let error = $state<string | null>(null);

	// Current company derived from store
	const currentCompany = $derived(companyState.currentCompany);
	const isLoadingCompany = $derived(companyState.isLoading);

	// Create a new pay group with default values (temporary ID, will be replaced by server)
	const tempId = `temp-${Date.now()}`;
	const now = new Date().toISOString();

	let payGroup = $state<PayGroup>({
		...createDefaultPayGroup(''),
		id: tempId,
		createdAt: now,
		updatedAt: now
	});

	// Update payGroup with companyId and province when company changes
	$effect(() => {
		if (currentCompany && payGroup.companyId !== currentCompany.id) {
			payGroup.companyId = currentCompany.id;
			payGroup.province = currentCompany.province;
		}
	});

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
	// NOTE: We intentionally do NOT validate that nextPeriodEnd is in the future.
	// This allows users to create pay groups with historical dates for scenarios like:
	// - Regenerating past payroll data
	// - System migration from another payroll system
	// - Correcting historical payroll records
	function validate(): boolean {
		if (!payGroup.name.trim()) {
			validationError = 'Pay group name is required';
			return false;
		}
		if (!payGroup.nextPeriodEnd) {
			validationError = 'Next period end date is required';
			return false;
		}
		return true;
	}

	// Handle save
	async function handleSave() {
		if (!validate()) return;
		if (!currentCompany) {
			error = 'No company found. Please create a company first.';
			return;
		}

		isSaving = true;
		error = null;

		// Build create input
		const createInput: PayGroupCreateInput = {
			company_id: currentCompany.id,
			name: payGroup.name,
			description: payGroup.description,
			pay_frequency: payGroup.payFrequency,
			employment_type: payGroup.employmentType,
			compensation_type: payGroup.compensationType,
			province: payGroup.province,
			next_period_end: payGroup.nextPeriodEnd,
			period_start_day: payGroup.periodStartDay,
			leave_enabled: payGroup.leaveEnabled,
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
		<div class="loading-skeleton">
			<div class="header-skeleton">
				<Skeleton variant="text" width="200px" height="32px" />
				<Skeleton variant="text" width="100px" height="24px" />
			</div>
			<Skeleton variant="rounded" height="300px" />
			<Skeleton variant="rounded" height="200px" />
		</div>
	{:else if error && !currentCompany}
		<!-- No Company Error -->
		<EmptyState
			icon="fa-building"
			title="No Company Found"
			description={error}
			actionLabel="Go to Profile"
			onAction={() => goto('/company?tab=profile')}
			variant="card"
		/>
	{:else}
		<!-- Header -->
		<PayGroupDetailHeader {payGroup} isNew={true} onBack={handleBack} onDelete={() => {}} />

		<!-- API Error -->
		{#if error}
			<div class="mt-4">
				<AlertBanner
					type="error"
					title="Error"
					message={error}
					dismissible={true}
					onDismiss={() => (error = null)}
				/>
			</div>
		{/if}

		<!-- Validation Error -->
		{#if validationError}
			<div class="mt-4">
				<AlertBanner type="warning" title="Validation Error" message={validationError} />
			</div>
		{/if}

		<!-- Sections -->
		<div class="sections">
			<PayGroupBasicInfoSection
				{payGroup}
				companyProvince={currentCompany?.province}
				onUpdate={handleUpdate}
				startInEditMode={true}
			/>

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

	/* Loading Skeleton */
	.loading-skeleton {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-6);
	}

	.header-skeleton {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
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

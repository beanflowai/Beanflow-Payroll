<script lang="ts">
	// Pay Group Detail Page
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import type { PayGroup } from '$lib/types/pay-group';
	import { getPayGroup, updatePayGroup, deletePayGroup, type PayGroupUpdateInput } from '$lib/services/payGroupService';
	import PayGroupDetailHeader from '$lib/components/company/pay-group-detail/PayGroupDetailHeader.svelte';
	import PayGroupSummaryCards from '$lib/components/company/pay-group-detail/PayGroupSummaryCards.svelte';
	import PayGroupBasicInfoSection from '$lib/components/company/pay-group-detail/PayGroupBasicInfoSection.svelte';
	import PayGroupStatutorySection from '$lib/components/company/pay-group-detail/PayGroupStatutorySection.svelte';
	import PayGroupOvertimeSection from '$lib/components/company/pay-group-detail/PayGroupOvertimeSection.svelte';
	import PayGroupWcbSection from '$lib/components/company/pay-group-detail/PayGroupWcbSection.svelte';
	import PayGroupBenefitsSection from '$lib/components/company/pay-group-detail/PayGroupBenefitsSection.svelte';
	import PayGroupDeductionsSection from '$lib/components/company/pay-group-detail/PayGroupDeductionsSection.svelte';
	import { companyState } from '$lib/stores/company.svelte';

	// Get pay group ID from route
	const payGroupId = $derived($page.params.id);

	// State
	let payGroup = $state<PayGroup | null>(null);
	let isLoading = $state(true);
	let isSaving = $state(false);
	let isDeleting = $state(false);
	let error = $state<string | null>(null);

	// Load pay group when company changes or ID changes
	$effect(() => {
		// Depend on currentCompany to reload when company switches
		const company = companyState.currentCompany;
		if (company && payGroupId) {
			loadPayGroupData(payGroupId);
		}
	});

	async function loadPayGroupData(id: string) {
		isLoading = true;
		error = null;

		try {
			const result = await getPayGroup(id);
			if (result.error) {
				error = result.error;
			} else if (result.data) {
				payGroup = result.data;
			} else {
				error = 'Pay Group not found';
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load pay group';
		} finally {
			isLoading = false;
		}
	}

	// Handle back navigation
	function handleBack() {
		goto('/company?tab=pay-groups');
	}

	// Handle delete
	async function handleDelete() {
		if (!payGroup) return;
		if (!confirm(`Delete "${payGroup.name}"? This action cannot be undone.`)) return;

		isDeleting = true;
		try {
			const result = await deletePayGroup(payGroup.id);
			if (result.error) {
				error = result.error;
			} else {
				goto('/company?tab=pay-groups');
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to delete pay group';
		} finally {
			isDeleting = false;
		}
	}

	// Handle pay group updates from sections
	async function handleUpdate(updatedPayGroup: PayGroup) {
		if (!payGroup) return;

		isSaving = true;
		error = null;

		// Build update input from the changed pay group
		const updateInput: PayGroupUpdateInput = {
			name: updatedPayGroup.name,
			description: updatedPayGroup.description,
			pay_frequency: updatedPayGroup.payFrequency,
			employment_type: updatedPayGroup.employmentType,
			next_period_end: updatedPayGroup.nextPeriodEnd,
			period_start_day: updatedPayGroup.periodStartDay,
			leave_enabled: updatedPayGroup.leaveEnabled,
			statutory_defaults: updatedPayGroup.statutoryDefaults,
			overtime_policy: updatedPayGroup.overtimePolicy,
			wcb_config: updatedPayGroup.wcbConfig,
			group_benefits: updatedPayGroup.groupBenefits,
			earnings_config: updatedPayGroup.earningsConfig,
			taxable_benefits_config: updatedPayGroup.taxableBenefitsConfig,
			deductions_config: updatedPayGroup.deductionsConfig
		};

		try {
			const result = await updatePayGroup(payGroup.id, updateInput);
			if (result.error) {
				error = result.error;
			} else if (result.data) {
				payGroup = result.data;
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to update pay group';
		} finally {
			isSaving = false;
		}
	}
</script>

<svelte:head>
	<title>{payGroup?.name ?? 'Pay Group'} - BeanFlow Payroll</title>
</svelte:head>

<div class="pay-group-detail-page">
	{#if isLoading}
		<div class="loading-state">
			<i class="fas fa-spinner fa-spin"></i>
			<span>Loading pay group...</span>
		</div>
	{:else if error}
		<div class="error-state">
			<i class="fas fa-exclamation-triangle"></i>
			<h2>Error</h2>
			<p>{error}</p>
			<button class="btn-primary" onclick={handleBack}>
				<i class="fas fa-arrow-left"></i>
				Back to Pay Groups
			</button>
		</div>
	{:else if payGroup}
		<!-- Save/Delete Error Banner -->
		{#if error && !isLoading}
			<div class="error-banner">
				<i class="fas fa-exclamation-circle"></i>
				<span>{error}</span>
				<button class="error-dismiss" onclick={() => error = null}>
					<i class="fas fa-times"></i>
				</button>
			</div>
		{/if}

		<!-- Saving Indicator -->
		{#if isSaving}
			<div class="saving-indicator">
				<i class="fas fa-spinner fa-spin"></i>
				<span>Saving changes...</span>
			</div>
		{/if}

		<!-- Header -->
		<PayGroupDetailHeader
			{payGroup}
			onBack={handleBack}
			onDelete={handleDelete}
		/>

		<!-- Summary Cards -->
		<div class="summary-cards-wrapper">
			<PayGroupSummaryCards {payGroup} />
		</div>

		<!-- Sections -->
		<div class="sections">
			<PayGroupBasicInfoSection
				{payGroup}
				onUpdate={handleUpdate}
			/>

			<PayGroupStatutorySection
				{payGroup}
				onUpdate={handleUpdate}
			/>

			<PayGroupOvertimeSection
				{payGroup}
				onUpdate={handleUpdate}
			/>

			<PayGroupWcbSection
				{payGroup}
				onUpdate={handleUpdate}
			/>

			<PayGroupBenefitsSection
				{payGroup}
				onUpdate={handleUpdate}
			/>

			<PayGroupDeductionsSection
				{payGroup}
				onUpdate={handleUpdate}
			/>
		</div>
	{/if}
</div>

<style>
	.pay-group-detail-page {
		max-width: 1000px;
		margin: 0 auto;
		padding: var(--spacing-6);
	}

	.loading-state,
	.error-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 400px;
		text-align: center;
		gap: var(--spacing-4);
	}

	.loading-state i {
		font-size: 32px;
		color: var(--color-primary-500);
	}

	.loading-state span {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
	}

	.error-state i {
		font-size: 48px;
		color: var(--color-error-500);
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

	.summary-cards-wrapper {
		margin-top: var(--spacing-5);
	}

	.sections {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-6);
		margin-top: var(--spacing-6);
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
		margin-bottom: var(--spacing-4);
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

	/* Saving Indicator */
	.saving-indicator {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-primary-50);
		border: 1px solid var(--color-primary-200);
		border-radius: var(--radius-lg);
		color: var(--color-primary-700);
		font-size: var(--font-size-body-content);
		margin-bottom: var(--spacing-4);
	}

	@media (max-width: 768px) {
		.pay-group-detail-page {
			padding: var(--spacing-4);
		}
	}
</style>

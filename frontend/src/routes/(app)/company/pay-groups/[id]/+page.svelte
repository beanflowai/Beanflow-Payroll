<script lang="ts">
	// Pay Group Detail Page
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import type { PayGroup } from '$lib/types/pay-group';
	import {
		getPayGroup,
		updatePayGroup,
		deletePayGroup,
		setPayGroupStatus,
		type PayGroupUpdateInput
	} from '$lib/services/payGroupService';
	import PayGroupDetailHeader from '$lib/components/company/pay-group-detail/PayGroupDetailHeader.svelte';
	import PayGroupSummaryCards from '$lib/components/company/pay-group-detail/PayGroupSummaryCards.svelte';
	import PayGroupBasicInfoSection from '$lib/components/company/pay-group-detail/PayGroupBasicInfoSection.svelte';
	import PayGroupOvertimeSection from '$lib/components/company/pay-group-detail/PayGroupOvertimeSection.svelte';
	import PayGroupWcbSection from '$lib/components/company/pay-group-detail/PayGroupWcbSection.svelte';
	import PayGroupBenefitsSection from '$lib/components/company/pay-group-detail/PayGroupBenefitsSection.svelte';
	import PayGroupDeductionsSection from '$lib/components/company/pay-group-detail/PayGroupDeductionsSection.svelte';
	import PayGroupDeleteModal from '$lib/components/company/PayGroupDeleteModal.svelte';
	import { companyState } from '$lib/stores/company.svelte';
	import { Skeleton, AlertBanner } from '$lib/components/shared';

	// Get pay group ID from route
	const payGroupId = $derived($page.params.id);

	// State
	let payGroup = $state<PayGroup | null>(null);
	let isLoading = $state(true);
	let isSaving = $state(false);
	let error = $state<string | null>(null);

	// Delete modal state
	let showDeleteModal = $state(false);

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

	// Handle delete button click - show modal
	function handleDelete() {
		if (!payGroup) return;
		showDeleteModal = true;
	}

	// Handle modal close
	function handleDeleteModalClose() {
		showDeleteModal = false;
	}

	// Handle delete confirmation from modal
	async function handleDeleteConfirm(action: 'hard_delete' | 'soft_delete') {
		if (!payGroup) return;

		try {
			if (action === 'hard_delete') {
				const result = await deletePayGroup(payGroup.id);
				if (result.error) {
					error = result.error;
				} else {
					goto('/company?tab=pay-groups');
				}
			} else {
				// soft_delete = set as inactive
				const result = await setPayGroupStatus(payGroup.id, false);
				if (result.error) {
					error = result.error;
				} else {
					goto('/company?tab=pay-groups');
				}
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to process pay group';
		} finally {
			handleDeleteModalClose();
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
			compensation_type: updatedPayGroup.compensationType,
			province: updatedPayGroup.province,
			next_period_end: updatedPayGroup.nextPeriodEnd,
			period_start_day: updatedPayGroup.periodStartDay,
			leave_enabled: updatedPayGroup.leaveEnabled,
			tax_calculation_method: updatedPayGroup.taxCalculationMethod,
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
		<div class="loading-skeleton">
			<div class="header-skeleton">
				<Skeleton variant="text" width="200px" height="32px" />
				<Skeleton variant="text" width="100px" height="24px" />
			</div>
			<div class="cards-skeleton">
				<Skeleton variant="rounded" height="100px" />
				<Skeleton variant="rounded" height="100px" />
				<Skeleton variant="rounded" height="100px" />
				<Skeleton variant="rounded" height="100px" />
			</div>
			<Skeleton variant="rounded" height="200px" />
			<Skeleton variant="rounded" height="150px" />
		</div>
	{:else if error && !payGroup}
		<AlertBanner type="error" title="Error" message={error}>
			<button class="btn-primary mt-3" onclick={handleBack}>
				<i class="fas fa-arrow-left"></i>
				Back to Pay Groups
			</button>
		</AlertBanner>
	{:else if payGroup}
		<!-- Save/Delete Error Banner -->
		{#if error && !isLoading}
			<AlertBanner
				type="error"
				title="Operation Failed"
				message={error}
				dismissible={true}
				onDismiss={() => (error = null)}
			/>
		{/if}

		<!-- Saving Indicator -->
		{#if isSaving}
			<AlertBanner type="info" title="Saving changes..." />
		{/if}

		<!-- Header -->
		<PayGroupDetailHeader {payGroup} onBack={handleBack} onDelete={handleDelete} />

		<!-- Summary Cards -->
		<div class="summary-cards-wrapper">
			<PayGroupSummaryCards {payGroup} />
		</div>

		<!-- Sections -->
		<div class="sections">
			<PayGroupBasicInfoSection {payGroup} onUpdate={handleUpdate} />

			<PayGroupOvertimeSection {payGroup} onUpdate={handleUpdate} />

			<PayGroupWcbSection {payGroup} onUpdate={handleUpdate} />

			<PayGroupBenefitsSection {payGroup} onUpdate={handleUpdate} />

			<PayGroupDeductionsSection {payGroup} onUpdate={handleUpdate} />
		</div>
	{/if}
</div>

<!-- Delete/Deactivate Confirmation Modal -->
{#if showDeleteModal && payGroup}
	<PayGroupDeleteModal
		{payGroup}
		onClose={handleDeleteModalClose}
		onConfirm={handleDeleteConfirm}
	/>
{/if}

<style>
	.pay-group-detail-page {
		max-width: 1000px;
		margin: 0 auto;
		padding: var(--spacing-6);
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

	.cards-skeleton {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: var(--spacing-4);
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

	@media (max-width: 768px) {
		.pay-group-detail-page {
			padding: var(--spacing-4);
		}
	}
</style>

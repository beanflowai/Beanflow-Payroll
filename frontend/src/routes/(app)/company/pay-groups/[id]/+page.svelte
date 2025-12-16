<script lang="ts">
	// Pay Group Detail Page
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import type { PayGroup } from '$lib/types/pay-group';
	import { getMockPayGroup } from '$lib/mocks/pay-groups';
	import PayGroupDetailHeader from '$lib/components/company/pay-group-detail/PayGroupDetailHeader.svelte';
	import PayGroupSummaryCards from '$lib/components/company/pay-group-detail/PayGroupSummaryCards.svelte';
	import PayGroupBasicInfoSection from '$lib/components/company/pay-group-detail/PayGroupBasicInfoSection.svelte';
	import PayGroupStatutorySection from '$lib/components/company/pay-group-detail/PayGroupStatutorySection.svelte';
	import PayGroupOvertimeSection from '$lib/components/company/pay-group-detail/PayGroupOvertimeSection.svelte';
	import PayGroupWcbSection from '$lib/components/company/pay-group-detail/PayGroupWcbSection.svelte';
	import PayGroupBenefitsSection from '$lib/components/company/pay-group-detail/PayGroupBenefitsSection.svelte';
	import PayGroupDeductionsSection from '$lib/components/company/pay-group-detail/PayGroupDeductionsSection.svelte';

	// Get pay group ID from route
	const payGroupId = $derived($page.params.id);

	// Load pay group data (using mock data)
	let payGroup = $state<PayGroup | null>(null);
	let isLoading = $state(true);
	let error = $state<string | null>(null);

	// Load pay group on mount
	$effect(() => {
		loadPayGroup(payGroupId);
	});

	function loadPayGroup(id: string) {
		isLoading = true;
		error = null;

		// Simulate async load with mock data
		setTimeout(() => {
			const found = getMockPayGroup(id);
			if (found) {
				payGroup = found;
			} else {
				error = 'Pay Group not found';
			}
			isLoading = false;
		}, 100);
	}

	// Handle back navigation
	function handleBack() {
		goto('/company?tab=pay-groups');
	}

	// Handle delete (would show confirmation modal in real app)
	function handleDelete() {
		if (confirm(`Delete "${payGroup?.name}"? This action cannot be undone.`)) {
			// In real app, call API to delete
			goto('/company?tab=pay-groups');
		}
	}

	// Handle pay group updates from sections
	function handleUpdate(updatedPayGroup: PayGroup) {
		payGroup = updatedPayGroup;
		// In real app, would save to backend
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
		<!-- Header -->
		<PayGroupDetailHeader
			{payGroup}
			onBack={handleBack}
			onDelete={handleDelete}
		/>

		<!-- Summary Cards -->
		<PayGroupSummaryCards {payGroup} />

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

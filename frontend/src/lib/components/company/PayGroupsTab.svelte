<script lang="ts">
	// PayGroupsTab - Pay Groups management (Tab 2)
	// Supports Active and Inactive pay groups with soft delete functionality
	import { goto } from '$app/navigation';
	import type { PayGroup } from '$lib/types/pay-group';
	import {
		listPayGroupsWithCounts,
		deletePayGroup,
		setPayGroupStatus,
		type PayGroupWithCount
	} from '$lib/services/payGroupService';
	import { companyState } from '$lib/stores/company.svelte';
	import PayGroupCard from './PayGroupCard.svelte';
	import PayGroupDeleteModal from './PayGroupDeleteModal.svelte';
	import { Skeleton, AlertBanner, EmptyState } from '$lib/components/shared';

	// State
	let activePayGroups = $state<PayGroupWithCount[]>([]);
	let inactivePayGroups = $state<PayGroupWithCount[]>([]);
	let isLoading = $state(true);
	let error = $state<string | null>(null);
	let companyId = $state<string | null>(null);
	let isInactiveExpanded = $state(false);

	// Delete modal state
	let showDeleteModal = $state(false);
	let deletingPayGroup = $state<PayGroup | null>(null);

	// Computed: is empty state (only active groups count)
	const isEmpty = $derived(activePayGroups.length === 0 && inactivePayGroups.length === 0);
	const hasNoCompany = $derived(!companyId && !isLoading);

	// Load data when company changes
	$effect(() => {
		const company = companyState.currentCompany;
		if (company) {
			companyId = company.id;
			loadPayGroups();
		} else {
			companyId = null;
			activePayGroups = [];
			inactivePayGroups = [];
			isLoading = false;
		}
	});

	async function loadPayGroups() {
		if (!companyId) return;

		isLoading = true;
		error = null;

		try {
			const result = await listPayGroupsWithCounts(companyId);
			if (result.error) {
				error = result.error;
				return;
			}

			// Separate active and inactive pay groups
			activePayGroups = result.data.filter((pg) => pg.isActive);
			inactivePayGroups = result.data.filter((pg) => !pg.isActive);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load pay groups';
		} finally {
			isLoading = false;
		}
	}

	function handleAddGroup() {
		// Navigate to the new pay group page
		goto('/company/pay-groups/new');
	}

	function handleViewGroup(payGroup: PayGroup) {
		// Navigate to the Pay Group detail page
		goto(`/company/pay-groups/${payGroup.id}`);
	}

	function handleDeleteGroup(payGroup: PayGroup) {
		deletingPayGroup = payGroup;
		showDeleteModal = true;
	}

	function handleDeleteModalClose() {
		showDeleteModal = false;
		deletingPayGroup = null;
	}

	async function handleActivate(payGroup: PayGroup) {
		try {
			const result = await setPayGroupStatus(payGroup.id, true);
			if (result.error) {
				error = result.error;
			} else {
				// Reload to update both lists
				await loadPayGroups();
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to activate pay group';
		}
	}

	async function handleDeleteConfirm(action: 'hard_delete' | 'soft_delete') {
		if (!deletingPayGroup) return;

		try {
			if (action === 'hard_delete') {
				const result = await deletePayGroup(deletingPayGroup.id);
				if (result.error) {
					error = result.error;
				} else {
					// Remove from both lists
					activePayGroups = activePayGroups.filter((pg) => pg.id !== deletingPayGroup!.id);
					inactivePayGroups = inactivePayGroups.filter((pg) => pg.id !== deletingPayGroup!.id);
				}
			} else {
				// soft_delete = set as inactive
				const result = await setPayGroupStatus(deletingPayGroup.id, false);
				if (result.error) {
					error = result.error;
				} else {
					// Reload to update both lists
					await loadPayGroups();
				}
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to process pay group';
		} finally {
			handleDeleteModalClose();
		}
	}

	function toggleInactiveSection() {
		isInactiveExpanded = !isInactiveExpanded;
	}
</script>

<div class="pay-groups-tab">
	<!-- Error Banner -->
	{#if error}
		<AlertBanner
			type="error"
			title="Error"
			message={error}
			dismissible={true}
			onDismiss={() => (error = null)}
		/>
	{/if}

	<!-- Loading State -->
	{#if isLoading}
		<div class="loading-skeleton">
			<Skeleton variant="rounded" height="60px" />
			<Skeleton variant="rounded" height="120px" />
			<Skeleton variant="rounded" height="120px" />
		</div>
	{:else if hasNoCompany}
		<!-- No Company State -->
		<EmptyState
			icon="fa-building"
			title="No Company Profile"
			description="Please set up your company profile first before creating pay groups."
			actionLabel="Go to Profile"
			onAction={() => goto('/company?tab=profile')}
			variant="card"
		/>
	{:else}
		<div class="tab-header">
			<div class="header-content">
				<h2 class="header-title">Pay Groups</h2>
				<p class="header-description">
					Organize employees by pay frequency and employment type. Each Pay Group is run separately
					in Payroll.
				</p>
			</div>
			<button class="btn-primary" onclick={handleAddGroup}>
				<i class="fas fa-plus"></i>
				<span>Add Group</span>
			</button>
		</div>

		{#if isEmpty}
			<!-- Empty State -->
			<div class="empty-state">
				<div class="empty-icon">
					<i class="fas fa-clipboard-list"></i>
				</div>
				<h3 class="empty-title">No Pay Groups Yet</h3>
				<p class="empty-description">
					Create your first pay group to start organizing employees by pay frequency and employment
					type.
				</p>
				<button class="btn-primary btn-lg" onclick={handleAddGroup}>
					<i class="fas fa-plus"></i>
					<span>Create Pay Group</span>
				</button>

				<div class="info-box">
					<div class="info-icon">
						<i class="fas fa-lightbulb"></i>
					</div>
					<div class="info-content">
						<h4 class="info-title">Why use Pay Groups?</h4>
						<ul class="info-list">
							<li>Run separate payrolls for different pay schedules</li>
							<li>Ensure correct tax calculations for each pay frequency</li>
							<li>Track leave policies per employment type</li>
						</ul>
					</div>
				</div>
			</div>
		{:else}
			<!-- Active Pay Groups Section -->
			{#if activePayGroups.length > 0}
				<div class="pay-groups-section">
					<h3 class="section-title">
						<i class="fas fa-check-circle"></i>
						Active Pay Groups ({activePayGroups.length})
					</h3>
					<div class="pay-groups-list">
						{#each activePayGroups as payGroup (payGroup.id)}
							<PayGroupCard {payGroup} onView={handleViewGroup} onDelete={handleDeleteGroup} />
						{/each}
					</div>
				</div>
			{:else}
				<!-- No Active Pay Groups -->
				<div class="no-active-state">
					<i class="fas fa-info-circle"></i>
					<span>No active pay groups. Create a new one or reactivate an inactive group below.</span>
				</div>
			{/if}

			<!-- Inactive Pay Groups Section (Collapsible) -->
			{#if inactivePayGroups.length > 0}
				<div class="pay-groups-section inactive-section">
					<button class="section-header-btn" onclick={toggleInactiveSection}>
						<i class="fas fa-chevron-{isInactiveExpanded ? 'down' : 'right'}"></i>
						<h3 class="section-title">
							<i class="fas fa-archive"></i>
							Inactive Pay Groups ({inactivePayGroups.length})
						</h3>
					</button>

					{#if isInactiveExpanded}
						<div class="pay-groups-list">
							{#each inactivePayGroups as payGroup (payGroup.id)}
								<PayGroupCard
									{payGroup}
									onView={handleViewGroup}
									onDelete={handleDeleteGroup}
									onActivate={handleActivate}
									isInactive={true}
								/>
							{/each}
						</div>
					{/if}
				</div>
			{/if}

			<!-- Info Note -->
			<div class="info-note">
				<i class="fas fa-info-circle"></i>
				<span>
					Employees must be assigned to a Pay Group before they can be included in a payroll run.
					Go to <a href="/employees">Employees</a> to assign groups.
				</span>
			</div>
		{/if}
	{/if}
</div>

<!-- Delete/Deactivate Confirmation Modal -->
{#if showDeleteModal && deletingPayGroup}
	<PayGroupDeleteModal
		payGroup={deletingPayGroup}
		onClose={handleDeleteModalClose}
		onConfirm={handleDeleteConfirm}
	/>
{/if}

<style>
	.pay-groups-tab {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-6);
	}

	.tab-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: var(--spacing-4);
	}

	.header-content {
		flex: 1;
	}

	.header-title {
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-1);
	}

	.header-description {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0;
		max-width: 600px;
	}

	/* Pay Groups Sections */
	.pay-groups-section {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
	}

	.section-title {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-700);
		margin: 0;
	}

	.section-title i {
		font-size: 14px;
	}

	.section-title i.fa-check-circle {
		color: var(--color-success-500);
	}

	.section-title i.fa-archive {
		color: var(--color-surface-400);
	}

	/* Inactive Section */
	.inactive-section {
		padding: var(--spacing-4);
		background: var(--color-surface-50);
		border-radius: var(--radius-lg);
		border: 1px solid var(--color-surface-100);
	}

	.section-header-btn {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		width: 100%;
		padding: 0;
		background: none;
		border: none;
		cursor: pointer;
		text-align: left;
		color: var(--color-surface-600);
		transition: var(--transition-fast);
	}

	.section-header-btn:hover {
		color: var(--color-surface-800);
	}

	.section-header-btn > i {
		font-size: 12px;
		width: 16px;
		color: var(--color-surface-400);
	}

	.inactive-section .pay-groups-list {
		margin-top: var(--spacing-4);
	}

	/* No Active State */
	.no-active-state {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-4);
		background: var(--color-warning-50);
		border: 1px solid var(--color-warning-200);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		color: var(--color-warning-700);
	}

	.no-active-state i {
		color: var(--color-warning-500);
	}

	/* Empty State */
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
		padding: var(--spacing-12) var(--spacing-6);
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
	}

	.empty-icon {
		width: 80px;
		height: 80px;
		border-radius: var(--radius-full);
		background: var(--color-surface-100);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 32px;
		color: var(--color-surface-400);
		margin-bottom: var(--spacing-4);
	}

	.empty-title {
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-2);
	}

	.empty-description {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0 0 var(--spacing-6);
		max-width: 400px;
	}

	.info-box {
		display: flex;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		background: var(--color-primary-50);
		border-radius: var(--radius-lg);
		text-align: left;
		margin-top: var(--spacing-8);
		max-width: 500px;
	}

	.info-icon {
		width: 32px;
		height: 32px;
		border-radius: var(--radius-md);
		background: var(--color-primary-100);
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--color-primary-600);
		flex-shrink: 0;
	}

	.info-content {
		flex: 1;
	}

	.info-title {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-2);
	}

	.info-list {
		margin: 0;
		padding-left: var(--spacing-4);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	.info-list li {
		margin-bottom: var(--spacing-1);
	}

	/* Pay Groups List */
	.pay-groups-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
	}

	/* Info Note */
	.info-note {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-2);
		padding: var(--spacing-4);
		background: var(--color-surface-50);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
	}

	.info-note i {
		color: var(--color-primary-500);
		margin-top: 2px;
	}

	.info-note a {
		color: var(--color-primary-600);
		font-weight: var(--font-weight-medium);
		text-decoration: none;
	}

	.info-note a:hover {
		text-decoration: underline;
	}

	/* Buttons */
	.btn-primary {
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
		background: var(--gradient-primary);
		color: white;
		box-shadow: var(--shadow-md3-1);
		white-space: nowrap;
	}

	.btn-primary:hover {
		opacity: 0.9;
		transform: translateY(-1px);
	}

	.btn-lg {
		padding: var(--spacing-4) var(--spacing-6);
		font-size: var(--font-size-title-medium);
	}

	/* Loading Skeleton */
	.loading-skeleton {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
	}

	@media (max-width: 640px) {
		.tab-header {
			flex-direction: column;
		}

		.btn-primary {
			width: 100%;
		}
	}
</style>

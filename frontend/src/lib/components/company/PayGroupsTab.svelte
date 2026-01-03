<script lang="ts">
	// PayGroupsTab - Pay Groups management (Tab 2)
	import { goto } from '$app/navigation';
	import type { PayGroup } from '$lib/types/pay-group';
	import { listPayGroupsWithCounts, deletePayGroup, type PayGroupWithCount } from '$lib/services/payGroupService';
	import { companyState } from '$lib/stores/company.svelte';
	import PayGroupCard from './PayGroupCard.svelte';
	import PayGroupDeleteModal from './PayGroupDeleteModal.svelte';

	// State
	let payGroups = $state<PayGroupWithCount[]>([]);
	let isLoading = $state(true);
	let error = $state<string | null>(null);
	let companyId = $state<string | null>(null);

	// Delete modal state
	let showDeleteModal = $state(false);
	let deletingPayGroup = $state<PayGroup | null>(null);
	let isDeleting = $state(false);

	// Computed: is empty state
	const isEmpty = $derived(payGroups.length === 0);
	const hasNoCompany = $derived(!companyId && !isLoading);

	// Load data when company changes
	$effect(() => {
		const company = companyState.currentCompany;
		if (company) {
			companyId = company.id;
			loadPayGroups();
		} else {
			companyId = null;
			payGroups = [];
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

			payGroups = result.data;
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

	async function handleDeleteConfirm() {
		if (!deletingPayGroup) return;

		isDeleting = true;
		try {
			const result = await deletePayGroup(deletingPayGroup.id);
			if (result.error) {
				error = result.error;
			} else {
				payGroups = payGroups.filter((pg) => pg.id !== deletingPayGroup!.id);
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to delete pay group';
		} finally {
			isDeleting = false;
			handleDeleteModalClose();
		}
	}
</script>

<div class="pay-groups-tab">
	<!-- Error Banner -->
	{#if error}
		<div class="error-banner">
			<i class="fas fa-exclamation-circle"></i>
			<span>{error}</span>
			<button class="error-dismiss" onclick={() => error = null} aria-label="Dismiss error">
				<i class="fas fa-times"></i>
			</button>
		</div>
	{/if}

	<!-- Loading State -->
	{#if isLoading}
		<div class="loading-container">
			<div class="loading-spinner"></div>
			<p>Loading pay groups...</p>
		</div>
	{:else if hasNoCompany}
		<!-- No Company State -->
		<div class="no-company-state">
			<div class="empty-icon">
				<i class="fas fa-building"></i>
			</div>
			<h3 class="empty-title">No Company Profile</h3>
			<p class="empty-description">
				Please set up your company profile first before creating pay groups.
			</p>
			<button class="btn-primary" onclick={() => goto('/company?tab=profile')}>
				<i class="fas fa-arrow-left"></i>
				<span>Go to Profile</span>
			</button>
		</div>
	{:else}
		<div class="tab-header">
			<div class="header-content">
				<h2 class="header-title">Pay Groups</h2>
				<p class="header-description">
					Organize employees by pay frequency and employment type. Each Pay Group is run separately in
					Payroll.
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
		<!-- Pay Groups List -->
		<div class="pay-groups-list">
			{#each payGroups as payGroup (payGroup.id)}
				<PayGroupCard {payGroup} onView={handleViewGroup} onDelete={handleDeleteGroup} />
			{/each}
		</div>

		<!-- Info Note -->
		<div class="info-note">
			<i class="fas fa-info-circle"></i>
			<span>
				Employees must be assigned to a Pay Group before they can be included in a payroll run. Go
				to <a href="/employees">Employees</a> to assign groups.
			</span>
		</div>
		{/if}
	{/if}
</div>

<!-- Delete Confirmation Modal -->
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

	/* Loading State */
	.loading-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-12) var(--spacing-6);
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

	/* No Company State */
	.no-company-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
		padding: var(--spacing-12) var(--spacing-6);
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
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

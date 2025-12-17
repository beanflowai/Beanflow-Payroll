<script lang="ts">
	import type { UpcomingPayDate, PayrollPageStatus } from '$lib/types/payroll';
	import { PayDateCard } from '$lib/components/payroll';
	import {
		checkPayrollPageStatus,
		getUpcomingPayDates
	} from '$lib/services/payrollService';

	// ===========================================
	// State
	// ===========================================
	let pageStatus = $state<PayrollPageStatus | null>(null);
	let upcomingPayDates = $state<UpcomingPayDate[]>([]);
	let isLoading = $state(true);
	let error = $state<string | null>(null);

	// ===========================================
	// Load Data
	// ===========================================
	async function loadData() {
		isLoading = true;
		error = null;

		try {
			// Check page status first
			const statusResult = await checkPayrollPageStatus();
			if (statusResult.error) {
				error = statusResult.error;
				return;
			}
			pageStatus = statusResult.data;

			// If ready or no_employees, load upcoming pay dates
			if (pageStatus?.status === 'ready' || pageStatus?.status === 'no_employees') {
				const payDatesResult = await getUpcomingPayDates();
				if (payDatesResult.error) {
					error = payDatesResult.error;
					return;
				}
				upcomingPayDates = payDatesResult.data ?? [];
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load payroll data';
		} finally {
			isLoading = false;
		}
	}

	// Load data on mount
	$effect(() => {
		loadData();
	});

	// ===========================================
	// Computed
	// ===========================================
	const totalUpcoming = $derived(upcomingPayDates.length);
	const nextPayDate = $derived(upcomingPayDates.length > 0 ? upcomingPayDates[0] : null);

	// ===========================================
	// Helpers
	// ===========================================
	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		}).format(amount);
	}

	function formatDate(dateStr: string): string {
		return new Date(dateStr).toLocaleDateString('en-CA', {
			weekday: 'short',
			month: 'short',
			day: 'numeric'
		});
	}
</script>

<svelte:head>
	<title>Run Payroll - BeanFlow Payroll</title>
</svelte:head>

{#if isLoading}
	<!-- Loading State -->
	<div class="loading-state">
		<div class="loading-spinner"></div>
		<p>Loading payroll data...</p>
	</div>
{:else if error}
	<!-- Error State -->
	<div class="error-state">
		<div class="error-icon">
			<i class="fas fa-exclamation-triangle"></i>
		</div>
		<h3>Error Loading Payroll</h3>
		<p>{error}</p>
		<button class="btn-primary" onclick={() => loadData()}>
			<i class="fas fa-redo"></i>
			<span>Try Again</span>
		</button>
	</div>
{:else if pageStatus?.status === 'no_pay_groups'}
	<!-- No Pay Groups State -->
	<div class="payroll-dashboard">
		<header class="page-header">
			<div class="header-content">
				<h1 class="page-title">Run Payroll</h1>
				<p class="page-subtitle">Get started by creating your first pay group</p>
			</div>
		</header>

		<div class="empty-state-large">
			<div class="empty-icon">
				<i class="fas fa-layer-group"></i>
			</div>
			<h3>No Pay Groups Yet</h3>
			<p>Create a pay group to organize employees by pay frequency and configure payroll settings.</p>
			<a href="/company?tab=pay-groups" class="btn-primary">
				<i class="fas fa-plus"></i>
				<span>Create Pay Group</span>
			</a>
		</div>
	</div>
{:else if pageStatus?.status === 'no_employees' || pageStatus?.status === 'ready'}
	<!-- Ready State - Normal Dashboard -->
	<div class="payroll-dashboard">
		<!-- Header -->
		<header class="page-header">
			<div class="header-content">
				<h1 class="page-title">Run Payroll</h1>
				<p class="page-subtitle">Manage upcoming payroll runs for all pay groups</p>
			</div>
		</header>

		<!-- Quick Stats -->
		<div class="stats-grid">
			<div class="stat-card">
				<div class="stat-icon upcoming">
					<i class="fas fa-calendar-alt"></i>
				</div>
				<div class="stat-content">
					<span class="stat-value">{totalUpcoming}</span>
					<span class="stat-label">Upcoming Pay Dates</span>
				</div>
			</div>
			{#if nextPayDate}
				<div class="stat-card">
					<div class="stat-icon next">
						<i class="fas fa-clock"></i>
					</div>
					<div class="stat-content">
						<span class="stat-value">{formatDate(nextPayDate.payDate)}</span>
						<span class="stat-label">Next Pay Date</span>
					</div>
				</div>
				<div class="stat-card">
					<div class="stat-icon employees">
						<i class="fas fa-users"></i>
					</div>
					<div class="stat-content">
						<span class="stat-value">{nextPayDate.totalEmployees}</span>
						<span class="stat-label">Employees (Next Run)</span>
					</div>
				</div>
				<div class="stat-card">
					<div class="stat-icon amount">
						<i class="fas fa-dollar-sign"></i>
					</div>
					<div class="stat-content">
						<span class="stat-value">{formatCurrency(nextPayDate.totalEstimatedGross)}</span>
						<span class="stat-label">Est. Gross (Next Run)</span>
					</div>
				</div>
			{/if}
		</div>

		<!-- Pay Date Cards -->
		<section class="pay-dates-section">
			<div class="section-header">
				<h2 class="section-title">Upcoming Pay Dates</h2>
				<a href="/payroll/history" class="view-history-link">
					<span>View History</span>
					<i class="fas fa-arrow-right"></i>
				</a>
			</div>

			{#if upcomingPayDates.length === 0}
				<div class="empty-state">
					<div class="empty-icon">
						<i class="fas fa-calendar-check"></i>
					</div>
					<h3>No Upcoming Pay Dates</h3>
					<p>All scheduled payroll runs have been completed.</p>
				</div>
			{:else}
				<div class="pay-dates-list">
					{#each upcomingPayDates as payDateData (payDateData.payDate)}
						<PayDateCard {payDateData} />
					{/each}
				</div>
			{/if}
		</section>

		<!-- Quick Actions -->
		<section class="quick-actions-section">
			<h2 class="section-title">Quick Actions</h2>
			<div class="actions-grid">
				<a href="/employees" class="action-card">
					<div class="action-icon">
						<i class="fas fa-user-plus"></i>
					</div>
					<div class="action-content">
						<h3>Manage Employees</h3>
						<p>Add or update employee information</p>
					</div>
					<i class="fas fa-chevron-right"></i>
				</a>
				<a href="/company?tab=pay-groups" class="action-card">
					<div class="action-icon">
						<i class="fas fa-layer-group"></i>
					</div>
					<div class="action-content">
						<h3>Pay Groups</h3>
						<p>Configure pay frequencies and policies</p>
					</div>
					<i class="fas fa-chevron-right"></i>
				</a>
				<a href="/reports" class="action-card">
					<div class="action-icon">
						<i class="fas fa-file-invoice-dollar"></i>
					</div>
					<div class="action-content">
						<h3>Remittance Reports</h3>
						<p>View CRA remittance summaries</p>
					</div>
					<i class="fas fa-chevron-right"></i>
				</a>
			</div>
		</section>
	</div>
{/if}

<style>
	.payroll-dashboard {
		max-width: 1200px;
	}

	/* Loading State */
	.loading-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 400px;
		text-align: center;
	}

	.loading-spinner {
		width: 48px;
		height: 48px;
		border: 4px solid var(--color-surface-200);
		border-top-color: var(--color-primary-500);
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin-bottom: var(--spacing-4);
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.loading-state p {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
	}

	/* Error State */
	.error-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 400px;
		text-align: center;
	}

	.error-icon {
		width: 80px;
		height: 80px;
		border-radius: 50%;
		background: var(--color-error-100);
		color: var(--color-error-600);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 32px;
		margin-bottom: var(--spacing-4);
	}

	.error-state h3 {
		font-size: var(--font-size-title-small);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-2);
	}

	.error-state p {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0 0 var(--spacing-6);
	}

	/* Empty State Large (for no pay groups/employees) */
	.empty-state-large {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: var(--spacing-16) var(--spacing-6);
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		text-align: center;
		max-width: 500px;
		margin: 0 auto;
	}

	.empty-state-large .empty-icon {
		width: 100px;
		height: 100px;
		border-radius: 50%;
		background: var(--color-primary-100);
		color: var(--color-primary-600);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 40px;
		margin-bottom: var(--spacing-6);
	}

	.empty-state-large h3 {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-3);
	}

	.empty-state-large p {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0 0 var(--spacing-8);
		line-height: 1.6;
	}

	/* Header */
	.page-header {
		margin-bottom: var(--spacing-6);
	}

	.page-title {
		font-size: var(--font-size-headline-minimum);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-1);
	}

	.page-subtitle {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0;
	}

	/* Stats Grid */
	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: var(--spacing-4);
		margin-bottom: var(--spacing-8);
	}

	.stat-card {
		display: flex;
		align-items: center;
		gap: var(--spacing-4);
		padding: var(--spacing-5);
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
	}

	.stat-icon {
		width: 48px;
		height: 48px;
		border-radius: var(--radius-lg);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 20px;
	}

	.stat-icon.upcoming {
		background: var(--color-primary-100);
		color: var(--color-primary-600);
	}

	.stat-icon.next {
		background: var(--color-warning-100);
		color: var(--color-warning-600);
	}

	.stat-icon.employees {
		background: var(--color-info-100);
		color: var(--color-info-600);
	}

	.stat-icon.amount {
		background: var(--color-success-100);
		color: var(--color-success-600);
	}

	.stat-content {
		display: flex;
		flex-direction: column;
	}

	.stat-value {
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.stat-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	/* Section */
	.pay-dates-section {
		margin-bottom: var(--spacing-8);
	}

	.section-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: var(--spacing-4);
	}

	.section-title {
		font-size: var(--font-size-title-small);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0;
	}

	.view-history-link {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-primary-600);
		text-decoration: none;
		transition: var(--transition-fast);
	}

	.view-history-link:hover {
		color: var(--color-primary-700);
	}

	.view-history-link i {
		font-size: 12px;
	}

	/* Pay Dates List */
	.pay-dates-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
	}

	/* Empty State */
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: var(--spacing-12) var(--spacing-6);
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		text-align: center;
	}

	.empty-icon {
		width: 80px;
		height: 80px;
		border-radius: 50%;
		background: var(--color-surface-100);
		color: var(--color-surface-400);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 32px;
		margin-bottom: var(--spacing-4);
	}

	.empty-state h3 {
		font-size: var(--font-size-title-small);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-2);
	}

	.empty-state p {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0 0 var(--spacing-6);
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
		text-decoration: none;
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-primary:hover {
		opacity: 0.9;
		transform: translateY(-1px);
	}

	/* Quick Actions */
	.quick-actions-section {
		margin-bottom: var(--spacing-8);
	}

	.actions-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: var(--spacing-4);
	}

	.action-card {
		display: flex;
		align-items: center;
		gap: var(--spacing-4);
		padding: var(--spacing-5);
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		text-decoration: none;
		transition: var(--transition-fast);
	}

	.action-card:hover {
		box-shadow: var(--shadow-md3-2);
		transform: translateY(-2px);
	}

	.action-icon {
		width: 44px;
		height: 44px;
		border-radius: var(--radius-lg);
		background: var(--color-surface-100);
		color: var(--color-surface-600);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 18px;
		flex-shrink: 0;
	}

	.action-card:hover .action-icon {
		background: var(--color-primary-100);
		color: var(--color-primary-600);
	}

	.action-content {
		flex: 1;
	}

	.action-content h3 {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-1);
	}

	.action-content p {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
		margin: 0;
	}

	.action-card > i {
		color: var(--color-surface-400);
		font-size: 14px;
	}

	.action-card:hover > i {
		color: var(--color-primary-600);
	}

	/* Responsive */
	@media (max-width: 768px) {
		.stats-grid {
			grid-template-columns: repeat(2, 1fr);
		}

		.actions-grid {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 480px) {
		.stats-grid {
			grid-template-columns: 1fr;
		}
	}
</style>

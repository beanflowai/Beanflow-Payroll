<script lang="ts">
	// Dashboard page - Dynamic data based on current company
	import { companyState } from '$lib/stores/company.svelte';
	import { listEmployees } from '$lib/services/employeeService';
	import { getRecentCompletedRuns, getUpcomingPeriods } from '$lib/services/payroll';
	import { formatShortDate } from '$lib/utils/dateUtils';

	// State
	let employeeCount = $state(0);
	let lastPayrollAmount = $state(0);
	let nextPayDate = $state<string | null>(null);
	let isLoading = $state(true);
	let error = $state<string | null>(null);

	// Load dashboard data
	async function loadDashboardData() {
		isLoading = true;
		error = null;
		try {
			const [employeesResult, recentRunsResult, upcomingResult] = await Promise.all([
				listEmployees(),
				getRecentCompletedRuns(1),
				getUpcomingPeriods()
			]);

			if (employeesResult.error) {
				error = employeesResult.error;
				return;
			}

			employeeCount = employeesResult.data?.length ?? 0;
			lastPayrollAmount = recentRunsResult.data?.[0]?.totalNetPay ?? 0;
			nextPayDate = upcomingResult.data?.[0]?.payDate ?? null;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load dashboard data';
		} finally {
			isLoading = false;
		}
	}

	// Load data when company changes
	$effect(() => {
		const company = companyState.currentCompany;
		if (company) {
			loadDashboardData();
		} else if (!companyState.isLoading) {
			// No company selected and not loading - stop spinner
			isLoading = false;
		}
	});

	// Format currency
	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		}).format(amount);
	}
</script>

<svelte:head>
	<title>Dashboard - BeanFlow Payroll</title>
</svelte:head>

{#if isLoading}
	<div class="dashboard">
		<header class="page-header">
			<h1 class="page-title">Dashboard</h1>
			<p class="page-subtitle">Loading...</p>
		</header>
		<div class="flex items-center justify-center py-16">
			<div class="w-10 h-10 border-[3px] border-surface-200 border-t-primary-500 rounded-full animate-spin"></div>
		</div>
	</div>
{:else if error}
	<div class="dashboard">
		<header class="page-header">
			<h1 class="page-title">Dashboard</h1>
			<p class="page-subtitle">Welcome to BeanFlow Payroll</p>
		</header>
		<div class="flex flex-col items-center justify-center py-16 text-center">
			<div class="w-16 h-16 rounded-full bg-error-100 text-error-600 flex items-center justify-center text-2xl mb-4">
				<i class="fas fa-exclamation-triangle"></i>
			</div>
			<p class="text-body-content text-surface-600 mb-4">{error}</p>
			<button class="py-2 px-4 bg-primary-600 text-white rounded-lg" onclick={() => loadDashboardData()}>
				Try Again
			</button>
		</div>
	</div>
{:else}
<div class="dashboard">
	<header class="page-header">
		<h1 class="page-title">Dashboard</h1>
		<p class="page-subtitle">Welcome to BeanFlow Payroll</p>
	</header>

	<!-- Stats Grid -->
	<div class="stats-grid">
		<div class="stat-card">
			<div class="stat-icon employees">
				<i class="fas fa-users"></i>
			</div>
			<div class="stat-content">
				<span class="stat-value">{employeeCount}</span>
				<span class="stat-label">Active Employees</span>
			</div>
		</div>

		<div class="stat-card">
			<div class="stat-icon payroll">
				<i class="fas fa-dollar-sign"></i>
			</div>
			<div class="stat-content">
				<span class="stat-value">{lastPayrollAmount > 0 ? formatCurrency(lastPayrollAmount) : '—'}</span>
				<span class="stat-label">Last Payroll</span>
			</div>
		</div>

		<div class="stat-card">
			<div class="stat-icon next-run">
				<i class="fas fa-calendar-alt"></i>
			</div>
			<div class="stat-content">
				<span class="stat-value">{nextPayDate ? formatShortDate(nextPayDate) : '—'}</span>
				<span class="stat-label">Next Pay Date</span>
			</div>
		</div>

		<!-- TODO: Fetch actual CRA remittance due amount from remittance service -->
		<div class="stat-card">
			<div class="stat-icon remittance">
				<i class="fas fa-file-invoice-dollar"></i>
			</div>
			<div class="stat-content">
				<span class="stat-value">—</span>
				<span class="stat-label">CRA Remittance Due</span>
			</div>
		</div>
	</div>

	<!-- Quick Actions -->
	<section class="section">
		<h2 class="section-title">Quick Actions</h2>
		<div class="actions-grid">
			<a href="/payroll" class="action-card primary">
				<i class="fas fa-play-circle"></i>
				<span>Run Payroll</span>
			</a>
			<a href="/employees" class="action-card">
				<i class="fas fa-user-plus"></i>
				<span>Add Employee</span>
			</a>
			<a href="/reports" class="action-card">
				<i class="fas fa-chart-bar"></i>
				<span>View Reports</span>
			</a>
			<a href="/company" class="action-card">
				<i class="fas fa-building"></i>
				<span>Company</span>
			</a>
		</div>
	</section>

	<!-- Recent Activity -->
	<section class="section">
		<h2 class="section-title">Recent Activity</h2>
		<div class="activity-card">
			<div class="activity-list">
				<div class="activity-item">
					<div class="activity-icon success">
						<i class="fas fa-check"></i>
					</div>
					<div class="activity-content">
						<span class="activity-title">Payroll completed</span>
						<span class="activity-meta">December 1, 2025 - 12 employees</span>
					</div>
					<span class="activity-amount">$45,230.00</span>
				</div>

				<div class="activity-item">
					<div class="activity-icon info">
						<i class="fas fa-user-plus"></i>
					</div>
					<div class="activity-content">
						<span class="activity-title">New employee added</span>
						<span class="activity-meta">November 28, 2025 - Sarah Johnson</span>
					</div>
				</div>

				<div class="activity-item">
					<div class="activity-icon warning">
						<i class="fas fa-file-upload"></i>
					</div>
					<div class="activity-content">
						<span class="activity-title">CRA remittance submitted</span>
						<span class="activity-meta">November 15, 2025</span>
					</div>
					<span class="activity-amount">$7,890.00</span>
				</div>

				<div class="activity-item">
					<div class="activity-icon success">
						<i class="fas fa-check"></i>
					</div>
					<div class="activity-content">
						<span class="activity-title">Payroll completed</span>
						<span class="activity-meta">November 15, 2025 - 11 employees</span>
					</div>
					<span class="activity-amount">$42,150.00</span>
				</div>
			</div>
		</div>
	</section>
</div>
{/if}

<style>
	.dashboard {
		max-width: 1200px;
	}

	.page-header {
		margin-bottom: var(--spacing-8);
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
		grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
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

	.stat-icon.employees {
		background: var(--color-primary-100);
		color: var(--color-primary-600);
	}

	.stat-icon.payroll {
		background: var(--color-success-100);
		color: var(--color-success-600);
	}

	.stat-icon.next-run {
		background: var(--color-warning-100);
		color: var(--color-warning-600);
	}

	.stat-icon.remittance {
		background: var(--color-secondary-100);
		color: var(--color-secondary-600);
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
	.section {
		margin-bottom: var(--spacing-8);
	}

	.section-title {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-4);
	}

	/* Actions Grid */
	.actions-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
		gap: var(--spacing-4);
	}

	.action-card {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-6);
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		text-decoration: none;
		color: var(--color-surface-700);
		transition: var(--transition-fast);
	}

	.action-card:hover {
		transform: translateY(-2px);
		box-shadow: var(--shadow-md3-2);
		color: var(--color-primary-600);
	}

	.action-card.primary {
		background: var(--gradient-primary);
		color: white;
	}

	.action-card.primary:hover {
		color: white;
		opacity: 0.9;
	}

	.action-card i {
		font-size: 28px;
	}

	.action-card span {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
	}

	/* Activity Card */
	.activity-card {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		overflow: hidden;
	}

	.activity-list {
		display: flex;
		flex-direction: column;
	}

	.activity-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-4);
		padding: var(--spacing-4) var(--spacing-5);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.activity-item:last-child {
		border-bottom: none;
	}

	.activity-icon {
		width: 36px;
		height: 36px;
		border-radius: var(--radius-full);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 14px;
	}

	.activity-icon.success {
		background: var(--color-success-100);
		color: var(--color-success-600);
	}

	.activity-icon.info {
		background: var(--color-primary-100);
		color: var(--color-primary-600);
	}

	.activity-icon.warning {
		background: var(--color-warning-100);
		color: var(--color-warning-600);
	}

	.activity-content {
		flex: 1;
		display: flex;
		flex-direction: column;
		min-width: 0;
	}

	.activity-title {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.activity-meta {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.activity-amount {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	@media (max-width: 640px) {
		.activity-amount {
			display: none;
		}
	}
</style>

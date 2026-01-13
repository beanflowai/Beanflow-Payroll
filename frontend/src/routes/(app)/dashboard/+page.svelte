<script lang="ts">
	// Dashboard page - Dynamic data based on current company
	import { companyState } from '$lib/stores/company.svelte';
	import { listEmployees } from '$lib/services/employeeService';
	import { getRecentCompletedRuns, getUpcomingPeriods } from '$lib/services/payroll';
	import { listRemittancePeriods } from '$lib/services/remittanceService';
	import { formatShortDate } from '$lib/utils/dateUtils';
	import { formatCurrency } from '$lib/utils/formatUtils';
	import { Skeleton, AlertBanner, EmptyState } from '$lib/components/shared';
	import type { PayrollRunWithGroups } from '$lib/types/payroll';
	import type { RemittancePeriod } from '$lib/types/remittance';
	import { onboardingState, loadOnboardingProgress, dismissOnboarding } from '$lib/stores/onboarding.svelte';
	import { OnboardingBanner, OnboardingProgressCard, GettingStartedSection } from '$lib/components/onboarding';
	import { ONBOARDING_STEPS } from '$lib/config/onboardingSteps';
	import { goto } from '$app/navigation';

	// State
	let employeeCount = $state(0);
	let lastPayrollAmount = $state(0);
	let nextPayDate = $state<string | null>(null);
	let recentPayrollRuns = $state<PayrollRunWithGroups[]>([]);
	let nextRemittance = $state<RemittancePeriod | null>(null);
	let isLoading = $state(true);
	let error = $state<string | null>(null);
	const showOnboarding = $derived(
		!!onboardingState.progress && !onboardingState.isCompleted && !onboardingState.isDismissed
	);

	// Load dashboard data
	async function loadDashboardData() {
		isLoading = true;
		error = null;
		try {
			const company = companyState.currentCompany;
			if (!company) return;

			const currentYear = new Date().getFullYear();

			const [employeesResult, recentRunsResult, upcomingResult, remittancesResult] =
				await Promise.all([
					listEmployees(),
					getRecentCompletedRuns(5),
					getUpcomingPeriods(),
					listRemittancePeriods(company.id, { year: currentYear, limit: 100 })
				]);

			if (employeesResult.error) {
				error = employeesResult.error;
				return;
			}

			employeeCount = employeesResult.data?.length ?? 0;
			lastPayrollAmount = recentRunsResult.data?.[0]?.totalNetPay ?? 0;
			nextPayDate = upcomingResult.data?.[0]?.payDate ?? null;
			recentPayrollRuns = recentRunsResult.data ?? [];

			// Find the first pending/due_soon/overdue remittance
			const pendingRemittances = remittancesResult.data.filter(
				(r) => r.status === 'pending' || r.status === 'due_soon' || r.status === 'overdue'
			);
			// Sort by due_date ascending to get the earliest upcoming remittance
			pendingRemittances.sort((a, b) => new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime());
			nextRemittance = pendingRemittances.length > 0 ? pendingRemittances[0] : null;
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
		// Load onboarding progress (works with or without company)
		loadOnboardingProgress();
	});

	// Helper to format activity date
	function formatActivityDate(dateStr: string): string {
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-CA', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}
</script>

<svelte:head>
	<title>Dashboard - BeanFlow Payroll</title>
</svelte:head>

{#if isLoading}
	<div class="dashboard">
		<header class="page-header">
			<h1 class="page-title">Dashboard</h1>
			<p class="page-subtitle">Welcome to BeanFlow Payroll</p>
		</header>
		<!-- Skeleton Stats Grid - conditional based on onboarding -->
		<div class="stats-grid">
			{#if !showOnboarding}
				<!-- Post-onboarding: show 4 regular stat skeletons -->
				{#each Array(4) as _unused, idx (idx)}
					<div class="stat-card">
						<Skeleton variant="circular" width="48px" height="48px" />
						<div class="stat-content" style="flex:1">
							<Skeleton variant="text" width="60%" height="28px" />
							<Skeleton variant="text" width="80%" height="14px" />
						</div>
					</div>
				{/each}
			{:else}
				<!-- During onboarding: show only onboarding card skeleton -->
				<div class="stat-card">
					<Skeleton variant="circular" width="48px" height="48px" />
					<div class="stat-content" style="flex:1">
						<Skeleton variant="text" width="40%" height="28px" />
						<Skeleton variant="text" width="70%" height="14px" />
					</div>
				</div>
			{/if}
		</div>
	</div>
{:else if error}
	<div class="dashboard">
		<header class="page-header">
			<h1 class="page-title">Dashboard</h1>
			<p class="page-subtitle">Welcome to BeanFlow Payroll</p>
		</header>
		<AlertBanner type="error" title="Failed to load dashboard" message={error}>
			<button
				class="py-2 px-4 bg-error-600 text-white rounded-lg text-sm mt-2"
				onclick={() => loadDashboardData()}
			>
				Try Again
			</button>
		</AlertBanner>
	</div>
{:else}
	<div class="dashboard">
		<header class="page-header">
			<h1 class="page-title">Dashboard</h1>
			<p class="page-subtitle">Welcome to BeanFlow Payroll</p>
		</header>

		{#if showOnboarding}
			<OnboardingBanner
				progress={onboardingState.progress}
				onDismiss={() => dismissOnboarding()}
				onContinue={() => {
					const nextStep = ONBOARDING_STEPS.find(
						(s) => !onboardingState.progress?.completedSteps.includes(s.id)
					);
					if (nextStep) goto(nextStep.route);
				}}
			/>
		{/if}

		<!-- Stats Grid -->
		<div class="stats-grid">
			{#if showOnboarding}
				<!-- During onboarding: show only onboarding progress card -->
				<OnboardingProgressCard
					progress={onboardingState.progress}
					onStepClick={(stepId) => {
						const step = ONBOARDING_STEPS.find((s) => s.id === stepId);
						if (step) goto(step.route);
					}}
				/>
			{:else}
				<!-- After onboarding: show regular stat cards -->
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
						<span class="stat-value"
							>{lastPayrollAmount > 0
								? formatCurrency(lastPayrollAmount, { maximumFractionDigits: 0 })
								: '—'}</span
						>
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

				<!-- CRA Remittance Due -->
				<div class="stat-card">
					<div class="stat-icon remittance">
						<i class="fas fa-file-invoice-dollar"></i>
					</div>
					<div class="stat-content">
						{#if nextRemittance}
							<a
								href="/remittance"
								class="stat-value-link"
								title="View remittance details"
								style="text-decoration: none;"
							>
								<span class="stat-value">{formatCurrency(nextRemittance.totalAmount)}</span>
							</a>
							<span class="stat-label">Due {formatShortDate(nextRemittance.dueDate)}</span>
						{:else}
							<span class="stat-value">—</span>
							<span class="stat-label">No pending remittances</span>
						{/if}
					</div>
				</div>
			{/if}
		</div>

		<!-- Quick Actions / Getting Started -->
		{#if showOnboarding}
			<!-- During onboarding: show video guides -->
			<GettingStartedSection progress={onboardingState.progress} />
		{:else}
			<!-- After onboarding: show quick actions -->
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
		{/if}

		<!-- Recent Activity -->
		<section class="section">
			<h2 class="section-title">Recent Activity</h2>
			<div class="activity-card">
				{#if recentPayrollRuns.length === 0}
					<EmptyState
						icon="fa-history"
						title="No Recent Activity"
						description="Your recent payroll runs and activities will appear here."
						variant="card"
					/>
				{:else}
					<div class="activity-list">
						{#each recentPayrollRuns as run (run.id)}
							<div class="activity-item">
								<div class="activity-icon success">
									<i class="fas fa-check"></i>
								</div>
								<div class="activity-content">
									<span class="activity-title">Payroll completed</span>
									<span class="activity-meta"
										>{formatActivityDate(run.periodEnd)} - {run.totalEmployees} employees</span
									>
								</div>
								<span class="activity-amount">{formatCurrency(run.totalNetPay)}</span>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</section>
	</div>
{/if}

<style>
	.dashboard {
		max-width: 1200px;
		margin: 0 auto;
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

	.stat-value-link {
		transition: var(--transition-fast);
	}

	.stat-value-link:hover {
		opacity: 0.8;
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

<script lang="ts">
	import type { UpcomingPeriod, PayrollPageStatus, PayGroupSummary, PayrollRunWithGroups } from '$lib/types/payroll';
	import { PAYROLL_STATUS_LABELS } from '$lib/types/payroll';
	import { PayPeriodCard, PayGroupEmployeesPanel } from '$lib/components/payroll';
	import {
		checkPayrollPageStatus,
		getUpcomingPeriods,
		getRecentCompletedRuns
	} from '$lib/services/payroll';
	import { formatShortDate } from '$lib/utils/dateUtils';
	import { companyState } from '$lib/stores/company.svelte';

	// ===========================================
	// State
	// ===========================================
	let pageStatus = $state<PayrollPageStatus | null>(null);
	let upcomingPeriods = $state<UpcomingPeriod[]>([]);
	let recentRuns = $state<PayrollRunWithGroups[]>([]);
	let isLoading = $state(true);
	let error = $state<string | null>(null);

	// Employee panel state
	let selectedPayGroup = $state<PayGroupSummary | null>(null);
	let showEmployeesPanel = $state(false);

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

			// If ready or no_employees, load upcoming periods and recent runs
			if (pageStatus?.status === 'ready' || pageStatus?.status === 'no_employees') {
				const [periodsResult, recentRunsResult] = await Promise.all([
					getUpcomingPeriods(),
					getRecentCompletedRuns(5)
				]);

				if (periodsResult.error) {
					error = periodsResult.error;
					return;
				}
				upcomingPeriods = periodsResult.data ?? [];
				recentRuns = recentRunsResult.data ?? [];
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load payroll data';
		} finally {
			isLoading = false;
		}
	}

	// Load data when company changes
	$effect(() => {
		// Depend on currentCompany to reload when company switches
		const company = companyState.currentCompany;
		if (company) {
			loadData();
		} else if (!companyState.isLoading) {
			// No company selected and not loading - stop spinner
			isLoading = false;
		}
	});

	// ===========================================
	// Computed
	// ===========================================
	const totalUpcoming = $derived(upcomingPeriods.length);
	const nextPeriod = $derived(upcomingPeriods.length > 0 ? upcomingPeriods[0] : null);

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

	function getStatusBadgeClass(status: string): string {
		switch (status) {
			case 'paid':
				return 'bg-success-100 text-success-700';
			case 'approved':
				return 'bg-info-100 text-info-700';
			case 'pending_approval':
				return 'bg-warning-100 text-warning-700';
			default:
				return 'bg-surface-100 text-surface-600';
		}
	}

	// ===========================================
	// Pay Group Click Handler
	// ===========================================
	function handlePayGroupClick(payGroup: PayGroupSummary) {
		selectedPayGroup = payGroup;
		showEmployeesPanel = true;
	}

	function handleCloseEmployeesPanel() {
		showEmployeesPanel = false;
		selectedPayGroup = null;
	}

	function handleEmployeesChanged() {
		// Reload data to update employee counts
		loadData();
	}
</script>

<svelte:head>
	<title>Run Payroll - BeanFlow Payroll</title>
</svelte:head>

{#if isLoading}
	<!-- Loading State -->
	<div class="flex flex-col items-center justify-center min-h-[400px] text-center">
		<div class="w-12 h-12 border-4 border-surface-200 border-t-primary-500 rounded-full animate-spin mb-4"></div>
		<p class="text-body-content text-surface-600">Loading payroll data...</p>
	</div>
{:else if !companyState.currentCompany}
	<!-- No Company Selected State -->
	<div class="flex flex-col items-center justify-center min-h-[400px] text-center">
		<div class="w-20 h-20 rounded-full bg-surface-100 text-surface-400 flex items-center justify-center text-[32px] mb-4">
			<i class="fas fa-building"></i>
		</div>
		<h3 class="text-title-small font-semibold text-surface-800 m-0 mb-2">No Company Selected</h3>
		<p class="text-body-content text-surface-600 m-0 mb-6">Please select or create a company to run payroll.</p>
	</div>
{:else if error}
	<!-- Error State -->
	<div class="flex flex-col items-center justify-center min-h-[400px] text-center">
		<div class="w-20 h-20 rounded-full bg-error-100 text-error-600 flex items-center justify-center text-[32px] mb-4">
			<i class="fas fa-exclamation-triangle"></i>
		</div>
		<h3 class="text-title-small font-semibold text-surface-800 m-0 mb-2">Error Loading Payroll</h3>
		<p class="text-body-content text-surface-600 m-0 mb-6">{error}</p>
		<button class="inline-flex items-center gap-2 py-3 px-5 bg-gradient-to-br from-primary-600 to-secondary-600 text-white border-none rounded-lg text-body-content font-medium cursor-pointer transition-fast hover:opacity-90 hover:-translate-y-px" onclick={() => loadData()}>
			<i class="fas fa-redo"></i>
			<span>Try Again</span>
		</button>
	</div>
{:else if pageStatus?.status === 'no_pay_groups'}
	<!-- No Pay Groups State -->
	<div class="max-w-[1200px] mx-auto">
		<header class="mb-6">
			<div>
				<h1 class="text-headline-minimum font-semibold text-surface-800 m-0 mb-1">Run Payroll</h1>
				<p class="text-body-content text-surface-600 m-0">Get started by creating your first pay group</p>
			</div>
		</header>

		<div class="flex flex-col items-center py-16 px-6 bg-white rounded-xl shadow-md3-1 text-center max-w-[500px] mx-auto">
			<div class="w-[100px] h-[100px] rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-[40px] mb-6">
				<i class="fas fa-layer-group"></i>
			</div>
			<h3 class="text-title-medium font-semibold text-surface-800 m-0 mb-3">No Pay Groups Yet</h3>
			<p class="text-body-content text-surface-600 m-0 mb-8 leading-relaxed">Create a pay group to organize employees by pay frequency and configure payroll settings.</p>
			<a href="/company?tab=pay-groups" class="inline-flex items-center gap-2 py-3 px-5 bg-gradient-to-br from-primary-600 to-secondary-600 text-white border-none rounded-lg text-body-content font-medium no-underline cursor-pointer transition-fast hover:opacity-90 hover:-translate-y-px">
				<i class="fas fa-plus"></i>
				<span>Create Pay Group</span>
			</a>
		</div>
	</div>
{:else if pageStatus?.status === 'no_employees' || pageStatus?.status === 'ready'}
	<!-- Ready State - Normal Dashboard -->
	<div class="max-w-[1200px] mx-auto">
		<!-- Header -->
		<header class="mb-6">
			<div>
				<h1 class="text-headline-minimum font-semibold text-surface-800 m-0 mb-1">Run Payroll</h1>
				<p class="text-body-content text-surface-600 m-0">Manage upcoming payroll runs for all pay groups</p>
			</div>
		</header>

		<!-- Quick Stats -->
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-[repeat(auto-fit,minmax(220px,1fr))] gap-4 mb-8">
			<div class="flex items-center gap-4 p-5 bg-white rounded-xl shadow-md3-1">
				<div class="w-12 h-12 rounded-lg flex items-center justify-center text-[20px] bg-primary-100 text-primary-600">
					<i class="fas fa-calendar-alt"></i>
				</div>
				<div class="flex flex-col">
					<span class="text-title-large font-semibold text-surface-800">{totalUpcoming}</span>
					<span class="text-auxiliary-text text-surface-600">Upcoming Periods</span>
				</div>
			</div>
			{#if nextPeriod}
				<div class="flex items-center gap-4 p-5 bg-white rounded-xl shadow-md3-1">
					<div class="w-12 h-12 rounded-lg flex items-center justify-center text-[20px] bg-warning-100 text-warning-600">
						<i class="fas fa-clock"></i>
					</div>
					<div class="flex flex-col">
						<span class="text-title-large font-semibold text-surface-800">{formatShortDate(nextPeriod.periodEnd)}</span>
						<span class="text-auxiliary-text text-surface-600">Next Period End</span>
					</div>
				</div>
				<div class="flex items-center gap-4 p-5 bg-white rounded-xl shadow-md3-1">
					<div class="w-12 h-12 rounded-lg flex items-center justify-center text-[20px] bg-tertiary-100 text-tertiary-600">
						<i class="fas fa-users"></i>
					</div>
					<div class="flex flex-col">
						<span class="text-title-large font-semibold text-surface-800">{nextPeriod.totalEmployees}</span>
						<span class="text-auxiliary-text text-surface-600">Employees (Next Run)</span>
					</div>
				</div>
				<div class="flex items-center gap-4 p-5 bg-white rounded-xl shadow-md3-1">
					<div class="w-12 h-12 rounded-lg flex items-center justify-center text-[20px] bg-success-100 text-success-600">
						<i class="fas fa-dollar-sign"></i>
					</div>
					<div class="flex flex-col">
						<span class="text-title-large font-semibold text-surface-800">{formatCurrency(nextPeriod.totalEstimatedGross)}</span>
						<span class="text-auxiliary-text text-surface-600">Est. Gross (Next Run)</span>
					</div>
				</div>
			{/if}
		</div>

		<!-- Pay Period Cards -->
		<section class="mb-8">
			<div class="flex items-center justify-between mb-4">
				<h2 class="text-title-small font-semibold text-surface-800 m-0">Upcoming Pay Periods</h2>
				<a href="/payroll/history" class="flex items-center gap-2 text-body-content font-medium text-primary-600 no-underline transition-fast hover:text-primary-700">
					<span>View History</span>
					<i class="fas fa-arrow-right text-xs"></i>
				</a>
			</div>

			{#if upcomingPeriods.length === 0}
				<div class="flex flex-col items-center py-12 px-6 bg-white rounded-xl shadow-md3-1 text-center">
					<div class="w-20 h-20 rounded-full bg-surface-100 text-surface-400 flex items-center justify-center text-[32px] mb-4">
						<i class="fas fa-calendar-check"></i>
					</div>
					<h3 class="text-title-small font-semibold text-surface-800 m-0 mb-2">No Upcoming Pay Periods</h3>
					<p class="text-body-content text-surface-600 m-0 mb-6">All scheduled payroll runs have been completed.</p>
				</div>
			{:else}
				<div class="flex flex-col gap-4">
					{#each upcomingPeriods as periodData (periodData.periodEnd)}
						<PayPeriodCard {periodData} onPayGroupClick={handlePayGroupClick} />
					{/each}
				</div>
			{/if}
		</section>

		<!-- Recent Completed Runs -->
		{#if recentRuns.length > 0}
			<section class="mb-8">
				<div class="flex items-center justify-between mb-4">
					<h2 class="text-title-small font-semibold text-surface-800 m-0">Recent Completed</h2>
					<a href="/payroll/history" class="flex items-center gap-2 text-body-content font-medium text-primary-600 no-underline transition-fast hover:text-primary-700">
						<span>View All</span>
						<i class="fas fa-arrow-right text-xs"></i>
					</a>
				</div>

				<div class="bg-white rounded-xl shadow-md3-1 overflow-hidden">
					<table class="w-full border-collapse">
						<thead>
							<tr>
								<th class="text-left p-4 px-5 bg-surface-50 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide border-b border-surface-200">Pay Date</th>
								<th class="text-left p-4 px-5 bg-surface-50 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide border-b border-surface-200">Employees</th>
								<th class="text-left p-4 px-5 bg-surface-50 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide border-b border-surface-200">Net Pay</th>
								<th class="text-left p-4 px-5 bg-surface-50 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide border-b border-surface-200">Status</th>
							</tr>
						</thead>
						<tbody>
							{#each recentRuns as run (run.id)}
								<tr
									class="cursor-pointer transition-[150ms] hover:[&>td]:bg-surface-50"
									onclick={() => window.location.href = '/payroll/history'}
									role="button"
									tabindex="0"
									onkeydown={(e) => e.key === 'Enter' && (window.location.href = '/payroll/history')}
								>
									<td class="p-4 px-5 text-body-content border-b border-surface-100 font-medium text-surface-800 last:border-b-0">{formatShortDate(run.payDate)}</td>
									<td class="p-4 px-5 text-body-content border-b border-surface-100 text-surface-700 last:border-b-0">{run.totalEmployees}</td>
									<td class="p-4 px-5 text-body-content border-b border-surface-100 font-mono font-semibold text-surface-800 last:border-b-0">{formatCurrency(run.totalNetPay)}</td>
									<td class="p-4 px-5 text-body-content border-b border-surface-100 text-surface-700 last:border-b-0">
										<span class="inline-flex items-center gap-2 py-1 px-3 rounded-full text-auxiliary-text font-medium {getStatusBadgeClass(run.status)}">
											{PAYROLL_STATUS_LABELS[run.status]}
										</span>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</section>
		{/if}

		<!-- Quick Actions -->
		<section class="mb-8">
			<h2 class="text-title-small font-semibold text-surface-800 m-0 mb-4">Quick Actions</h2>
			<div class="grid grid-cols-1 md:grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-4">
				<a href="/employees" class="flex items-center gap-4 p-5 bg-white rounded-xl shadow-md3-1 no-underline transition-fast hover:shadow-md3-2 hover:-translate-y-0.5 group">
					<div class="w-11 h-11 rounded-lg bg-surface-100 text-surface-600 flex items-center justify-center text-[18px] shrink-0 group-hover:bg-primary-100 group-hover:text-primary-600">
						<i class="fas fa-user-plus"></i>
					</div>
					<div class="flex-1">
						<h3 class="text-body-content font-semibold text-surface-800 m-0 mb-1">Manage Employees</h3>
						<p class="text-auxiliary-text text-surface-600 m-0">Add or update employee information</p>
					</div>
					<i class="fas fa-chevron-right text-surface-400 text-sm group-hover:text-primary-600"></i>
				</a>
				<a href="/company?tab=pay-groups" class="flex items-center gap-4 p-5 bg-white rounded-xl shadow-md3-1 no-underline transition-fast hover:shadow-md3-2 hover:-translate-y-0.5 group">
					<div class="w-11 h-11 rounded-lg bg-surface-100 text-surface-600 flex items-center justify-center text-[18px] shrink-0 group-hover:bg-primary-100 group-hover:text-primary-600">
						<i class="fas fa-layer-group"></i>
					</div>
					<div class="flex-1">
						<h3 class="text-body-content font-semibold text-surface-800 m-0 mb-1">Pay Groups</h3>
						<p class="text-auxiliary-text text-surface-600 m-0">Configure pay frequencies and policies</p>
					</div>
					<i class="fas fa-chevron-right text-surface-400 text-sm group-hover:text-primary-600"></i>
				</a>
				<a href="/reports" class="flex items-center gap-4 p-5 bg-white rounded-xl shadow-md3-1 no-underline transition-fast hover:shadow-md3-2 hover:-translate-y-0.5 group">
					<div class="w-11 h-11 rounded-lg bg-surface-100 text-surface-600 flex items-center justify-center text-[18px] shrink-0 group-hover:bg-primary-100 group-hover:text-primary-600">
						<i class="fas fa-file-invoice-dollar"></i>
					</div>
					<div class="flex-1">
						<h3 class="text-body-content font-semibold text-surface-800 m-0 mb-1">Remittance Reports</h3>
						<p class="text-auxiliary-text text-surface-600 m-0">View CRA remittance summaries</p>
					</div>
					<i class="fas fa-chevron-right text-surface-400 text-sm group-hover:text-primary-600"></i>
				</a>
			</div>
		</section>
	</div>
{/if}

<!-- Pay Group Employees Panel -->
{#if selectedPayGroup}
	<PayGroupEmployeesPanel
		payGroup={selectedPayGroup}
		isOpen={showEmployeesPanel}
		onClose={handleCloseEmployeesPanel}
		onEmployeesChanged={handleEmployeesChanged}
	/>
{/if}

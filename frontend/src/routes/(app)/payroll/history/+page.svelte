<script lang="ts">
	import { goto } from '$app/navigation';
	import type { PayrollRunWithGroups, PayrollRunStatus } from '$lib/types/payroll';
	import { PAYROLL_STATUS_LABELS } from '$lib/types/payroll';
	import { listPayrollRuns, type PayrollRunListOptionsExt } from '$lib/services/payroll';
	import { formatShortDate } from '$lib/utils/dateUtils';

	// Filter tabs configuration
	type FilterTab = 'all' | 'draft' | 'pending' | 'completed' | 'cancelled';
	const filterTabs: { key: FilterTab; label: string }[] = [
		{ key: 'all', label: 'All' },
		{ key: 'draft', label: 'Draft' },
		{ key: 'pending', label: 'Pending Approval' },
		{ key: 'completed', label: 'Completed' },
		{ key: 'cancelled', label: 'Cancelled' }
	];

	// State
	let runs = $state<PayrollRunWithGroups[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let activeTab = $state<FilterTab>('all');
	let currentPage = $state(1);
	let totalCount = $state(0);

	// Constants
	const PAGE_SIZE = 20;

	// Get filter options based on active tab
	function getFilterOptions(): PayrollRunListOptionsExt {
		const offset = (currentPage - 1) * PAGE_SIZE;

		switch (activeTab) {
			case 'draft':
				return {
					status: 'draft',
					limit: PAGE_SIZE,
					offset
				};
			case 'pending':
				return {
					status: 'pending_approval',
					limit: PAGE_SIZE,
					offset
				};
			case 'completed':
				return {
					excludeStatuses: ['draft', 'pending_approval', 'cancelled'],
					limit: PAGE_SIZE,
					offset
				};
			case 'cancelled':
				return {
					status: 'cancelled',
					limit: PAGE_SIZE,
					offset
				};
			default:
				// All - include everything
				return {
					limit: PAGE_SIZE,
					offset
				};
		}
	}

	// Load payroll runs
	async function loadRuns() {
		loading = true;
		error = null;

		const options = getFilterOptions();
		const result = await listPayrollRuns(options);

		if (result.error) {
			error = result.error;
			runs = [];
			totalCount = 0;
		} else {
			runs = result.data;
			totalCount = result.count;
		}

		loading = false;
	}

	// Initial load
	$effect(() => {
		loadRuns();
	});

	// Reload when tab or page changes
	function changeTab(tab: FilterTab) {
		if (activeTab !== tab) {
			activeTab = tab;
			currentPage = 1;
			loadRuns();
		}
	}

	function changePage(page: number) {
		if (page !== currentPage && page >= 1 && page <= totalPages) {
			currentPage = page;
			loadRuns();
		}
	}

	// Select a run to navigate to payroll run page
	function selectRun(run: PayrollRunWithGroups) {
		goto(`/payroll/run/${run.periodEnd}`);
	}

	// Computed
	const totalPages = $derived(Math.ceil(totalCount / PAGE_SIZE));
	const ytdTotalPaid = $derived(runs.reduce((sum, run) => sum + run.totalNetPay, 0));
	const showingStart = $derived((currentPage - 1) * PAGE_SIZE + 1);
	const showingEnd = $derived(Math.min(currentPage * PAGE_SIZE, totalCount));

	// Helpers
	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD'
		}).format(amount);
	}

	function formatPeriod(start: string, end: string): string {
		const startDate = new Date(start);
		const endDate = new Date(end);
		const startStr = startDate.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' });
		const endStr = endDate.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' });
		return `${startStr} - ${endStr}`;
	}

	function getStatusBadgeClass(status: PayrollRunStatus): string {
		switch (status) {
			case 'paid':
				return 'bg-success-100 text-success-700';
			case 'approved':
				return 'bg-info-100 text-info-700';
			case 'pending_approval':
				return 'bg-warning-100 text-warning-700';
			case 'draft':
				return 'bg-surface-100 text-surface-600';
			case 'cancelled':
				return 'bg-error-100 text-error-700';
			default:
				return '';
		}
	}
</script>

<svelte:head>
	<title>Payroll History - BeanFlow Payroll</title>
</svelte:head>

<div class="max-w-[1400px]">
	<!-- Main Content -->
	<div class="flex-1 min-w-0">
		<header class="flex items-start justify-between mb-6 max-md:flex-col max-md:gap-4">
			<div class="flex-1">
				<h1 class="text-headline-minimum font-semibold text-surface-800 m-0 mb-1">Payroll History</h1>
				<p class="text-body-content text-surface-600 m-0">View past payroll runs and details</p>
			</div>
			<div>
				<button class="flex items-center gap-2 py-3 px-5 bg-white text-surface-700 border border-surface-200 rounded-lg text-body-content font-medium cursor-pointer transition-[150ms] hover:bg-surface-50 hover:border-surface-300">
					<i class="fas fa-download"></i>
					<span>Export</span>
				</button>
			</div>
		</header>

		<!-- Filter Tabs -->
		<div class="flex gap-1 mb-6 border-b border-surface-200">
			{#each filterTabs as tab}
				<button
					class="py-3 px-4 text-body-content font-medium border-b-2 -mb-px transition-colors cursor-pointer bg-transparent border-l-0 border-r-0 border-t-0 {activeTab === tab.key
						? 'text-primary-600 border-primary-600'
						: 'text-surface-600 border-transparent hover:text-surface-800'}"
					onclick={() => changeTab(tab.key)}
				>
					{tab.label}
				</button>
			{/each}
		</div>

		<!-- Loading State -->
		{#if loading}
			<div class="flex items-center justify-center py-16">
				<div class="flex flex-col items-center gap-4">
					<i class="fas fa-spinner fa-spin text-3xl text-primary-500"></i>
					<span class="text-body-content text-surface-600">Loading payroll history...</span>
				</div>
			</div>
		{:else if error}
			<!-- Error State -->
			<div class="bg-error-50 border border-error-200 rounded-xl p-6 text-center">
				<i class="fas fa-exclamation-circle text-3xl text-error-500 mb-3"></i>
				<p class="text-body-content text-error-700 m-0 mb-4">{error}</p>
				<button
					class="py-2 px-4 bg-error-600 text-white rounded-lg text-body-content font-medium cursor-pointer hover:bg-error-700"
					onclick={() => loadRuns()}
				>
					Try Again
				</button>
			</div>
		{:else if runs.length === 0}
			<!-- Empty State -->
			<div class="bg-white rounded-xl shadow-md3-1 p-12 text-center">
				<i class="fas fa-history text-5xl text-surface-300 mb-4"></i>
				<h3 class="text-title-medium font-semibold text-surface-800 m-0 mb-2">No Payroll Runs Found</h3>
				<p class="text-body-content text-surface-600 m-0">
					{#if activeTab === 'all'}
						You haven't created any payroll runs yet.
					{:else if activeTab === 'draft'}
						No draft payroll runs.
					{:else if activeTab === 'pending'}
						No payroll runs are pending approval.
					{:else if activeTab === 'completed'}
						No completed payroll runs.
					{:else}
						No cancelled payroll runs.
					{/if}
				</p>
			</div>
		{:else}
			<!-- Summary Stats -->
			<div class="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-4 mb-6">
				<div class="flex items-center gap-4 p-5 bg-white rounded-xl shadow-md3-1">
					<div class="w-12 h-12 rounded-lg bg-primary-100 text-primary-600 flex items-center justify-center text-xl">
						<i class="fas fa-calendar-check"></i>
					</div>
					<div class="flex flex-col">
						<span class="text-title-large font-semibold text-surface-800">{totalCount}</span>
						<span class="text-auxiliary-text text-surface-600">Payroll Runs</span>
					</div>
				</div>
				<div class="flex items-center gap-4 p-5 bg-white rounded-xl shadow-md3-1">
					<div class="w-12 h-12 rounded-lg bg-primary-100 text-primary-600 flex items-center justify-center text-xl">
						<i class="fas fa-dollar-sign"></i>
					</div>
					<div class="flex flex-col">
						<span class="text-title-large font-semibold text-surface-800">{formatCurrency(ytdTotalPaid)}</span>
						<span class="text-auxiliary-text text-surface-600">Total Net Pay (This Page)</span>
					</div>
				</div>
			</div>

			<!-- History Table -->
			<div class="bg-white rounded-xl shadow-md3-1 overflow-hidden mb-4 max-md:overflow-x-auto">
				<table class="w-full border-collapse max-md:min-w-[700px]">
					<thead>
						<tr>
							<th class="text-left p-4 px-5 bg-surface-50 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide border-b border-surface-200">Period End</th>
							<th class="text-left p-4 px-5 bg-surface-50 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide border-b border-surface-200">Employees</th>
							<th class="text-left p-4 px-5 bg-surface-50 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide border-b border-surface-200">Gross Pay</th>
							<th class="text-left p-4 px-5 bg-surface-50 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide border-b border-surface-200">Net Pay</th>
							<th class="text-left p-4 px-5 bg-surface-50 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide border-b border-surface-200">Status</th>
							<th class="text-left p-4 px-5 bg-surface-50 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide border-b border-surface-200"></th>
						</tr>
					</thead>
					<tbody>
						{#each runs as run (run.id)}
							<tr
								class="cursor-pointer transition-[150ms] hover:[&>td]:bg-surface-50"
								onclick={() => selectRun(run)}
								role="button"
								tabindex="0"
								onkeydown={(e) => e.key === 'Enter' && selectRun(run)}
							>
								<td class="p-4 px-5 text-body-content border-b border-surface-100 font-medium text-surface-800 last:border-b-0">{formatShortDate(run.periodEnd)}</td>
								<td class="p-4 px-5 text-body-content border-b border-surface-100 text-surface-700 last:border-b-0">{run.totalEmployees}</td>
								<td class="p-4 px-5 text-body-content border-b border-surface-100 text-surface-700 font-mono last:border-b-0">{formatCurrency(run.totalGross)}</td>
								<td class="p-4 px-5 text-body-content border-b border-surface-100 font-mono font-semibold text-surface-800 last:border-b-0">{formatCurrency(run.totalNetPay)}</td>
								<td class="p-4 px-5 text-body-content border-b border-surface-100 text-surface-700 last:border-b-0">
									<span class="inline-flex items-center gap-2 py-1 px-3 rounded-full text-auxiliary-text font-medium {getStatusBadgeClass(run.status)}">
										{PAYROLL_STATUS_LABELS[run.status]}
									</span>
								</td>
								<td class="p-4 px-5 text-body-content border-b border-surface-100 text-surface-700 last:border-b-0">
									<button
										class="p-2 bg-transparent border-none rounded-md text-surface-400 cursor-pointer transition-[150ms] hover:bg-surface-100 hover:text-primary-600"
										title="View details"
										onclick={(e) => {
											e.stopPropagation();
											selectRun(run);
										}}
									>
										<i class="fas fa-chevron-right"></i>
									</button>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			<!-- Pagination -->
			{#if totalPages > 1}
				<div class="flex items-center justify-between max-md:flex-col max-md:gap-3">
					<span class="text-body-content text-surface-600">
						Showing {showingStart}-{showingEnd} of {totalCount} payroll runs
					</span>
					<div class="flex gap-2">
						<button
							class="min-w-9 h-9 px-3 bg-white border border-surface-200 rounded-md text-body-content text-surface-700 cursor-pointer transition-[150ms] hover:bg-surface-50 hover:border-primary-300 disabled:opacity-50 disabled:cursor-not-allowed"
							disabled={currentPage === 1}
							onclick={() => changePage(currentPage - 1)}
							aria-label="Previous page"
						>
							<i class="fas fa-chevron-left"></i>
						</button>
						{#each Array(Math.min(totalPages, 5)) as _, i}
							{@const page = i + 1}
							<button
								class="min-w-9 h-9 px-3 rounded-md text-body-content cursor-pointer transition-[150ms] {currentPage === page
									? 'bg-primary-500 border border-primary-500 text-white'
									: 'bg-white border border-surface-200 text-surface-700 hover:bg-surface-50 hover:border-primary-300'}"
								onclick={() => changePage(page)}
							>
								{page}
							</button>
						{/each}
						<button
							class="min-w-9 h-9 px-3 bg-white border border-surface-200 rounded-md text-body-content text-surface-700 cursor-pointer transition-[150ms] hover:bg-surface-50 hover:border-primary-300 disabled:opacity-50 disabled:cursor-not-allowed"
							disabled={currentPage === totalPages}
							onclick={() => changePage(currentPage + 1)}
							aria-label="Next page"
						>
							<i class="fas fa-chevron-right"></i>
						</button>
					</div>
				</div>
			{:else}
				<div class="text-body-content text-surface-600">
					Showing {runs.length} payroll run{runs.length !== 1 ? 's' : ''}
				</div>
			{/if}
		{/if}
	</div>
</div>

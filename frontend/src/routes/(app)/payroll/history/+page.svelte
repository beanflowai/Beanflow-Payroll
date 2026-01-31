<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import type { PayrollRunWithGroups, PayrollRunStatus } from '$lib/types/payroll';
	import type { PayGroup } from '$lib/types/pay-group';
	import type { Employee } from '$lib/types/employee';
	import { PAYROLL_STATUS_LABELS } from '$lib/types/payroll';
	import {
		listPayrollRuns,
		listPayrollRecordsForEmployee,
		type PayrollRunListOptionsExt,
		type PayrollRecordWithPeriod
	} from '$lib/services/payroll';
	import { listPayGroups } from '$lib/services/payGroupService';
	import { listEmployees } from '$lib/services/employeeService';
	import { formatShortDate } from '$lib/utils/dateUtils';
	import { formatCurrency } from '$lib/utils/formatUtils';
	import { companyState } from '$lib/stores/company.svelte';
	import { TableSkeleton, AlertBanner, EmptyState } from '$lib/components/shared';
	import PayrollHistoryFiltersComponent from '$lib/components/payroll/PayrollHistoryFilters.svelte';
	import PayrollHistorySummary from '$lib/components/payroll/PayrollHistorySummary.svelte';
	import type { PayrollHistoryFilters } from '$lib/types/payroll-filters';
	import { DEFAULT_PAYROLL_HISTORY_FILTERS } from '$lib/types/payroll-filters';



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
	let employeeRecords = $state<PayrollRecordWithPeriod[]>([]); // For employee detail view
	let payGroups = $state<PayGroup[]>([]);
	let employees = $state<Employee[]>([]);
	let filters = $state<PayrollHistoryFilters>(DEFAULT_PAYROLL_HISTORY_FILTERS);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let activeTab = $state<FilterTab>('all');
	let currentPage = $state(1);
	let totalCount = $state(0);

	// Derived: are we in employee detail view?
	const isEmployeeView = $derived(filters.employeeId !== 'all' && filters.employeeId !== '');

	// Constants
	const PAGE_SIZE = 20;

	// Get filter options based on active tab and filters
	function getFilterOptions(): PayrollRunListOptionsExt {
		const offset = (currentPage - 1) * PAGE_SIZE;

		const baseOptions: PayrollRunListOptionsExt = {
			limit: PAGE_SIZE,
			offset
		};

		// Status filter (from tabs)
		switch (activeTab) {
			case 'draft':
				baseOptions.status = 'draft';
				break;
			case 'pending':
				baseOptions.status = 'pending_approval';
				break;
			case 'completed':
				baseOptions.excludeStatuses = ['draft', 'pending_approval', 'cancelled'];
				break;
			case 'cancelled':
				baseOptions.status = 'cancelled';
				break;
		}

		// Pay group filter
		if (filters.payGroupId && filters.payGroupId !== 'all') {
			baseOptions.payGroupId = filters.payGroupId;
		}

		// Employee filter
		if (filters.employeeId && filters.employeeId !== 'all') {
			baseOptions.employeeId = filters.employeeId;
		}

		// Date range filter
		if (filters.dateRange) {
			baseOptions.startDate = filters.dateRange.from;
			baseOptions.endDate = filters.dateRange.to;
		}

		return baseOptions;
	}

	// Load pay groups
	async function loadPayGroups(): Promise<void> {
		const companyId = companyState.currentCompany?.id;
		if (!companyId) return;

		const result = await listPayGroups({ company_id: companyId });
		if (result.data) {
			payGroups = result.data;
		}
	}

	// Load employees
	async function loadEmployees(): Promise<void> {
		const result = await listEmployees();
		if (result.data) {
			employees = result.data;
		}
	}

	// Filter change handler
	function handleFiltersChange(newFilters: PayrollHistoryFilters) {
		filters = newFilters;
		currentPage = 1; // Reset to first page when filters change
		loadRuns();
	}

	// Load payroll runs or employee records (based on view mode)
	async function loadRuns() {
		error = null;

		// Check if we should use employee view (specific employee selected)
		const shouldUseEmployeeView = filters.employeeId !== 'all' && filters.employeeId !== '';

		if (shouldUseEmployeeView) {
			// Employee detail view: query payroll_records for this employee
			const result = await listPayrollRecordsForEmployee(filters.employeeId, {
				startDate: filters.dateRange?.from,
				endDate: filters.dateRange?.to,
				status: getStatusFromTab(activeTab),
				excludeStatuses: getExcludeStatusesFromTab(activeTab),
				limit: PAGE_SIZE,
				offset: (currentPage - 1) * PAGE_SIZE
			});

			if (result.error) {
				error = result.error;
				employeeRecords = [];
				totalCount = 0;
			} else {
				employeeRecords = result.data;
				totalCount = result.count;
				runs = []; // Clear runs when in employee view
			}
		} else {
			// Pay Run summary view: existing logic
			const options = getFilterOptions();
			const result = await listPayrollRuns(options);

			if (result.error) {
				error = result.error;
				runs = [];
				totalCount = 0;
			} else {
				runs = result.data;
				totalCount = result.count;
				employeeRecords = []; // Clear employee records when in summary view
			}
		}
	}

	// Helper: get status from active tab
	function getStatusFromTab(tab: FilterTab): PayrollRunStatus | undefined {
		switch (tab) {
			case 'draft':
				return 'draft';
			case 'pending':
				return 'pending_approval';
			case 'cancelled':
				return 'cancelled';
			default:
				return undefined;
		}
	}

	// Helper: get exclude statuses from active tab
	function getExcludeStatusesFromTab(tab: FilterTab): string[] | undefined {
		if (tab === 'completed') {
			return ['draft', 'pending_approval', 'cancelled'];
		}
		return undefined;
	}

	// Track previous company to avoid reloading same company
	let previousCompanyId: string | null = null;

	// Load when company changes
	$effect(() => {
		const company = companyState.currentCompany;
		const currentCompanyId = company?.id ?? null;

		// Only reload if company changed
		if (currentCompanyId !== previousCompanyId) {
			previousCompanyId = currentCompanyId;

			if (company) {
				loadAllData();
			} else if (!companyState.isLoading) {
				// Company cleared
				loading = false;
				runs = [];
				payGroups = [];
				employees = [];
				totalCount = 0;
			}
		}
	});

	// Load all data (employees, pay groups, runs)
	async function loadAllData() {
		try {
			loading = true;
			error = null;
			await Promise.all([loadEmployees(), loadPayGroups()]);
			await loadRuns();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load data';
		} finally {
			loading = false;
		}
	}

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

	// Select an employee record to navigate to payroll run page
	function selectEmployeeRecord(record: PayrollRecordWithPeriod) {
		goto(`/payroll/run/${record.periodEnd}`);
	}

	// Computed
	const totalPages = $derived(Math.ceil(totalCount / PAGE_SIZE));
	// Calculate total net pay based on view mode
	const ytdTotalPaid = $derived(
		isEmployeeView
			? employeeRecords.reduce((sum, r) => sum + r.netPay, 0)
			: runs.reduce((sum, run) => sum + run.totalNetPay, 0)
	);
	const showingStart = $derived((currentPage - 1) * PAGE_SIZE + 1);
	const showingEnd = $derived(Math.min(currentPage * PAGE_SIZE, totalCount));

	// Helpers
	function _formatPeriod(start: string, end: string): string {
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

	function formatTableCellValue(value: number | undefined | null): string {
		if (value === undefined || value === null || value === 0) {
			return '-';
		}
		return formatCurrency(value, { maximumFractionDigits: 2 });
	}
</script>

<svelte:head>
	<title>Payroll History - BeanFlow Payroll</title>
</svelte:head>

<div class="max-w-[1400px] mx-auto">
	<!-- Main Content -->
	<div class="flex-1 min-w-0">
		<header class="flex items-start justify-between mb-8 max-md:flex-col max-md:gap-4">
			<div class="flex-1">
				<h1 class="text-3xl font-bold text-surface-900 tracking-tight m-0 mb-1">Payroll History</h1>
				<p class="text-base text-surface-500 m-0">View past payroll runs and details</p>
			</div>
			<div class="flex items-center gap-3">
				<button
					class="flex items-center gap-2 py-2.5 px-4 bg-white text-surface-700 border border-surface-200 rounded-lg text-sm font-semibold cursor-pointer transition-all hover:bg-surface-50 hover:border-surface-300 hover:shadow-sm active:scale-95"
				>
					<i class="fas fa-file-export text-surface-400"></i>
					<span>Export CSV</span>
				</button>
				<button
					onclick={() => goto('/payroll')}
					class="flex items-center gap-2 py-2.5 px-5 bg-primary-600 text-white rounded-lg text-sm font-semibold cursor-pointer transition-all hover:bg-primary-700 shadow-md shadow-primary-500/20 active:scale-95"
				>
					<i class="fas fa-play"></i>
					<span>Run Payroll</span>
				</button>
			</div>
		</header>

		<!-- Filter Tabs -->
		<div class="flex gap-1 mb-4 border-b border-surface-200">
			{#each filterTabs as tab (tab.key)}
				<button
					class="py-3 px-4 text-body-content font-medium border-b-2 -mb-px transition-colors cursor-pointer bg-transparent border-l-0 border-r-0 border-t-0 {activeTab ===
					tab.key
						? 'text-primary-600 border-primary-600'
						: 'text-surface-600 border-transparent hover:text-surface-800'}"
					onclick={() => changeTab(tab.key)}
				>
					{tab.label}
				</button>
			{/each}
		</div>

		<!-- Payroll History Filters -->
		{#if payGroups.length > 0}
			<PayrollHistoryFiltersComponent
				{filters}
				{payGroups}
				{employees}
				onFiltersChange={handleFiltersChange}
			/>
		{/if}

		<!-- Loading State -->
		{#if loading}
			<TableSkeleton rows={6} columns={5} />
		{:else if !companyState.currentCompany}
			<EmptyState
				icon="fa-building"
				title="No Company Selected"
				description="Please select or create a company to view payroll history."
				variant="card"
			/>
		{:else if error}
			<AlertBanner type="error" title="Failed to load payroll history" message={error}>
				<button
					class="py-2 px-4 bg-error-600 text-white rounded-lg text-sm font-medium cursor-pointer hover:bg-error-700 mt-2"
					onclick={() => loadRuns()}
				>
					Try Again
				</button>
			</AlertBanner>
		{:else if (isEmployeeView && employeeRecords.length === 0) || (!isEmployeeView && runs.length === 0)}
			<EmptyState
				icon="fa-history"
				title={isEmployeeView ? 'No Payroll Records Found' : 'No Payroll Runs Found'}
				description={isEmployeeView
					? 'No payroll records found for this employee.'
					: activeTab === 'all'
						? "You haven't created any payroll runs yet."
						: activeTab === 'draft'
							? 'No draft payroll runs.'
							: activeTab === 'pending'
								? 'No payroll runs are pending approval.'
								: activeTab === 'completed'
									? 'No completed payroll runs.'
									: 'No cancelled payroll runs.'}
				variant="card"
			/>
		{:else}
			<!-- Summary Stats -->
			<PayrollHistorySummary
				count={totalCount}
				{isEmployeeView}
				records={isEmployeeView ? employeeRecords : runs}
			/>

			<!-- History Table -->
			<div class="bg-surface-50 rounded-xl overflow-hidden mb-4">
				<div class="overflow-x-auto">
					<table class="w-full border-collapse min-w-[1400px]">
						<thead>
							<!-- First row: Group headers -->
							<tr class="bg-surface-100">
								<th
									rowspan="2"
									class="border-b border-r border-surface-300 text-center py-3 px-4 text-xs font-semibold text-surface-600 uppercase tracking-wider"
									>Period End</th
								>
								{#if !isEmployeeView}
									<th
										rowspan="2"
										class="border-b border-r border-surface-300 text-center py-3 px-4 text-xs font-semibold text-surface-600 uppercase tracking-wider"
										>Emp</th
									>
								{/if}
								<th
									rowspan="2"
									class="border-b border-r border-surface-300 text-center py-3 px-4 text-xs font-semibold text-surface-600 uppercase tracking-wider"
									>Gross Pay</th
								>

								<!-- Employee Deductions group -->
								<th
									colspan="4"
									class="border-b border-r border-surface-300 text-center py-3 px-4 text-xs font-semibold text-surface-600 uppercase tracking-wider"
									>Employee Deductions</th
								>

								<!-- Employer Contributions group -->
								<th
									colspan="2"
									class="border-b border-r border-surface-300 text-center py-3 px-4 text-xs font-semibold text-surface-600 uppercase tracking-wider"
									>Employer Contributions</th
								>

								<!-- Remittance group -->
								<th
									colspan="3"
									class="border-b border-surface-300 text-center py-3 px-4 text-xs font-semibold text-surface-600 uppercase tracking-wider"
									>Remittance</th
								>

								<!-- Status -->
								<th
									rowspan="2"
									class="border-b border-surface-300 text-center py-3 px-4 text-xs font-semibold text-surface-600 uppercase tracking-wider"
									>Status</th
								>

								<!-- Action -->
								<th rowspan="2" class="border-b border-surface-300 py-3 px-4"></th>
							</tr>

							<!-- Second row: Specific column headers -->
							<tr class="bg-surface-100">
								<!-- Employee Deductions -->
								<th
									class="border-b border-r border-surface-300 text-center py-2 px-4 text-xs font-semibold text-surface-600"
									>CPP</th
								>
								<th
									class="border-b border-r border-surface-300 text-center py-2 px-4 text-xs font-semibold text-surface-600"
									>EI</th
								>
								<th
									class="border-b border-r border-surface-300 text-center py-2 px-4 text-xs font-semibold text-surface-600"
									>Tax</th
								>
								<th
									class="border-b border-r border-surface-300 text-center py-2 px-4 text-xs font-semibold text-surface-600"
									>Net Pay</th
								>

								<!-- Employer Contributions -->
								<th
									class="border-b border-r border-surface-300 text-center py-2 px-4 text-xs font-semibold text-surface-600"
									>CPP</th
								>
								<th
									class="border-b border-r border-surface-300 text-center py-2 px-4 text-xs font-semibold text-surface-600"
									>EI</th
								>

								<!-- Remittance -->
								<th
									class="border-b border-r border-surface-300 text-center py-2 px-4 text-xs font-semibold text-surface-600"
									>Total CPP</th
								>
								<th
									class="border-b border-r border-surface-300 text-center py-2 px-4 text-xs font-semibold text-surface-600"
									>Total EI</th
								>
								<th
									class="border-b border-surface-300 text-center py-2 px-4 text-xs font-semibold text-surface-600"
									>Remit</th
								>
							</tr>
						</thead>
						<tbody>
							{#if isEmployeeView}
								<!-- Employee Records View -->
								{#each employeeRecords as record (record.id)}
									<tr
										class="cursor-pointer transition-[150ms] hover:bg-white"
										onclick={() => selectEmployeeRecord(record)}
										role="button"
										tabindex="0"
										onkeydown={(e) => e.key === 'Enter' && selectEmployeeRecord(record)}
									>
										<!-- Period End -->
										<td
											class="border-b border-surface-200 py-4 px-5 text-sm text-surface-700 font-medium text-left"
											>{formatShortDate(record.periodEnd)}</td
										>

										<!-- No Employees column in employee view -->

										<!-- Gross Pay -->
										<td
											class="border-b border-surface-200 py-4 px-5 text-sm text-surface-700 font-mono text-right"
											>{formatTableCellValue(record.totalGross)}</td
										>

										<!-- Employee Deductions: CPP -->
										<td
											class="border-b border-surface-200 py-4 px-5 text-sm text-surface-600 font-mono text-right"
											>{formatTableCellValue(record.cppEmployee + record.cppAdditional)}</td
										>

										<!-- Employee Deductions: EI -->
										<td
											class="border-b border-surface-200 py-4 px-5 text-sm text-surface-600 font-mono text-right"
											>{formatTableCellValue(record.eiEmployee)}</td
										>

										<!-- Employee Deductions: Tax -->
										<td
											class="border-b border-surface-200 py-4 px-5 text-sm text-surface-600 font-mono text-right"
											>{formatTableCellValue(
												(record.federalTax || 0) + (record.provincialTax || 0)
											)}</td
										>

										<!-- Employee Deductions: Net Pay -->
										<td
											class="border-b border-surface-200 py-4 px-5 text-sm text-surface-700 font-mono font-semibold text-right"
											>{formatTableCellValue(record.netPay)}</td
										>

										<!-- Employer Contributions: CPP -->
										<td
											class="border-b border-surface-200 py-4 px-5 text-sm text-surface-600 font-mono text-right"
											>{formatTableCellValue(record.cppEmployer)}</td
										>

										<!-- Employer Contributions: EI -->
										<td
											class="border-b border-surface-200 py-4 px-5 text-sm text-surface-600 font-mono text-right"
											>{formatTableCellValue(record.eiEmployer)}</td
										>

										<!-- Remittance: Total CPP -->
										<td
											class="border-b border-surface-200 py-4 px-5 text-sm text-surface-600 font-mono text-right"
											>{formatTableCellValue(
												(record.cppEmployee || 0) +
													(record.cppAdditional || 0) +
													(record.cppEmployer || 0)
											)}</td
										>

										<!-- Remittance: Total EI -->
										<td
											class="border-b border-surface-200 py-4 px-5 text-sm text-surface-600 font-mono text-right"
											>{formatTableCellValue(
												(record.eiEmployee || 0) + (record.eiEmployer || 0)
											)}</td
										>

										<!-- Remittance: Remit (Total CPP + Total EI + Tax) -->
										<td
											class="border-b border-surface-200 py-4 px-5 text-sm text-surface-700 font-mono font-semibold text-primary-600 text-right"
											>{formatTableCellValue(
												(record.cppEmployee || 0) +
													(record.cppAdditional || 0) +
													(record.cppEmployer || 0) +
													(record.eiEmployee || 0) +
													(record.eiEmployer || 0) +
													(record.federalTax || 0) +
													(record.provincialTax || 0)
											)}</td
										>

										<!-- Status -->
										<td class="border-b border-surface-200 py-4 px-5 text-center">
											<span
												class="inline-flex items-center gap-2 py-1 px-3 rounded-full text-xs font-medium {getStatusBadgeClass(
													record.runStatus
												)}"
											>
												{PAYROLL_STATUS_LABELS[record.runStatus]}
											</span>
										</td>

										<!-- Action -->
										<td class="border-b border-surface-200 py-4 px-5">
											<button
												class="p-2 bg-transparent border-none rounded-md text-surface-400 cursor-pointer transition-[150ms] hover:bg-surface-200 hover:text-primary-600"
												title="View details"
												onclick={(e) => {
													e.stopPropagation();
													selectEmployeeRecord(record);
												}}
											>
												<i class="fas fa-chevron-right"></i>
											</button>
										</td>
									</tr>
								{/each}
							{:else}
								<!-- Pay Run Summary View -->
								{#each runs as run (run.id)}
									<tr
										class="cursor-pointer transition-[150ms] hover:bg-white"
										onclick={() => selectRun(run)}
										role="button"
										tabindex="0"
										onkeydown={(e) => e.key === 'Enter' && selectRun(run)}
									>
										<!-- Period End -->
										<td
											class="border-b border-surface-200 py-4 px-5 text-sm text-surface-700 font-medium text-left"
											>{formatShortDate(run.periodEnd)}</td
										>

										<!-- Employees -->
										<td
											class="border-b border-surface-200 py-4 px-5 text-sm text-surface-600 text-right"
											>{run.totalEmployees}</td
										>

										<!-- Gross Pay -->
										<td
											class="border-b border-surface-200 py-4 px-5 text-sm text-surface-700 font-mono text-right"
											>{formatTableCellValue(run.totalGross)}</td
										>

										<!-- Employee Deductions: CPP -->
										<td
											class="border-b border-surface-200 py-4 px-5 text-sm text-surface-600 font-mono text-right"
											>{formatTableCellValue(run.totalCppEmployee)}</td
										>

										<!-- Employee Deductions: EI -->
										<td
											class="border-b border-surface-200 py-4 px-5 text-sm text-surface-600 font-mono text-right"
											>{formatTableCellValue(run.totalEiEmployee)}</td
										>

										<!-- Employee Deductions: Tax -->
										<td
											class="border-b border-surface-200 py-4 px-5 text-sm text-surface-600 font-mono text-right"
											>{formatTableCellValue(
												(run.totalFederalTax || 0) + (run.totalProvincialTax || 0)
											)}</td
										>

										<!-- Employee Deductions: Net Pay -->
										<td
											class="border-b border-surface-200 py-4 px-5 text-sm text-surface-700 font-mono font-semibold text-right"
											>{formatTableCellValue(run.totalNetPay)}</td
										>

										<!-- Employer Contributions: CPP -->
										<td
											class="border-b border-surface-200 py-4 px-5 text-sm text-surface-600 font-mono text-right"
											>{formatTableCellValue(run.totalCppEmployer)}</td
										>

										<!-- Employer Contributions: EI -->
										<td
											class="border-b border-surface-200 py-4 px-5 text-sm text-surface-600 font-mono text-right"
											>{formatTableCellValue(run.totalEiEmployer)}</td
										>

										<!-- Remittance: Total CPP -->
										<td
											class="border-b border-surface-200 py-4 px-5 text-sm text-surface-600 font-mono text-right"
											>{formatTableCellValue(
												(run.totalCppEmployee || 0) + (run.totalCppEmployer || 0)
											)}</td
										>

										<!-- Remittance: Total EI -->
										<td
											class="border-b border-surface-200 py-4 px-5 text-sm text-surface-600 font-mono text-right"
											>{formatTableCellValue(
												(run.totalEiEmployee || 0) + (run.totalEiEmployer || 0)
											)}</td
										>

										<!-- Remittance: Remit -->
										<td
											class="border-b border-surface-200 py-4 px-5 text-sm text-surface-700 font-mono font-semibold text-primary-600 text-right"
											>{formatTableCellValue(run.totalRemittance)}</td
										>

										<!-- Status -->
										<td class="border-b border-surface-200 py-4 px-5 text-center">
											<span
												class="inline-flex items-center gap-2 py-1 px-3 rounded-full text-xs font-medium {getStatusBadgeClass(
													run.status
												)}"
											>
												{PAYROLL_STATUS_LABELS[run.status]}
											</span>
										</td>

										<!-- Action -->
										<td class="border-b border-surface-200 py-4 px-5">
											<button
												class="p-2 bg-transparent border-none rounded-md text-surface-400 cursor-pointer transition-[150ms] hover:bg-surface-200 hover:text-primary-600"
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
							{/if}
						</tbody>
					</table>
				</div>
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
						{#each Array(Math.min(totalPages, 5)) as _unused, i (i)}
							{@const page = i + 1}
							<button
								class="min-w-9 h-9 px-3 rounded-md text-body-content cursor-pointer transition-[150ms] {currentPage ===
								page
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

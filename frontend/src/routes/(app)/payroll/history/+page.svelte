<script lang="ts">
	import type { PayrollRun, PayrollRecord, PayrollRunStatus } from '$lib/types/payroll';
	import { PAYROLL_STATUS_LABELS } from '$lib/types/payroll';
	import PayrollRunDetailPanel from '$lib/components/payroll/PayrollRunDetailPanel.svelte';
	import { formatShortDate } from '$lib/utils/dateUtils';

	// Mock data - will be replaced with API calls
	const mockPayrollRuns: PayrollRun[] = [
		{
			id: '1',
			periodStart: '2025-12-01',
			periodEnd: '2025-12-15',
			payDate: '2025-12-20',
			status: 'paid',
			totalEmployees: 4,
			totalGross: 11538.46,
			totalCppEmployee: 560.42,
			totalCppEmployer: 560.42,
			totalEiEmployee: 196.15,
			totalEiEmployer: 274.61,
			totalFederalTax: 1200.0,
			totalProvincialTax: 800.0,
			totalDeductions: 2756.57,
			totalNetPay: 8781.89,
			totalEmployerCost: 835.03
		},
		{
			id: '2',
			periodStart: '2025-11-16',
			periodEnd: '2025-11-30',
			payDate: '2025-12-05',
			status: 'paid',
			totalEmployees: 4,
			totalGross: 11538.46,
			totalCppEmployee: 560.42,
			totalCppEmployer: 560.42,
			totalEiEmployee: 196.15,
			totalEiEmployer: 274.61,
			totalFederalTax: 1200.0,
			totalProvincialTax: 800.0,
			totalDeductions: 2756.57,
			totalNetPay: 8781.89,
			totalEmployerCost: 835.03
		},
		{
			id: '3',
			periodStart: '2025-11-01',
			periodEnd: '2025-11-15',
			payDate: '2025-11-20',
			status: 'paid',
			totalEmployees: 4,
			totalGross: 11538.46,
			totalCppEmployee: 560.42,
			totalCppEmployer: 560.42,
			totalEiEmployee: 196.15,
			totalEiEmployer: 274.61,
			totalFederalTax: 1200.0,
			totalProvincialTax: 800.0,
			totalDeductions: 2756.57,
			totalNetPay: 8781.89,
			totalEmployerCost: 835.03
		},
		{
			id: '4',
			periodStart: '2025-10-16',
			periodEnd: '2025-10-31',
			payDate: '2025-11-05',
			status: 'paid',
			totalEmployees: 4,
			totalGross: 11538.46,
			totalCppEmployee: 560.42,
			totalCppEmployer: 560.42,
			totalEiEmployee: 196.15,
			totalEiEmployer: 274.61,
			totalFederalTax: 1200.0,
			totalProvincialTax: 800.0,
			totalDeductions: 2756.57,
			totalNetPay: 8781.89,
			totalEmployerCost: 835.03
		},
		{
			id: '5',
			periodStart: '2025-10-01',
			periodEnd: '2025-10-15',
			payDate: '2025-10-20',
			status: 'paid',
			totalEmployees: 4,
			totalGross: 11538.46,
			totalCppEmployee: 560.42,
			totalCppEmployer: 560.42,
			totalEiEmployee: 196.15,
			totalEiEmployer: 274.61,
			totalFederalTax: 1200.0,
			totalProvincialTax: 800.0,
			totalDeductions: 2756.57,
			totalNetPay: 8781.89,
			totalEmployerCost: 835.03
		}
	];

	// Mock payroll records for selected run
	function getMockRecords(runId: string): PayrollRecord[] {
		return [
			{
				id: `${runId}-1`,
				employeeId: 'emp-1',
				employeeName: 'Jane Doe',
				employeeProvince: 'ON',
				grossRegular: 2884.62,
				grossOvertime: 0,
				holidayPay: 0,
				holidayPremiumPay: 0,
				vacationPayPaid: 0,
				otherEarnings: 0,
				totalGross: 2884.62,
				cppEmployee: 140.11,
				cppAdditional: 0,
				eiEmployee: 49.04,
				federalTax: 300.0,
				provincialTax: 200.0,
				rrsp: 0,
				unionDues: 0,
				garnishments: 0,
				otherDeductions: 0,
				totalDeductions: 689.15,
				netPay: 2195.47,
				cppEmployer: 140.11,
				eiEmployer: 68.66,
				totalEmployerCost: 208.77,
				ytdGross: 69230.88,
				ytdCpp: 3362.64,
				ytdEi: 1049.12,
				ytdFederalTax: 7200.0,
				ytdProvincialTax: 4800.0,
				ytdNetPay: 52619.28
			},
			{
				id: `${runId}-2`,
				employeeId: 'emp-2',
				employeeName: 'John Smith',
				employeeProvince: 'ON',
				grossRegular: 2884.62,
				grossOvertime: 0,
				holidayPay: 0,
				holidayPremiumPay: 0,
				vacationPayPaid: 0,
				otherEarnings: 0,
				totalGross: 2884.62,
				cppEmployee: 140.11,
				cppAdditional: 0,
				eiEmployee: 49.04,
				federalTax: 300.0,
				provincialTax: 200.0,
				rrsp: 0,
				unionDues: 0,
				garnishments: 0,
				otherDeductions: 0,
				totalDeductions: 689.15,
				netPay: 2195.47,
				cppEmployer: 140.11,
				eiEmployer: 68.66,
				totalEmployerCost: 208.77,
				ytdGross: 69230.88,
				ytdCpp: 3362.64,
				ytdEi: 1049.12,
				ytdFederalTax: 7200.0,
				ytdProvincialTax: 4800.0,
				ytdNetPay: 52619.28
			},
			{
				id: `${runId}-3`,
				employeeId: 'emp-3',
				employeeName: 'Mary Johnson',
				employeeProvince: 'ON',
				grossRegular: 2884.62,
				grossOvertime: 0,
				holidayPay: 0,
				holidayPremiumPay: 0,
				vacationPayPaid: 0,
				otherEarnings: 0,
				totalGross: 2884.62,
				cppEmployee: 140.11,
				cppAdditional: 0,
				eiEmployee: 49.04,
				federalTax: 300.0,
				provincialTax: 200.0,
				rrsp: 0,
				unionDues: 0,
				garnishments: 0,
				otherDeductions: 0,
				totalDeductions: 689.15,
				netPay: 2195.47,
				cppEmployer: 140.11,
				eiEmployer: 68.66,
				totalEmployerCost: 208.77,
				ytdGross: 69230.88,
				ytdCpp: 3362.64,
				ytdEi: 1049.12,
				ytdFederalTax: 7200.0,
				ytdProvincialTax: 4800.0,
				ytdNetPay: 52619.28
			},
			{
				id: `${runId}-4`,
				employeeId: 'emp-4',
				employeeName: 'James Wilson',
				employeeProvince: 'ON',
				grossRegular: 2884.6,
				grossOvertime: 0,
				holidayPay: 0,
				holidayPremiumPay: 0,
				vacationPayPaid: 0,
				otherEarnings: 0,
				totalGross: 2884.6,
				cppEmployee: 140.09,
				cppAdditional: 0,
				eiEmployee: 49.03,
				federalTax: 300.0,
				provincialTax: 200.0,
				rrsp: 0,
				unionDues: 0,
				garnishments: 0,
				otherDeductions: 0,
				totalDeductions: 689.12,
				netPay: 2195.48,
				cppEmployer: 140.09,
				eiEmployer: 68.63,
				totalEmployerCost: 208.72,
				ytdGross: 69230.4,
				ytdCpp: 3362.16,
				ytdEi: 1048.72,
				ytdFederalTax: 7200.0,
				ytdProvincialTax: 4800.0,
				ytdNetPay: 52619.52
			}
		];
	}

	// State
	let selectedRun = $state<PayrollRun | null>(null);
	let selectedRecords = $state<PayrollRecord[]>([]);

	// Computed
	const ytdTotalPaid = $derived(
		mockPayrollRuns.reduce((sum, run) => sum + run.totalNetPay, 0)
	);

	// Handlers
	function selectRun(run: PayrollRun) {
		selectedRun = run;
		selectedRecords = getMockRecords(run.id);
	}

	function closePanel() {
		selectedRun = null;
		selectedRecords = [];
	}

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

<div class="flex gap-6 max-w-[1400px] max-lg:flex-col">
	<!-- Main Content -->
	<div class="flex-1 min-w-0 {selectedRun ? 'max-lg:max-w-full max-w-[calc(100%-400px-1.5rem)]' : ''}">
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

		<!-- Summary Stats -->
		<div class="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-4 mb-6">
			<div class="flex items-center gap-4 p-5 bg-white rounded-xl shadow-md3-1">
				<div class="w-12 h-12 rounded-lg bg-primary-100 text-primary-600 flex items-center justify-center text-xl">
					<i class="fas fa-calendar-check"></i>
				</div>
				<div class="flex flex-col">
					<span class="text-title-large font-semibold text-surface-800">{mockPayrollRuns.length}</span>
					<span class="text-auxiliary-text text-surface-600">Payroll Runs (YTD)</span>
				</div>
			</div>
			<div class="flex items-center gap-4 p-5 bg-white rounded-xl shadow-md3-1">
				<div class="w-12 h-12 rounded-lg bg-primary-100 text-primary-600 flex items-center justify-center text-xl">
					<i class="fas fa-dollar-sign"></i>
				</div>
				<div class="flex flex-col">
					<span class="text-title-large font-semibold text-surface-800">{formatCurrency(ytdTotalPaid)}</span>
					<span class="text-auxiliary-text text-surface-600">Total Paid (YTD)</span>
				</div>
			</div>
			<div class="flex items-center gap-4 p-5 bg-white rounded-xl shadow-md3-1">
				<div class="w-12 h-12 rounded-lg bg-primary-100 text-primary-600 flex items-center justify-center text-xl">
					<i class="fas fa-users"></i>
				</div>
				<div class="flex flex-col">
					<span class="text-title-large font-semibold text-surface-800">4</span>
					<span class="text-auxiliary-text text-surface-600">Active Employees</span>
				</div>
			</div>
		</div>

		<!-- History Table -->
		<div class="bg-white rounded-xl shadow-md3-1 overflow-hidden mb-4 max-md:overflow-x-auto">
			<table class="w-full border-collapse max-md:min-w-[700px]">
				<thead>
					<tr>
						<th class="text-left p-4 px-5 bg-surface-50 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide border-b border-surface-200">Pay Period</th>
						<th class="text-left p-4 px-5 bg-surface-50 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide border-b border-surface-200">Pay Date</th>
						<th class="text-left p-4 px-5 bg-surface-50 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide border-b border-surface-200">Employees</th>
						<th class="text-left p-4 px-5 bg-surface-50 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide border-b border-surface-200">Gross Pay</th>
						<th class="text-left p-4 px-5 bg-surface-50 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide border-b border-surface-200">Net Pay</th>
						<th class="text-left p-4 px-5 bg-surface-50 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide border-b border-surface-200">Status</th>
						<th class="text-left p-4 px-5 bg-surface-50 text-auxiliary-text font-semibold text-surface-600 uppercase tracking-wide border-b border-surface-200"></th>
					</tr>
				</thead>
				<tbody>
					{#each mockPayrollRuns as run (run.id)}
						<tr
							class="cursor-pointer transition-[150ms] {selectedRun?.id === run.id ? '[&>td]:bg-primary-50' : ''} hover:[&>td]:bg-surface-50"
							onclick={() => selectRun(run)}
							role="button"
							tabindex="0"
							onkeydown={(e) => e.key === 'Enter' && selectRun(run)}
						>
							<td class="p-4 px-5 text-body-content border-b border-surface-100 font-medium text-surface-800 last:border-b-0">{formatPeriod(run.periodStart, run.periodEnd)}</td>
							<td class="p-4 px-5 text-body-content border-b border-surface-100 text-surface-600 last:border-b-0">{formatShortDate(run.payDate)}</td>
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
		<div class="flex items-center justify-between max-md:flex-col max-md:gap-3">
			<span class="text-body-content text-surface-600">Showing 1-{mockPayrollRuns.length} of {mockPayrollRuns.length} payroll runs</span>
			<div class="flex gap-2">
				<button class="min-w-9 h-9 px-3 bg-white border border-surface-200 rounded-md text-body-content text-surface-700 cursor-pointer transition-[150ms] hover:bg-surface-50 hover:border-primary-300 disabled:opacity-50 disabled:cursor-not-allowed" disabled aria-label="Previous page">
					<i class="fas fa-chevron-left"></i>
				</button>
				<button class="min-w-9 h-9 px-3 bg-primary-500 border border-primary-500 rounded-md text-body-content text-white cursor-pointer transition-[150ms]">1</button>
				<button class="min-w-9 h-9 px-3 bg-white border border-surface-200 rounded-md text-body-content text-surface-700 cursor-pointer transition-[150ms] hover:bg-surface-50 hover:border-primary-300" aria-label="Next page">
					<i class="fas fa-chevron-right"></i>
				</button>
			</div>
		</div>
	</div>

	<!-- Detail Panel -->
	{#if selectedRun}
		<PayrollRunDetailPanel
			payrollRun={selectedRun}
			payrollRecords={selectedRecords}
			onClose={closePanel}
		/>
	{/if}
</div>

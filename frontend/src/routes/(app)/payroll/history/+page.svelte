<script lang="ts">
	import type { PayrollRun, PayrollRecord, PayrollRunStatus } from '$lib/types/payroll';
	import { PAYROLL_STATUS_LABELS } from '$lib/types/payroll';
	import PayrollRunDetailPanel from '$lib/components/payroll/PayrollRunDetailPanel.svelte';

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

	function formatDate(dateStr: string): string {
		return new Date(dateStr).toLocaleDateString('en-CA', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	function formatPeriod(start: string, end: string): string {
		const startDate = new Date(start);
		const endDate = new Date(end);
		const startStr = startDate.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' });
		const endStr = endDate.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' });
		return `${startStr} - ${endStr}`;
	}

	function getStatusClass(status: PayrollRunStatus): string {
		switch (status) {
			case 'paid':
				return 'status-paid';
			case 'approved':
				return 'status-approved';
			case 'pending_approval':
				return 'status-pending';
			case 'draft':
				return 'status-draft';
			case 'cancelled':
				return 'status-cancelled';
			default:
				return '';
		}
	}
</script>

<svelte:head>
	<title>Payroll History - BeanFlow Payroll</title>
</svelte:head>

<div class="history-page" class:panel-open={selectedRun !== null}>
	<!-- Main Content -->
	<div class="main-content">
		<header class="page-header">
			<div class="header-content">
				<h1 class="page-title">Payroll History</h1>
				<p class="page-subtitle">View past payroll runs and details</p>
			</div>
			<div class="header-actions">
				<button class="btn-secondary">
					<i class="fas fa-download"></i>
					<span>Export</span>
				</button>
			</div>
		</header>

		<!-- Summary Stats -->
		<div class="stats-grid">
			<div class="stat-card">
				<div class="stat-icon">
					<i class="fas fa-calendar-check"></i>
				</div>
				<div class="stat-content">
					<span class="stat-value">{mockPayrollRuns.length}</span>
					<span class="stat-label">Payroll Runs (YTD)</span>
				</div>
			</div>
			<div class="stat-card">
				<div class="stat-icon">
					<i class="fas fa-dollar-sign"></i>
				</div>
				<div class="stat-content">
					<span class="stat-value">{formatCurrency(ytdTotalPaid)}</span>
					<span class="stat-label">Total Paid (YTD)</span>
				</div>
			</div>
			<div class="stat-card">
				<div class="stat-icon">
					<i class="fas fa-users"></i>
				</div>
				<div class="stat-content">
					<span class="stat-value">4</span>
					<span class="stat-label">Active Employees</span>
				</div>
			</div>
		</div>

		<!-- History Table -->
		<div class="table-container">
			<table class="history-table">
				<thead>
					<tr>
						<th>Pay Period</th>
						<th>Pay Date</th>
						<th>Employees</th>
						<th>Gross Pay</th>
						<th>Net Pay</th>
						<th>Status</th>
						<th></th>
					</tr>
				</thead>
				<tbody>
					{#each mockPayrollRuns as run (run.id)}
						<tr
							class:selected={selectedRun?.id === run.id}
							onclick={() => selectRun(run)}
							role="button"
							tabindex="0"
							onkeydown={(e) => e.key === 'Enter' && selectRun(run)}
						>
							<td class="period">{formatPeriod(run.periodStart, run.periodEnd)}</td>
							<td class="pay-date">{formatDate(run.payDate)}</td>
							<td>{run.totalEmployees}</td>
							<td class="amount">{formatCurrency(run.totalGross)}</td>
							<td class="amount net">{formatCurrency(run.totalNetPay)}</td>
							<td>
								<span class="status-badge {getStatusClass(run.status)}">
									{PAYROLL_STATUS_LABELS[run.status]}
								</span>
							</td>
							<td>
								<button
									class="action-btn"
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
		<div class="pagination">
			<span class="pagination-info">Showing 1-{mockPayrollRuns.length} of {mockPayrollRuns.length} payroll runs</span>
			<div class="pagination-controls">
				<button class="pagination-btn" disabled aria-label="Previous page">
					<i class="fas fa-chevron-left"></i>
				</button>
				<button class="pagination-btn active">1</button>
				<button class="pagination-btn" aria-label="Next page">
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

<style>
	.history-page {
		display: flex;
		gap: var(--spacing-6);
		max-width: 1400px;
	}

	.main-content {
		flex: 1;
		min-width: 0;
	}

	.history-page.panel-open .main-content {
		max-width: calc(100% - 400px - var(--spacing-6));
	}

	.page-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		margin-bottom: var(--spacing-6);
	}

	.header-content {
		flex: 1;
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

	.btn-secondary {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-5);
		background: white;
		color: var(--color-surface-700);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-secondary:hover {
		background: var(--color-surface-50);
		border-color: var(--color-surface-300);
	}

	/* Stats Grid */
	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: var(--spacing-4);
		margin-bottom: var(--spacing-6);
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
		background: var(--color-primary-100);
		color: var(--color-primary-600);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 20px;
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

	/* Table */
	.table-container {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		overflow: hidden;
		margin-bottom: var(--spacing-4);
	}

	.history-table {
		width: 100%;
		border-collapse: collapse;
	}

	.history-table th {
		text-align: left;
		padding: var(--spacing-4) var(--spacing-5);
		background: var(--color-surface-50);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-600);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		border-bottom: 1px solid var(--color-surface-200);
	}

	.history-table td {
		padding: var(--spacing-4) var(--spacing-5);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.history-table tr:last-child td {
		border-bottom: none;
	}

	.history-table tbody tr {
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.history-table tbody tr:hover td {
		background: var(--color-surface-50);
	}

	.history-table tbody tr.selected td {
		background: var(--color-primary-50);
	}

	.period {
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.pay-date {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
	}

	.amount {
		font-family: monospace;
	}

	.amount.net {
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	/* Status Badge */
	.status-badge {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-1) var(--spacing-3);
		border-radius: var(--radius-full);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
	}

	.status-badge.status-paid {
		background: var(--color-success-100);
		color: var(--color-success-700);
	}

	.status-badge.status-approved {
		background: var(--color-info-100);
		color: var(--color-info-700);
	}

	.status-badge.status-pending {
		background: var(--color-warning-100);
		color: var(--color-warning-700);
	}

	.status-badge.status-draft {
		background: var(--color-surface-100);
		color: var(--color-surface-600);
	}

	.status-badge.status-cancelled {
		background: var(--color-error-100);
		color: var(--color-error-700);
	}

	.action-btn {
		padding: var(--spacing-2);
		background: none;
		border: none;
		border-radius: var(--radius-md);
		color: var(--color-surface-400);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.action-btn:hover {
		background: var(--color-surface-100);
		color: var(--color-primary-600);
	}

	/* Pagination */
	.pagination {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.pagination-info {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
	}

	.pagination-controls {
		display: flex;
		gap: var(--spacing-2);
	}

	.pagination-btn {
		min-width: 36px;
		height: 36px;
		padding: 0 var(--spacing-3);
		background: white;
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.pagination-btn:hover:not(:disabled) {
		background: var(--color-surface-50);
		border-color: var(--color-primary-300);
	}

	.pagination-btn.active {
		background: var(--color-primary-500);
		border-color: var(--color-primary-500);
		color: white;
	}

	.pagination-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	@media (max-width: 1024px) {
		.history-page {
			flex-direction: column;
		}

		.history-page.panel-open .main-content {
			max-width: 100%;
		}
	}

	@media (max-width: 768px) {
		.page-header {
			flex-direction: column;
			gap: var(--spacing-4);
		}

		.table-container {
			overflow-x: auto;
		}

		.history-table {
			min-width: 700px;
		}

		.pagination {
			flex-direction: column;
			gap: var(--spacing-3);
		}
	}
</style>

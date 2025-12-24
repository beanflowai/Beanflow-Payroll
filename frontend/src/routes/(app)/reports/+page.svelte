<script lang="ts">
	// Reports page - Phase 0 static UI prototype
	import { formatShortDate } from '$lib/utils/dateUtils';

	const reportTypes = [
		{
			id: 'remittance',
			title: 'CRA Remittance Summary',
			description: 'Monthly payroll deduction remittance report for CRA',
			icon: 'fa-file-invoice-dollar',
			color: 'primary'
		},
		{
			id: 'ytd',
			title: 'Year-to-Date Summary',
			description: 'Cumulative payroll totals for the current year',
			icon: 'fa-calendar-alt',
			color: 'success'
		},
		{
			id: 't4',
			title: 'T4 Summary',
			description: 'Annual T4 slip preparation and submission',
			icon: 'fa-file-alt',
			color: 'warning'
		},
		{
			id: 'roe',
			title: 'ROE Report',
			description: 'Record of Employment generation',
			icon: 'fa-user-minus',
			color: 'secondary'
		},
		{
			id: 'payroll-register',
			title: 'Payroll Register',
			description: 'Detailed breakdown of each payroll run',
			icon: 'fa-list-alt',
			color: 'tertiary'
		},
		{
			id: 'deduction',
			title: 'Deduction Report',
			description: 'Summary of all payroll deductions',
			icon: 'fa-minus-circle',
			color: 'error'
		}
	];

	const recentReports = [
		{
			id: '1',
			name: 'CRA Remittance - November 2025',
			type: 'Remittance Summary',
			generatedAt: '2025-12-01',
			status: 'ready'
		},
		{
			id: '2',
			name: 'YTD Summary - Q4 2025',
			type: 'Year-to-Date',
			generatedAt: '2025-11-30',
			status: 'ready'
		},
		{
			id: '3',
			name: 'Payroll Register - Nov 2025',
			type: 'Payroll Register',
			generatedAt: '2025-11-15',
			status: 'ready'
		}
	];

	function formatDate(dateStr: string): string {
		return formatShortDate(dateStr);
	}
</script>

<svelte:head>
	<title>Reports - BeanFlow Payroll</title>
</svelte:head>

<div class="reports-page">
	<header class="page-header">
		<h1 class="page-title">Reports</h1>
		<p class="page-subtitle">Generate and download payroll reports</p>
	</header>

	<!-- Report Types Grid -->
	<section class="section">
		<h2 class="section-title">Generate Report</h2>
		<div class="reports-grid">
			{#each reportTypes as report (report.id)}
				<button class="report-card">
					<div class="report-icon {report.color}">
						<i class="fas {report.icon}"></i>
					</div>
					<div class="report-content">
						<h3 class="report-title">{report.title}</h3>
						<p class="report-description">{report.description}</p>
					</div>
					<i class="fas fa-chevron-right report-arrow"></i>
				</button>
			{/each}
		</div>
	</section>

	<!-- Recent Reports -->
	<section class="section">
		<h2 class="section-title">Recent Reports</h2>
		<div class="table-container">
			<table class="reports-table">
				<thead>
					<tr>
						<th>Report Name</th>
						<th>Type</th>
						<th>Generated</th>
						<th>Status</th>
						<th></th>
					</tr>
				</thead>
				<tbody>
					{#each recentReports as report (report.id)}
						<tr>
							<td class="report-name">{report.name}</td>
							<td>{report.type}</td>
							<td>{formatDate(report.generatedAt)}</td>
							<td>
								<span class="status-badge ready">
									<i class="fas fa-check-circle"></i>
									Ready
								</span>
							</td>
							<td>
								<div class="action-buttons">
									<button class="action-btn" title="View">
										<i class="fas fa-eye"></i>
									</button>
									<button class="action-btn" title="Download PDF">
										<i class="fas fa-file-pdf"></i>
									</button>
									<button class="action-btn" title="Download CSV">
										<i class="fas fa-file-csv"></i>
									</button>
								</div>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</section>
</div>

<style>
	.reports-page {
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

	.section {
		margin-bottom: var(--spacing-8);
	}

	.section-title {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-4);
	}

	/* Reports Grid */
	.reports-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
		gap: var(--spacing-4);
	}

	.report-card {
		display: flex;
		align-items: center;
		gap: var(--spacing-4);
		padding: var(--spacing-5);
		background: white;
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-xl);
		cursor: pointer;
		transition: var(--transition-fast);
		text-align: left;
	}

	.report-card:hover {
		border-color: var(--color-primary-300);
		box-shadow: var(--shadow-md3-1);
		transform: translateY(-2px);
	}

	.report-icon {
		width: 48px;
		height: 48px;
		min-width: 48px;
		border-radius: var(--radius-lg);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 20px;
	}

	.report-icon.primary {
		background: var(--color-primary-100);
		color: var(--color-primary-600);
	}

	.report-icon.success {
		background: var(--color-success-100);
		color: var(--color-success-600);
	}

	.report-icon.warning {
		background: var(--color-warning-100);
		color: var(--color-warning-600);
	}

	.report-icon.secondary {
		background: var(--color-secondary-100);
		color: var(--color-secondary-600);
	}

	.report-icon.tertiary {
		background: var(--color-tertiary-100);
		color: var(--color-tertiary-600);
	}

	.report-icon.error {
		background: var(--color-error-100);
		color: var(--color-error-600);
	}

	.report-content {
		flex: 1;
	}

	.report-title {
		font-size: var(--font-size-body-content-large);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-1);
	}

	.report-description {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
		margin: 0;
	}

	.report-arrow {
		color: var(--color-surface-400);
		font-size: 14px;
		transition: var(--transition-fast);
	}

	.report-card:hover .report-arrow {
		color: var(--color-primary-500);
		transform: translateX(4px);
	}

	/* Table */
	.table-container {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		overflow: hidden;
	}

	.reports-table {
		width: 100%;
		border-collapse: collapse;
	}

	.reports-table th {
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

	.reports-table td {
		padding: var(--spacing-4) var(--spacing-5);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.reports-table tr:last-child td {
		border-bottom: none;
	}

	.reports-table tr:hover td {
		background: var(--color-surface-50);
	}

	.report-name {
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.status-badge {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-1) var(--spacing-3);
		border-radius: var(--radius-full);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
	}

	.status-badge.ready {
		background: var(--color-success-100);
		color: var(--color-success-700);
	}

	.status-badge i {
		font-size: 12px;
	}

	.action-buttons {
		display: flex;
		gap: var(--spacing-2);
	}

	.action-btn {
		padding: var(--spacing-2);
		background: none;
		border: none;
		border-radius: var(--radius-md);
		color: var(--color-surface-500);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.action-btn:hover {
		background: var(--color-surface-100);
		color: var(--color-primary-600);
	}

	@media (max-width: 768px) {
		.reports-grid {
			grid-template-columns: 1fr;
		}

		.table-container {
			overflow-x: auto;
		}

		.reports-table {
			min-width: 600px;
		}
	}
</style>

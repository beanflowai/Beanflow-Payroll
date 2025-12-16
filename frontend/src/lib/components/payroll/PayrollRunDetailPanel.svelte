<script lang="ts">
	import type { PayrollRun, PayrollRecord } from '$lib/types/payroll';
	import { PAYROLL_STATUS_LABELS } from '$lib/types/payroll';

	interface Props {
		payrollRun: PayrollRun;
		payrollRecords: PayrollRecord[];
		onClose: () => void;
	}

	let { payrollRun, payrollRecords, onClose }: Props = $props();

	// Helpers
	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			minimumFractionDigits: 2
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
		const endStr = endDate.toLocaleDateString('en-CA', {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		});
		return `${startStr} - ${endStr}`;
	}

	function getStatusClass(status: string): string {
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

<aside class="detail-panel">
	<div class="panel-header">
		<div class="header-info">
			<h2>{formatPeriod(payrollRun.periodStart, payrollRun.periodEnd)}</h2>
			<span class="status-badge {getStatusClass(payrollRun.status)}">
				{PAYROLL_STATUS_LABELS[payrollRun.status]}
			</span>
		</div>
		<button class="close-btn" onclick={onClose} aria-label="Close panel">
			<i class="fas fa-times"></i>
		</button>
	</div>

	<div class="panel-content">
		<!-- Pay Date -->
		<div class="pay-date-row">
			<span class="label">Pay Date</span>
			<span class="value">{formatDate(payrollRun.payDate)}</span>
		</div>

		<!-- Summary Cards - 2x2 Grid -->
		<section class="summary-section">
			<div class="summary-grid">
				<div class="summary-card">
					<span class="card-label">TOTAL GROSS</span>
					<span class="card-value">{formatCurrency(payrollRun.totalGross)}</span>
				</div>
				<div class="summary-card">
					<span class="card-label">TOTAL DEDUCTIONS</span>
					<span class="card-value deductions">-{formatCurrency(payrollRun.totalDeductions)}</span>
				</div>
				<div class="summary-card highlight">
					<span class="card-label">NET PAY</span>
					<span class="card-value">{formatCurrency(payrollRun.totalNetPay)}</span>
				</div>
				<div class="summary-card">
					<span class="card-label">EMPLOYEES</span>
					<span class="card-value">{payrollRun.totalEmployees}</span>
				</div>
			</div>
		</section>

		<!-- Employer Costs -->
		<section class="employer-section">
			<h3 class="section-title">Employer Costs</h3>
			<div class="employer-grid">
				<div class="employer-item">
					<span class="item-label">CPP</span>
					<span class="item-value">{formatCurrency(payrollRun.totalCppEmployer)}</span>
				</div>
				<div class="employer-item">
					<span class="item-label">EI</span>
					<span class="item-value">{formatCurrency(payrollRun.totalEiEmployer)}</span>
				</div>
				<div class="employer-item total">
					<span class="item-label">Total</span>
					<span class="item-value">{formatCurrency(payrollRun.totalEmployerCost)}</span>
				</div>
			</div>
		</section>

		<!-- Employee Breakdown -->
		<section class="employees-section">
			<h3 class="section-title">Employees</h3>
			<div class="employee-table-container">
				<table class="employee-table">
					<thead>
						<tr>
							<th>Name</th>
							<th class="amount">Gross</th>
							<th class="amount">Net</th>
						</tr>
					</thead>
					<tbody>
						{#each payrollRecords as record (record.id)}
							<tr>
								<td class="name">{record.employeeName}</td>
								<td class="amount">{formatCurrency(record.totalGross)}</td>
								<td class="amount net">{formatCurrency(record.netPay)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</section>

		<!-- Actions -->
		<div class="panel-actions">
			<button class="btn-secondary">
				<i class="fas fa-download"></i>
				Download Paystubs
			</button>
			{#if payrollRun.status === 'approved' || payrollRun.status === 'paid'}
				<button class="btn-secondary">
					<i class="fas fa-envelope"></i>
					Resend All
				</button>
			{/if}
		</div>
	</div>
</aside>

<style>
	.detail-panel {
		width: 400px;
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-2);
		overflow: hidden;
		position: sticky;
		top: var(--spacing-4);
		max-height: calc(100vh - var(--spacing-8));
		display: flex;
		flex-direction: column;
	}

	.panel-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		padding: var(--spacing-4) var(--spacing-5);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.header-info {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.header-info h2 {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0;
	}

	.close-btn {
		padding: var(--spacing-2);
		border: none;
		background: transparent;
		color: var(--color-surface-400);
		cursor: pointer;
		border-radius: var(--radius-md);
		transition: var(--transition-fast);
	}

	.close-btn:hover {
		background: var(--color-surface-100);
		color: var(--color-surface-700);
	}

	/* Status Badge */
	.status-badge {
		display: inline-block;
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

	.panel-content {
		flex: 1;
		overflow-y: auto;
		padding: var(--spacing-4) var(--spacing-5);
	}

	/* Pay Date Row */
	.pay-date-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding-bottom: var(--spacing-4);
		margin-bottom: var(--spacing-4);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.pay-date-row .label {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
	}

	.pay-date-row .value {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	/* Summary Section */
	.summary-section {
		margin-bottom: var(--spacing-5);
	}

	.summary-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--spacing-3);
	}

	.summary-card {
		padding: var(--spacing-4);
		background: var(--color-surface-50);
		border-radius: var(--radius-lg);
		border: 1px solid var(--color-surface-100);
	}

	.summary-card.highlight {
		background: var(--color-primary-500);
		border-color: var(--color-primary-500);
	}

	.summary-card.highlight .card-label,
	.summary-card.highlight .card-value {
		color: white;
	}

	.card-label {
		display: block;
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-500);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		margin-bottom: var(--spacing-1);
	}

	.card-value {
		display: block;
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.card-value.deductions {
		color: var(--color-error-600);
	}

	/* Section Title */
	.section-title {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-500);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		margin: 0 0 var(--spacing-3);
	}

	/* Employer Section */
	.employer-section {
		margin-bottom: var(--spacing-5);
		padding-bottom: var(--spacing-5);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.employer-grid {
		display: flex;
		gap: var(--spacing-4);
		align-items: center;
	}

	.employer-item {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.employer-item.total {
		margin-left: auto;
		padding: var(--spacing-2) var(--spacing-4);
		background: var(--color-surface-800);
		border-radius: var(--radius-lg);
	}

	.employer-item.total .item-label,
	.employer-item.total .item-value {
		color: white;
	}

	.item-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.item-value {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	/* Employees Section */
	.employees-section {
		margin-bottom: var(--spacing-5);
	}

	.employee-table-container {
		max-height: 200px;
		overflow-y: auto;
		border: 1px solid var(--color-surface-100);
		border-radius: var(--radius-lg);
	}

	.employee-table {
		width: 100%;
		border-collapse: collapse;
	}

	.employee-table th {
		position: sticky;
		top: 0;
		text-align: left;
		padding: var(--spacing-2) var(--spacing-3);
		background: var(--color-surface-50);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-600);
		border-bottom: 1px solid var(--color-surface-200);
	}

	.employee-table th.amount {
		text-align: right;
	}

	.employee-table td {
		padding: var(--spacing-2) var(--spacing-3);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
		border-bottom: 1px solid var(--color-surface-50);
	}

	.employee-table tr:last-child td {
		border-bottom: none;
	}

	.employee-table td.name {
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.employee-table td.amount {
		text-align: right;
		font-family: monospace;
	}

	.employee-table td.amount.net {
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	/* Panel Actions */
	.panel-actions {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-3);
		padding-top: var(--spacing-4);
		border-top: 1px solid var(--color-surface-100);
	}

	.btn-secondary {
		display: flex;
		align-items: center;
		justify-content: center;
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

	/* Responsive */
	@media (max-width: 1024px) {
		.detail-panel {
			width: 100%;
			position: fixed;
			right: 0;
			top: 0;
			height: 100vh;
			max-height: 100vh;
			border-radius: 0;
			z-index: 100;
		}
	}
</style>

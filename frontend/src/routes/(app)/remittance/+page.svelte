<script lang="ts">
	// Remittance page - Phase 0 static UI prototype
	import { REMITTER_TYPE_INFO } from '$lib/types/company';
	import type { RemitterType } from '$lib/types/company';
	import {
		REMITTANCE_STATUS_INFO,
		PAYMENT_METHOD_INFO,
		determineRemittanceStatus,
		formatPeriodLabel,
		calculatePenaltyRate,
		calculatePenaltyAmount
	} from '$lib/types/remittance';
	import type { RemittancePeriod, RemittanceStatus, PaymentMethod } from '$lib/types/remittance';
	import MarkAsPaidModal from '$lib/components/remittance/MarkAsPaidModal.svelte';

	// Mock data
	let selectedYear = $state(2025);
	let remitterType: RemitterType = 'regular';

	// Mock remittance data
	const mockRemittances: RemittancePeriod[] = [
		{
			id: '1',
			ledgerId: 'ledger_1',
			remitterType: 'regular',
			periodStart: '2025-12-01',
			periodEnd: '2025-12-31',
			periodLabel: 'December 2025',
			dueDate: '2026-01-15',
			cppEmployee: 1500,
			cppEmployer: 1500,
			eiEmployee: 400,
			eiEmployer: 560,
			federalTax: 3000,
			provincialTax: 1200,
			totalAmount: 8160,
			status: 'pending',
			paidDate: null,
			paymentMethod: null,
			confirmationNumber: null,
			notes: null,
			daysOverdue: 0,
			penaltyRate: 0,
			penaltyAmount: 0,
			payrollRunIds: ['run_1', 'run_2'],
			createdAt: '2025-12-01T00:00:00Z',
			updatedAt: '2025-12-01T00:00:00Z'
		},
		{
			id: '2',
			ledgerId: 'ledger_1',
			remitterType: 'regular',
			periodStart: '2025-11-01',
			periodEnd: '2025-11-30',
			periodLabel: 'November 2025',
			dueDate: '2025-12-15',
			cppEmployee: 1450,
			cppEmployer: 1450,
			eiEmployee: 390,
			eiEmployer: 546,
			federalTax: 2900,
			provincialTax: 1154,
			totalAmount: 7890,
			status: 'paid',
			paidDate: '2025-12-14',
			paymentMethod: 'my_payment',
			confirmationNumber: 'PAY-2025-12-001234',
			notes: null,
			daysOverdue: 0,
			penaltyRate: 0,
			penaltyAmount: 0,
			payrollRunIds: ['run_3', 'run_4'],
			createdAt: '2025-11-01T00:00:00Z',
			updatedAt: '2025-12-14T00:00:00Z'
		},
		{
			id: '3',
			ledgerId: 'ledger_1',
			remitterType: 'regular',
			periodStart: '2025-10-01',
			periodEnd: '2025-10-31',
			periodLabel: 'October 2025',
			dueDate: '2025-11-15',
			cppEmployee: 1400,
			cppEmployer: 1400,
			eiEmployee: 380,
			eiEmployer: 532,
			federalTax: 2800,
			provincialTax: 1138,
			totalAmount: 7650,
			status: 'paid',
			paidDate: '2025-11-12',
			paymentMethod: 'online_banking',
			confirmationNumber: null,
			notes: null,
			daysOverdue: 0,
			penaltyRate: 0,
			penaltyAmount: 0,
			payrollRunIds: ['run_5', 'run_6'],
			createdAt: '2025-10-01T00:00:00Z',
			updatedAt: '2025-11-12T00:00:00Z'
		},
		{
			id: '4',
			ledgerId: 'ledger_1',
			remitterType: 'regular',
			periodStart: '2025-09-01',
			periodEnd: '2025-09-30',
			periodLabel: 'September 2025',
			dueDate: '2025-10-15',
			cppEmployee: 1350,
			cppEmployer: 1350,
			eiEmployee: 370,
			eiEmployer: 518,
			federalTax: 2700,
			provincialTax: 1112,
			totalAmount: 7400,
			status: 'paid',
			paidDate: '2025-10-14',
			paymentMethod: 'my_payment',
			confirmationNumber: 'PAY-2025-10-000987',
			notes: null,
			daysOverdue: 0,
			penaltyRate: 0,
			penaltyAmount: 0,
			payrollRunIds: ['run_7', 'run_8'],
			createdAt: '2025-09-01T00:00:00Z',
			updatedAt: '2025-10-14T00:00:00Z'
		}
	];

	// Get upcoming remittance (first pending)
	let upcomingRemittance = $derived(mockRemittances.find((r) => r.status === 'pending') || null);

	// Calculate summary stats
	let summary = $derived(() => {
		const paidRemittances = mockRemittances.filter((r) => r.status === 'paid' || r.status === 'paid_late');
		const pendingRemittances = mockRemittances.filter((r) => r.status === 'pending' || r.status === 'due_soon' || r.status === 'overdue');

		return {
			ytdRemitted: paidRemittances.reduce((sum, r) => sum + r.totalAmount, 0),
			completedCount: paidRemittances.length,
			totalCount: 12, // For regular monthly
			onTimeRate: 1.0, // 100% on time
			pendingAmount: pendingRemittances.reduce((sum, r) => sum + r.totalAmount, 0),
			pendingCount: pendingRemittances.length
		};
	});

	// Days until due date
	function getDaysUntilDue(dueDate: string): number {
		const due = new Date(dueDate);
		const today = new Date();
		today.setHours(0, 0, 0, 0);
		due.setHours(0, 0, 0, 0);
		return Math.ceil((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
	}

	// Format currency
	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			minimumFractionDigits: 2
		}).format(amount);
	}

	// Format date
	function formatDate(dateStr: string): string {
		return new Date(dateStr).toLocaleDateString('en-CA', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	// Modal state
	let showMarkAsPaidModal = $state(false);
	let selectedRemittance = $state<RemittancePeriod | null>(null);

	function openMarkAsPaidModal(remittance: RemittancePeriod) {
		selectedRemittance = remittance;
		showMarkAsPaidModal = true;
	}

	function closeModal() {
		showMarkAsPaidModal = false;
		selectedRemittance = null;
	}

	function handleMarkAsPaid(data: {
		paymentDate: string;
		paymentMethod: PaymentMethod;
		confirmationNumber: string;
	}) {
		// TODO: API call to mark as paid
		console.log('Mark as paid:', selectedRemittance?.id, data);
		closeModal();
	}

	// Expanded row state
	let expandedRowId = $state<string | null>(null);

	function toggleRowExpansion(id: string) {
		expandedRowId = expandedRowId === id ? null : id;
	}
</script>

<svelte:head>
	<title>Remittance - BeanFlow Payroll</title>
</svelte:head>

<div class="remittance-page">
	<header class="page-header">
		<div class="header-left">
			<h1 class="page-title">CRA Remittance</h1>
			<p class="page-subtitle">Track and manage your payroll deduction remittances</p>
		</div>
		<div class="header-right">
			<div class="year-selector">
				<button class="year-btn" onclick={() => (selectedYear = selectedYear - 1)}>
					<i class="fas fa-chevron-left"></i>
				</button>
				<span class="year-label">{selectedYear}</span>
				<button class="year-btn" onclick={() => (selectedYear = selectedYear + 1)}>
					<i class="fas fa-chevron-right"></i>
				</button>
			</div>
		</div>
	</header>

	<!-- Remitter Type Badge -->
	<div class="remitter-badge">
		<i class="fas fa-landmark"></i>
		<span>{REMITTER_TYPE_INFO[remitterType].label}</span>
		<span class="badge-separator">|</span>
		<span class="badge-detail">Due 15th of following month</span>
	</div>

	<!-- Upcoming Remittance Card -->
	{#if upcomingRemittance}
		{@const daysUntil = getDaysUntilDue(upcomingRemittance.dueDate)}
		{@const isOverdue = daysUntil < 0}
		{@const isDueSoon = daysUntil >= 0 && daysUntil <= 7}

		<div
			class="upcoming-card"
			class:overdue={isOverdue}
			class:due-soon={isDueSoon && !isOverdue}
		>
			<div class="upcoming-header">
				{#if isOverdue}
					<i class="fas fa-exclamation-circle"></i>
					<span>REMITTANCE OVERDUE</span>
				{:else if isDueSoon}
					<i class="fas fa-exclamation-triangle"></i>
					<span>REMITTANCE DUE SOON</span>
				{:else}
					<i class="fas fa-clock"></i>
					<span>NEXT REMITTANCE DUE</span>
				{/if}
			</div>

			<div class="upcoming-content">
				<div class="upcoming-period">
					<span class="period-label">Period:</span>
					<span class="period-value">{upcomingRemittance.periodLabel}</span>
				</div>
				<div class="upcoming-due">
					<span class="due-label">Due Date:</span>
					<span class="due-value">{formatDate(upcomingRemittance.dueDate)}</span>
				</div>

				<div class="upcoming-amount">
					<span class="amount-value">{formatCurrency(upcomingRemittance.totalAmount)}</span>
					<span class="amount-label">Total Amount Due</span>
				</div>

				<div class="breakdown-grid">
					<div class="breakdown-item">
						<span class="breakdown-label">CPP</span>
						<span class="breakdown-value"
							>{formatCurrency(upcomingRemittance.cppEmployee + upcomingRemittance.cppEmployer)}</span
						>
						<span class="breakdown-detail">Emp + Empr</span>
					</div>
					<div class="breakdown-item">
						<span class="breakdown-label">EI</span>
						<span class="breakdown-value"
							>{formatCurrency(upcomingRemittance.eiEmployee + upcomingRemittance.eiEmployer)}</span
						>
						<span class="breakdown-detail">Emp + Empr</span>
					</div>
					<div class="breakdown-item">
						<span class="breakdown-label">Income Tax</span>
						<span class="breakdown-value"
							>{formatCurrency(upcomingRemittance.federalTax + upcomingRemittance.provincialTax)}</span
						>
						<span class="breakdown-detail">Fed + Prov</span>
					</div>
				</div>

				<div class="upcoming-countdown" class:warning={isDueSoon} class:danger={isOverdue}>
					{#if isOverdue}
						<i class="fas fa-exclamation-circle"></i>
						<span>{Math.abs(daysUntil)} days overdue - Pay immediately to avoid additional penalties</span>
					{:else}
						<i class="fas fa-clock"></i>
						<span>{daysUntil} days until due</span>
					{/if}
				</div>

				<div class="upcoming-actions">
					<button class="btn-secondary">
						<i class="fas fa-file-pdf"></i>
						<span>Generate PD7A</span>
					</button>
					<button class="btn-primary" onclick={() => openMarkAsPaidModal(upcomingRemittance)}>
						<i class="fas fa-check"></i>
						<span>Mark as Paid</span>
					</button>
				</div>
			</div>
		</div>
	{/if}

	<!-- Summary Cards -->
	<div class="summary-cards">
		<div class="summary-card">
			<span class="summary-label">YTD Remitted</span>
			<span class="summary-value">{formatCurrency(summary().ytdRemitted)}</span>
			<span class="summary-detail">Total paid this year</span>
		</div>
		<div class="summary-card">
			<span class="summary-label">Remittances</span>
			<span class="summary-value">{summary().completedCount} of {summary().totalCount}</span>
			<span class="summary-detail">Completed this year</span>
		</div>
		<div class="summary-card">
			<span class="summary-label">On-Time Rate</span>
			<span class="summary-value success">{(summary().onTimeRate * 100).toFixed(0)}%</span>
			<span class="summary-detail">No late payments</span>
		</div>
		<div class="summary-card">
			<span class="summary-label">Pending</span>
			<span class="summary-value">{formatCurrency(summary().pendingAmount)}</span>
			<span class="summary-detail">{summary().pendingCount} pending remittance(s)</span>
		</div>
	</div>

	<!-- Remittance History Table -->
	<div class="history-section">
		<div class="history-header">
			<h2 class="history-title">Remittance History</h2>
			<button class="btn-text">
				<i class="fas fa-download"></i>
				<span>Export</span>
			</button>
		</div>

		<div class="history-table-wrapper">
			<table class="history-table">
				<thead>
					<tr>
						<th>Period</th>
						<th>Due Date</th>
						<th class="text-right">Amount</th>
						<th>Paid</th>
						<th>Status</th>
						<th class="text-center">Actions</th>
					</tr>
				</thead>
				<tbody>
					{#each mockRemittances as remittance (remittance.id)}
						{@const statusInfo = REMITTANCE_STATUS_INFO[remittance.status]}
						<tr
							class="history-row"
							class:expanded={expandedRowId === remittance.id}
							onclick={() => toggleRowExpansion(remittance.id)}
						>
							<td class="period-cell">
								<i class="fas fa-chevron-right expand-icon" class:rotated={expandedRowId === remittance.id}></i>
								{remittance.periodLabel}
							</td>
							<td>{formatDate(remittance.dueDate)}</td>
							<td class="text-right amount-cell">{formatCurrency(remittance.totalAmount)}</td>
							<td>{remittance.paidDate ? formatDate(remittance.paidDate) : '-'}</td>
							<td>
								<span class="status-badge {statusInfo.colorClass}">
									<i class="fas fa-{statusInfo.icon}"></i>
									{statusInfo.label}
								</span>
							</td>
							<td class="text-center">
								<button class="action-btn" onclick={(e) => { e.stopPropagation(); }}>
									<i class="fas fa-ellipsis-v"></i>
								</button>
							</td>
						</tr>

						{#if expandedRowId === remittance.id}
							<tr class="expanded-row">
								<td colspan="6">
									<div class="expanded-content">
										<div class="expanded-section">
											<h4 class="expanded-title">Period Details</h4>
											<div class="detail-grid">
												<div class="detail-item">
													<span class="detail-label">Period</span>
													<span class="detail-value"
														>{formatDate(remittance.periodStart)} - {formatDate(
															remittance.periodEnd
														)}</span
													>
												</div>
												<div class="detail-item">
													<span class="detail-label">Due Date</span>
													<span class="detail-value">{formatDate(remittance.dueDate)}</span>
												</div>
												<div class="detail-item">
													<span class="detail-label">Payroll Runs</span>
													<span class="detail-value"
														>{remittance.payrollRunIds.length} runs included</span
													>
												</div>
											</div>
										</div>

										<div class="expanded-section">
											<h4 class="expanded-title">Deduction Breakdown</h4>
											<table class="breakdown-table">
												<thead>
													<tr>
														<th>Category</th>
														<th class="text-right">Employee</th>
														<th class="text-right">Employer</th>
													</tr>
												</thead>
												<tbody>
													<tr>
														<td>CPP Contributions</td>
														<td class="text-right">{formatCurrency(remittance.cppEmployee)}</td>
														<td class="text-right">{formatCurrency(remittance.cppEmployer)}</td>
													</tr>
													<tr>
														<td>EI Premiums</td>
														<td class="text-right">{formatCurrency(remittance.eiEmployee)}</td>
														<td class="text-right">{formatCurrency(remittance.eiEmployer)}</td>
													</tr>
													<tr>
														<td>Federal Income Tax</td>
														<td class="text-right">{formatCurrency(remittance.federalTax)}</td>
														<td class="text-right">-</td>
													</tr>
													<tr>
														<td>Provincial Income Tax</td>
														<td class="text-right">{formatCurrency(remittance.provincialTax)}</td>
														<td class="text-right">-</td>
													</tr>
													<tr class="total-row">
														<td>TOTAL</td>
														<td class="text-right"
															>{formatCurrency(
																remittance.cppEmployee +
																	remittance.eiEmployee +
																	remittance.federalTax +
																	remittance.provincialTax
															)}</td
														>
														<td class="text-right"
															>{formatCurrency(remittance.cppEmployer + remittance.eiEmployer)}</td
														>
													</tr>
												</tbody>
											</table>
										</div>

										{#if remittance.paidDate}
											<div class="expanded-section">
												<h4 class="expanded-title">Payment Information</h4>
												<div class="detail-grid">
													<div class="detail-item">
														<span class="detail-label">Status</span>
														<span class="detail-value status-paid">
															<i class="fas fa-check-circle"></i> Paid
														</span>
													</div>
													<div class="detail-item">
														<span class="detail-label">Payment Date</span>
														<span class="detail-value">{formatDate(remittance.paidDate)}</span>
													</div>
													<div class="detail-item">
														<span class="detail-label">Payment Method</span>
														<span class="detail-value"
															>{remittance.paymentMethod
																? PAYMENT_METHOD_INFO[remittance.paymentMethod].label
																: '-'}</span
														>
													</div>
													{#if remittance.confirmationNumber}
														<div class="detail-item">
															<span class="detail-label">Confirmation #</span>
															<span class="detail-value">{remittance.confirmationNumber}</span>
														</div>
													{/if}
												</div>
											</div>
										{/if}
									</div>
								</td>
							</tr>
						{/if}
					{/each}
				</tbody>
			</table>
		</div>
	</div>
</div>

<!-- Mark as Paid Modal -->
{#if showMarkAsPaidModal && selectedRemittance}
	<MarkAsPaidModal
		remittance={selectedRemittance}
		onClose={closeModal}
		onSubmit={handleMarkAsPaid}
	/>
{/if}

<style>
	.remittance-page {
		max-width: 1000px;
	}

	/* Header */
	.page-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
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

	.year-selector {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		background: white;
		border-radius: var(--radius-lg);
		padding: var(--spacing-2);
		box-shadow: var(--shadow-md3-1);
	}

	.year-btn {
		width: 32px;
		height: 32px;
		border: none;
		background: none;
		color: var(--color-surface-600);
		cursor: pointer;
		border-radius: var(--radius-md);
		transition: var(--transition-fast);
	}

	.year-btn:hover {
		background: var(--color-surface-100);
		color: var(--color-surface-800);
	}

	.year-label {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		min-width: 60px;
		text-align: center;
	}

	/* Remitter Badge */
	.remitter-badge {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		background: var(--color-secondary-100);
		color: var(--color-secondary-700);
		border-radius: var(--radius-full);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		margin-bottom: var(--spacing-6);
	}

	.badge-separator {
		color: var(--color-secondary-300);
	}

	.badge-detail {
		color: var(--color-secondary-600);
	}

	/* Upcoming Card */
	.upcoming-card {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-2);
		padding: var(--spacing-6);
		margin-bottom: var(--spacing-6);
		border-left: 4px solid var(--color-primary-500);
	}

	.upcoming-card.due-soon {
		border-left-color: var(--color-warning-500);
	}

	.upcoming-card.overdue {
		border-left-color: var(--color-error-500);
		background: var(--color-error-50);
	}

	.upcoming-header {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-semibold);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--color-primary-600);
		margin-bottom: var(--spacing-4);
	}

	.upcoming-card.due-soon .upcoming-header {
		color: var(--color-warning-600);
	}

	.upcoming-card.overdue .upcoming-header {
		color: var(--color-error-600);
	}

	.upcoming-content {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
	}

	.upcoming-period,
	.upcoming-due {
		display: flex;
		gap: var(--spacing-2);
		font-size: var(--font-size-body-content);
	}

	.period-label,
	.due-label {
		color: var(--color-surface-500);
	}

	.period-value,
	.due-value {
		color: var(--color-surface-800);
		font-weight: var(--font-weight-medium);
	}

	.upcoming-amount {
		text-align: center;
		padding: var(--spacing-6) 0;
		background: var(--color-surface-50);
		border-radius: var(--radius-lg);
	}

	.upcoming-card.overdue .upcoming-amount {
		background: var(--color-error-100);
	}

	.amount-value {
		display: block;
		font-size: var(--font-size-headline-minimum);
		font-weight: var(--font-weight-bold);
		color: var(--color-surface-900);
	}

	.amount-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	.breakdown-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: var(--spacing-4);
	}

	.breakdown-item {
		text-align: center;
		padding: var(--spacing-3);
		background: var(--color-surface-50);
		border-radius: var(--radius-md);
	}

	.breakdown-label {
		display: block;
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
		margin-bottom: var(--spacing-1);
	}

	.breakdown-value {
		display: block;
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.breakdown-detail {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.upcoming-countdown {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-2);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
	}

	.upcoming-countdown.warning {
		color: var(--color-warning-600);
	}

	.upcoming-countdown.danger {
		color: var(--color-error-600);
	}

	.upcoming-actions {
		display: flex;
		justify-content: center;
		gap: var(--spacing-3);
		padding-top: var(--spacing-4);
		border-top: 1px solid var(--color-surface-100);
	}

	/* Summary Cards */
	.summary-cards {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: var(--spacing-4);
		margin-bottom: var(--spacing-6);
	}

	.summary-card {
		background: white;
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-md3-1);
		padding: var(--spacing-4);
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.summary-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.summary-value {
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.summary-value.success {
		color: var(--color-success-600);
	}

	.summary-detail {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	/* History Section */
	.history-section {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		overflow: hidden;
	}

	.history-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-4) var(--spacing-6);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.history-title {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0;
	}

	.btn-text {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-3);
		background: none;
		border: none;
		color: var(--color-primary-600);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		border-radius: var(--radius-md);
		transition: var(--transition-fast);
	}

	.btn-text:hover {
		background: var(--color-primary-50);
	}

	.history-table-wrapper {
		overflow-x: auto;
	}

	.history-table {
		width: 100%;
		border-collapse: collapse;
	}

	.history-table th,
	.history-table td {
		padding: var(--spacing-3) var(--spacing-4);
		text-align: left;
		font-size: var(--font-size-body-content);
	}

	.history-table th {
		background: var(--color-surface-50);
		color: var(--color-surface-600);
		font-weight: var(--font-weight-medium);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.history-table td {
		border-bottom: 1px solid var(--color-surface-100);
		color: var(--color-surface-800);
	}

	.history-row {
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.history-row:hover {
		background: var(--color-surface-50);
	}

	.history-row.expanded {
		background: var(--color-primary-50);
	}

	.period-cell {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
	}

	.expand-icon {
		font-size: 12px;
		color: var(--color-surface-400);
		transition: var(--transition-fast);
	}

	.expand-icon.rotated {
		transform: rotate(90deg);
	}

	.text-right {
		text-align: right;
	}

	.text-center {
		text-align: center;
	}

	.amount-cell {
		font-weight: var(--font-weight-medium);
	}

	.status-badge {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-1);
		padding: var(--spacing-1) var(--spacing-2);
		border-radius: var(--radius-full);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
	}

	.action-btn {
		width: 32px;
		height: 32px;
		border: none;
		background: none;
		color: var(--color-surface-500);
		cursor: pointer;
		border-radius: var(--radius-md);
		transition: var(--transition-fast);
	}

	.action-btn:hover {
		background: var(--color-surface-100);
		color: var(--color-surface-700);
	}

	/* Expanded Row */
	.expanded-row td {
		padding: 0;
		background: var(--color-surface-50);
	}

	.expanded-content {
		padding: var(--spacing-6);
		display: flex;
		flex-direction: column;
		gap: var(--spacing-6);
	}

	.expanded-section {
		background: white;
		border-radius: var(--radius-lg);
		padding: var(--spacing-4);
	}

	.expanded-title {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-3);
	}

	.detail-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: var(--spacing-4);
	}

	.detail-item {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.detail-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.detail-value {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-800);
	}

	.detail-value.status-paid {
		color: var(--color-success-600);
	}

	.breakdown-table {
		width: 100%;
		border-collapse: collapse;
	}

	.breakdown-table th,
	.breakdown-table td {
		padding: var(--spacing-2) var(--spacing-3);
		font-size: var(--font-size-body-content);
	}

	.breakdown-table th {
		background: var(--color-surface-50);
		color: var(--color-surface-600);
		font-weight: var(--font-weight-medium);
	}

	.breakdown-table td {
		border-bottom: 1px solid var(--color-surface-100);
	}

	.breakdown-table .total-row {
		font-weight: var(--font-weight-semibold);
		background: var(--color-surface-50);
	}

	/* Buttons */
	.btn-primary,
	.btn-secondary {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-5);
		border: none;
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-primary {
		background: var(--gradient-primary);
		color: white;
		box-shadow: var(--shadow-md3-1);
	}

	.btn-primary:hover {
		opacity: 0.9;
		transform: translateY(-1px);
	}

	.btn-secondary {
		background: white;
		color: var(--color-surface-700);
		border: 1px solid var(--color-surface-200);
	}

	.btn-secondary:hover {
		background: var(--color-surface-50);
		border-color: var(--color-surface-300);
	}

	/* Responsive */
	@media (max-width: 768px) {
		.page-header {
			flex-direction: column;
			gap: var(--spacing-4);
		}

		.summary-cards {
			grid-template-columns: repeat(2, 1fr);
		}

		.breakdown-grid {
			grid-template-columns: 1fr;
		}

		.upcoming-actions {
			flex-direction: column;
		}
	}

	@media (max-width: 640px) {
		.summary-cards {
			grid-template-columns: 1fr;
		}
	}
</style>

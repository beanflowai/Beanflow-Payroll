<script lang="ts">
	import type {
		PayrollRunWithGroups,
		PayrollRunPayGroup,
		EmployeePayrollInput
	} from '$lib/types/payroll';
	import { DraftPayGroupSection } from '$lib/components/payroll';

	interface Props {
		payrollRun: PayrollRunWithGroups;
		hasModifiedRecords: boolean;
		isRecalculating: boolean;
		isFinalizing: boolean;
		onRecalculate: () => void;
		onFinalize: () => void;
		onUpdateRecord: (recordId: string, employeeId: string, updates: Partial<EmployeePayrollInput>) => void;
	}

	let {
		payrollRun,
		hasModifiedRecords,
		isRecalculating,
		isFinalizing,
		onRecalculate,
		onFinalize,
		onUpdateRecord
	}: Props = $props();

	let expandedRecordId = $state<string | null>(null);

	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD'
		}).format(amount);
	}

	function formatDate(dateStr: string): string {
		return new Date(dateStr).toLocaleDateString('en-CA', {
			weekday: 'short',
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		});
	}

	function handleToggleExpand(id: string) {
		expandedRecordId = expandedRecordId === id ? null : id;
	}

	// Calculate totals for summary cards
	const totalDeductions = $derived(
		payrollRun.totalCppEmployee +
			payrollRun.totalEiEmployee +
			payrollRun.totalFederalTax +
			payrollRun.totalProvincialTax
	);
</script>

<div class="draft-payroll-view">
	<!-- Header with Status Banner -->
	<div class="page-header">
		<div class="header-content">
			<div class="header-left">
				<div class="status-badge draft">
					<i class="fas fa-edit"></i>
					Draft
				</div>
				<h1 class="page-title">Pay Date: {formatDate(payrollRun.payDate)}</h1>
			</div>
			<div class="header-actions">
				<button
					class="btn btn-secondary"
					onclick={onRecalculate}
					disabled={isRecalculating || !hasModifiedRecords}
				>
					{#if isRecalculating}
						<i class="fas fa-spinner fa-spin"></i>
						Recalculating...
					{:else}
						<i class="fas fa-calculator"></i>
						Recalculate
					{/if}
				</button>
				<button
					class="btn btn-primary"
					onclick={onFinalize}
					disabled={isFinalizing || hasModifiedRecords}
					title={hasModifiedRecords ? 'Recalculate first to save changes' : 'Finalize payroll run'}
				>
					{#if isFinalizing}
						<i class="fas fa-spinner fa-spin"></i>
						Finalizing...
					{:else}
						<i class="fas fa-check-circle"></i>
						Finalize
					{/if}
				</button>
			</div>
		</div>

		<!-- Warning Banner (when modified) -->
		{#if hasModifiedRecords}
			<div class="warning-banner">
				<i class="fas fa-exclamation-triangle"></i>
				<span>
					<strong>Unsaved Changes:</strong> You have modified employee data. Click
					<strong>Recalculate</strong> to update CPP, EI, and tax calculations.
				</span>
			</div>
		{/if}
	</div>

	<!-- Summary Cards -->
	<div class="summary-cards">
		<div class="summary-card">
			<div class="card-icon employees">
				<i class="fas fa-users"></i>
			</div>
			<div class="card-content">
				<span class="card-value">{payrollRun.totalEmployees}</span>
				<span class="card-label">Employees</span>
			</div>
		</div>
		<div class="summary-card">
			<div class="card-icon gross">
				<i class="fas fa-dollar-sign"></i>
			</div>
			<div class="card-content">
				<span class="card-value">{formatCurrency(payrollRun.totalGross)}</span>
				<span class="card-label">Total Gross</span>
			</div>
		</div>
		<div class="summary-card">
			<div class="card-icon deductions">
				<i class="fas fa-minus-circle"></i>
			</div>
			<div class="card-content">
				<span class="card-value">{formatCurrency(totalDeductions)}</span>
				<span class="card-label">Total Deductions</span>
			</div>
		</div>
		<div class="summary-card highlight">
			<div class="card-icon net">
				<i class="fas fa-wallet"></i>
			</div>
			<div class="card-content">
				<span class="card-value">{formatCurrency(payrollRun.totalNetPay)}</span>
				<span class="card-label">Total Net Pay</span>
			</div>
		</div>
	</div>

	<!-- Deduction Breakdown -->
	<div class="deduction-breakdown">
		<h3 class="breakdown-title">Deduction Breakdown</h3>
		<div class="breakdown-grid">
			<div class="breakdown-item">
				<span class="breakdown-label">CPP (Employee)</span>
				<span class="breakdown-value">{formatCurrency(payrollRun.totalCppEmployee)}</span>
			</div>
			<div class="breakdown-item">
				<span class="breakdown-label">CPP (Employer)</span>
				<span class="breakdown-value employer">{formatCurrency(payrollRun.totalCppEmployer)}</span>
			</div>
			<div class="breakdown-item">
				<span class="breakdown-label">EI (Employee)</span>
				<span class="breakdown-value">{formatCurrency(payrollRun.totalEiEmployee)}</span>
			</div>
			<div class="breakdown-item">
				<span class="breakdown-label">EI (Employer)</span>
				<span class="breakdown-value employer">{formatCurrency(payrollRun.totalEiEmployer)}</span>
			</div>
			<div class="breakdown-item">
				<span class="breakdown-label">Federal Tax</span>
				<span class="breakdown-value">{formatCurrency(payrollRun.totalFederalTax)}</span>
			</div>
			<div class="breakdown-item">
				<span class="breakdown-label">Provincial Tax</span>
				<span class="breakdown-value">{formatCurrency(payrollRun.totalProvincialTax)}</span>
			</div>
		</div>
		<div class="employer-cost">
			<span class="employer-label">Total Employer Cost</span>
			<span class="employer-value">{formatCurrency(payrollRun.totalEmployerCost)}</span>
		</div>
	</div>

	<!-- Pay Group Sections -->
	<div class="pay-groups">
		{#each payrollRun.payGroups as payGroup (payGroup.payGroupId)}
			<DraftPayGroupSection
				{payGroup}
				{expandedRecordId}
				onToggleExpand={handleToggleExpand}
				{onUpdateRecord}
			/>
		{/each}
	</div>
</div>

<style>
	.draft-payroll-view {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-5);
	}

	/* Header */
	.page-header {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-3);
	}

	.header-content {
		display: flex;
		justify-content: space-between;
		align-items: center;
		flex-wrap: wrap;
		gap: var(--spacing-3);
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
	}

	.status-badge {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-3);
		border-radius: var(--radius-full);
		font-size: var(--font-size-body-small);
		font-weight: var(--font-weight-semibold);
	}

	.status-badge.draft {
		background: var(--color-warning-100);
		color: var(--color-warning-700);
	}

	.page-title {
		font-size: var(--font-size-headline);
		font-weight: var(--font-weight-bold);
		color: var(--color-surface-800);
		margin: 0;
	}

	.header-actions {
		display: flex;
		gap: var(--spacing-3);
	}

	.btn {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-secondary {
		background: white;
		border: 1px solid var(--color-surface-300);
		color: var(--color-surface-700);
	}

	.btn-secondary:hover:not(:disabled) {
		background: var(--color-surface-50);
		border-color: var(--color-surface-400);
	}

	.btn-primary {
		background: linear-gradient(135deg, var(--color-primary-600), var(--color-secondary-600));
		border: none;
		color: white;
	}

	.btn-primary:hover:not(:disabled) {
		opacity: 0.9;
		transform: translateY(-1px);
	}

	/* Warning Banner */
	.warning-banner {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-warning-50);
		border: 1px solid var(--color-warning-300);
		border-radius: var(--radius-md);
		color: var(--color-warning-800);
		font-size: var(--font-size-body-content);
	}

	.warning-banner i {
		color: var(--color-warning-600);
		font-size: 18px;
	}

	/* Summary Cards */
	.summary-cards {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: var(--spacing-4);
	}

	.summary-card {
		display: flex;
		align-items: center;
		gap: var(--spacing-4);
		padding: var(--spacing-4) var(--spacing-5);
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
	}

	.summary-card.highlight {
		background: linear-gradient(135deg, var(--color-success-50), var(--color-success-100));
		border: 1px solid var(--color-success-200);
	}

	.card-icon {
		width: 48px;
		height: 48px;
		border-radius: var(--radius-md);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 20px;
	}

	.card-icon.employees {
		background: var(--color-primary-100);
		color: var(--color-primary-600);
	}

	.card-icon.gross {
		background: var(--color-info-100);
		color: var(--color-info-600);
	}

	.card-icon.deductions {
		background: var(--color-warning-100);
		color: var(--color-warning-600);
	}

	.card-icon.net {
		background: var(--color-success-600);
		color: white;
	}

	.card-content {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.card-value {
		font-size: var(--font-size-title);
		font-weight: var(--font-weight-bold);
		color: var(--color-surface-800);
	}

	.card-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	/* Deduction Breakdown */
	.deduction-breakdown {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		padding: var(--spacing-4) var(--spacing-5);
	}

	.breakdown-title {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-700);
		margin: 0 0 var(--spacing-3) 0;
	}

	.breakdown-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: var(--spacing-3);
	}

	.breakdown-item {
		display: flex;
		justify-content: space-between;
		padding: var(--spacing-2) var(--spacing-3);
		background: var(--color-surface-50);
		border-radius: var(--radius-sm);
	}

	.breakdown-label {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
	}

	.breakdown-value {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.breakdown-value.employer {
		color: var(--color-info-600);
	}

	.employer-cost {
		display: flex;
		justify-content: flex-end;
		align-items: center;
		gap: var(--spacing-4);
		margin-top: var(--spacing-3);
		padding-top: var(--spacing-3);
		border-top: 1px solid var(--color-surface-200);
	}

	.employer-label {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-600);
	}

	.employer-value {
		font-size: var(--font-size-title);
		font-weight: var(--font-weight-bold);
		color: var(--color-info-600);
	}

	/* Pay Groups */
	.pay-groups {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
	}

	@media (max-width: 1024px) {
		.summary-cards {
			grid-template-columns: repeat(2, 1fr);
		}

		.breakdown-grid {
			grid-template-columns: repeat(2, 1fr);
		}
	}

	@media (max-width: 768px) {
		.header-content {
			flex-direction: column;
			align-items: flex-start;
		}

		.header-actions {
			width: 100%;
		}

		.btn {
			flex: 1;
			justify-content: center;
		}

		.summary-cards {
			grid-template-columns: 1fr;
		}

		.breakdown-grid {
			grid-template-columns: 1fr;
		}
	}
</style>

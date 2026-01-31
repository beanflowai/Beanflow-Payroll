<script lang="ts">
	import type { PayrollRecord, PayrollRunPayGroup } from '$lib/types/payroll';
	import { LEAVE_TYPE_LABELS, ADJUSTMENT_TYPE_LABELS } from '$lib/types/payroll';
	import { formatCurrency } from '$lib/utils/formatUtils';
	import { formatDateRange } from '$lib/utils/dateUtils';

	interface Props {
		record: PayrollRecord;
		payGroup?: PayrollRunPayGroup;
		payDate?: string;
	}

	let { record, payGroup, payDate }: Props = $props();

	// Derived: earnings adjustments from inputData (for Other Earnings breakdown)
	const earningsAdjustments = $derived(
		(record.inputData?.adjustments ?? [])
			.filter((adj) => adj.type !== 'deduction' && adj.amount > 0)
			.sort((a, b) => b.amount - a.amount)
	);

	const hasEarningsAdjustments = $derived(earningsAdjustments.length > 0);
	const otherEarningsTotal = $derived(
		earningsAdjustments.reduce((sum, adj) => sum + adj.amount, 0)
	);

	// Derived: check if tax breakdown exists (bonus tax calculated separately)
	const hasTaxBreakdown = $derived(
		(record.federalTaxOnBonus ?? 0) > 0 || (record.provincialTaxOnBonus ?? 0) > 0
	);

	// Format period string
	const periodString = $derived(
		payGroup ? formatDateRange(payGroup.periodStart, payGroup.periodEnd) : 'Current Period'
	);
</script>

<div class="paystub-preview">
	<!-- Header Section -->
	<div class="paystub-header">
		<div class="header-title">PAY STUB PREVIEW</div>
		<div class="header-subtitle">Draft - Subject to Change</div>
	</div>

	<!-- Employee Info Section -->
	<div class="info-section">
		<div class="info-row">
			<div class="info-item">
				<span class="info-label">Employee</span>
				<span class="info-value">{record.employeeName}</span>
			</div>
			<div class="info-item">
				<span class="info-label">Province</span>
				<span class="info-value">{record.employeeProvince}</span>
			</div>
		</div>
		<div class="info-row">
			<div class="info-item">
				<span class="info-label">Pay Period</span>
				<span class="info-value">{periodString}</span>
			</div>
			{#if payDate}
				<div class="info-item">
					<span class="info-label">Pay Date</span>
					<span class="info-value">{payDate}</span>
				</div>
			{/if}
		</div>
	</div>

	<!-- Main Content Grid -->
	<div class="content-grid">
		<!-- Earnings Section -->
		<div class="section earnings-section">
			<h4 class="section-title">EARNINGS</h4>
			<div class="line-items">
				<div class="line-item">
					<span class="item-label">Regular Pay</span>
					<span class="item-value">{formatCurrency(record.grossRegular)}</span>
				</div>
				{#if record.grossOvertime > 0}
					<div class="line-item highlight-success">
						<span class="item-label">
							<i class="fas fa-clock"></i>
							Overtime
						</span>
						<span class="item-value">{formatCurrency(record.grossOvertime)}</span>
					</div>
				{/if}
				{#if record.holidayPay > 0}
					<div class="line-item">
						<span class="item-label">Holiday Pay</span>
						<span class="item-value">{formatCurrency(record.holidayPay)}</span>
					</div>
				{/if}
				{#if record.holidayPremiumPay > 0}
					<div class="line-item">
						<span class="item-label">Holiday Premium</span>
						<span class="item-value">{formatCurrency(record.holidayPremiumPay)}</span>
					</div>
				{/if}
				{#if record.vacationPayPaid > 0}
					<div class="line-item">
						<span class="item-label">Vacation Pay</span>
						<span class="item-value">{formatCurrency(record.vacationPayPaid)}</span>
					</div>
				{/if}
				{#if hasEarningsAdjustments}
					<div class="line-item highlight-success">
						<span class="item-label">Other Earnings</span>
						<span class="item-value">{formatCurrency(otherEarningsTotal)}</span>
					</div>
					{#each earningsAdjustments.slice(0, 3) as adj (adj.id)}
						<div class="sub-item">
							<span class="sub-label">└─ {ADJUSTMENT_TYPE_LABELS[adj.type]?.label ?? adj.type}</span
							>
							<span class="sub-value">{formatCurrency(adj.amount)}</span>
						</div>
					{/each}
					{#if earningsAdjustments.length > 3}
						<div class="sub-item more-items">
							<span class="sub-label">└─ +{earningsAdjustments.length - 3} more</span>
						</div>
					{/if}
				{/if}
				<div class="line-item total">
					<span class="item-label">Total Gross</span>
					<span class="item-value">{formatCurrency(record.totalGross)}</span>
				</div>
			</div>
		</div>

		<!-- Deductions Section -->
		<div class="section deductions-section">
			<h4 class="section-title">DEDUCTIONS</h4>
			<div class="line-items">
				<div class="line-item">
					<span class="item-label">CPP</span>
					<span class="item-value deduction">{formatCurrency(record.cppEmployee)}</span>
				</div>
				{#if record.cppAdditional > 0}
					<div class="line-item">
						<span class="item-label">CPP2 (Enhanced)</span>
						<span class="item-value deduction">{formatCurrency(record.cppAdditional)}</span>
					</div>
				{/if}
				<div class="line-item">
					<span class="item-label">EI</span>
					<span class="item-value deduction">{formatCurrency(record.eiEmployee)}</span>
				</div>
				{#if hasTaxBreakdown}
					<div class="line-item">
						<span class="item-label">Federal Tax</span>
						<span class="item-value deduction">{formatCurrency(record.federalTax)}</span>
					</div>
					<div class="sub-item">
						<span class="sub-label">└─ On Income</span>
						<span class="sub-value deduction">{formatCurrency(record.federalTaxOnIncome ?? 0)}</span
						>
					</div>
					<div class="sub-item">
						<span class="sub-label">└─ On Bonus</span>
						<span class="sub-value deduction">{formatCurrency(record.federalTaxOnBonus ?? 0)}</span>
					</div>
				{:else}
					<div class="line-item">
						<span class="item-label">Federal Tax</span>
						<span class="item-value deduction">{formatCurrency(record.federalTax)}</span>
					</div>
				{/if}
				{#if hasTaxBreakdown}
					<div class="line-item">
						<span class="item-label">Provincial Tax</span>
						<span class="item-value deduction">{formatCurrency(record.provincialTax)}</span>
					</div>
					<div class="sub-item">
						<span class="sub-label">└─ On Income</span>
						<span class="sub-value deduction"
							>{formatCurrency(record.provincialTaxOnIncome ?? 0)}</span
						>
					</div>
					<div class="sub-item">
						<span class="sub-label">└─ On Bonus</span>
						<span class="sub-value deduction"
							>{formatCurrency(record.provincialTaxOnBonus ?? 0)}</span
						>
					</div>
				{:else}
					<div class="line-item">
						<span class="item-label">Provincial Tax</span>
						<span class="item-value deduction">{formatCurrency(record.provincialTax)}</span>
					</div>
				{/if}
				{#if record.rrsp > 0}
					<div class="line-item">
						<span class="item-label">RRSP</span>
						<span class="item-value deduction">{formatCurrency(record.rrsp)}</span>
					</div>
				{/if}
				{#if record.unionDues > 0}
					<div class="line-item">
						<span class="item-label">Union Dues</span>
						<span class="item-value deduction">{formatCurrency(record.unionDues)}</span>
					</div>
				{/if}
				{#if record.otherDeductions > 0}
					<div class="line-item">
						<span class="item-label">Other Deductions</span>
						<span class="item-value deduction">{formatCurrency(record.otherDeductions)}</span>
					</div>
				{/if}
				<div class="line-item total">
					<span class="item-label">Total Deductions</span>
					<span class="item-value deduction">-{formatCurrency(record.totalDeductions)}</span>
				</div>
			</div>
		</div>
	</div>

	<!-- Net Pay Section -->
	<div class="net-pay-section">
		<span class="net-pay-label">NET PAY</span>
		<span class="net-pay-value">{formatCurrency(record.netPay)}</span>
	</div>

	<!-- YTD Summary Section -->
	<div class="ytd-section">
		<h4 class="section-title">YEAR-TO-DATE</h4>
		<div class="ytd-grid">
			<div class="ytd-item">
				<span class="ytd-label">Gross</span>
				<span class="ytd-value">{formatCurrency(record.ytdGross)}</span>
			</div>
			<div class="ytd-item">
				<span class="ytd-label">CPP</span>
				<span class="ytd-value">{formatCurrency(record.ytdCpp)}</span>
			</div>
			<div class="ytd-item">
				<span class="ytd-label">EI</span>
				<span class="ytd-value">{formatCurrency(record.ytdEi)}</span>
			</div>
			<div class="ytd-item">
				<span class="ytd-label">Fed Tax</span>
				<span class="ytd-value">{formatCurrency(record.ytdFederalTax)}</span>
			</div>
			<div class="ytd-item">
				<span class="ytd-label">Prov Tax</span>
				<span class="ytd-value">{formatCurrency(record.ytdProvincialTax)}</span>
			</div>
			<div class="ytd-item highlight">
				<span class="ytd-label">Net Pay</span>
				<span class="ytd-value">{formatCurrency(record.ytdNetPay)}</span>
			</div>
		</div>
	</div>
</div>

<style>
	.paystub-preview {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
	}

	/* Header */
	.paystub-header {
		text-align: center;
		padding: var(--spacing-4);
		background: var(--gradient-primary);
		border-radius: var(--radius-lg);
		color: white;
	}

	.header-title {
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-bold);
	}

	.header-subtitle {
		font-size: var(--font-size-auxiliary-text);
		opacity: 0.8;
		margin-top: var(--spacing-1);
	}

	/* Info Section */
	.info-section {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		background: var(--color-surface-50);
		border-radius: var(--radius-lg);
	}

	.info-row {
		display: flex;
		gap: var(--spacing-6);
	}

	.info-item {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
		flex: 1;
	}

	.info-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.info-value {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	/* Content Grid */
	.content-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--spacing-4);
	}

	@media (max-width: 640px) {
		.content-grid {
			grid-template-columns: 1fr;
		}
	}

	/* Section */
	.section {
		background: white;
		border-radius: var(--radius-lg);
		padding: var(--spacing-4);
		box-shadow: var(--shadow-md3-1);
	}

	.section-title {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-500);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		margin: 0 0 var(--spacing-3);
		padding-bottom: var(--spacing-2);
		border-bottom: 1px solid var(--color-surface-100);
	}

	/* Line Items */
	.line-items {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.line-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-1) 0;
	}

	.line-item.total {
		margin-top: var(--spacing-2);
		padding-top: var(--spacing-2);
		border-top: 1px solid var(--color-surface-200);
		font-weight: var(--font-weight-semibold);
	}

	.line-item.highlight-success {
		background: var(--color-success-50);
		border-radius: var(--radius-md);
		padding: var(--spacing-2);
		margin: var(--spacing-1) 0;
	}

	.line-item.highlight-success .item-label {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		color: var(--color-success-700);
	}

	.line-item.highlight-success .item-value {
		color: var(--color-success-700);
	}

	.item-label {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
	}

	.item-value {
		font-size: var(--font-size-body-content);
		font-family: monospace;
		color: var(--color-surface-800);
	}

	.item-value.deduction {
		color: var(--color-error-600);
	}

	/* Sub Items */
	.sub-item {
		display: flex;
		align-items: center;
		padding: var(--spacing-1) 0;
		padding-left: var(--spacing-4);
	}

	.sub-label {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-500);
		font-family: monospace;
	}

	.sub-value {
		font-size: var(--font-size-body-content);
		font-family: monospace;
		color: var(--color-surface-600);
		margin-left: auto;
	}

	.sub-value.deduction {
		color: var(--color-error-500);
	}

	.sub-item.more-items .sub-label {
		font-style: italic;
		color: var(--color-surface-400);
	}

	/* Net Pay Section */
	.net-pay-section {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-5);
		background: var(--gradient-primary);
		border-radius: var(--radius-lg);
		color: white;
	}

	.net-pay-label {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
	}

	.net-pay-value {
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-bold);
		font-family: monospace;
	}

	/* YTD Section */
	.ytd-section {
		background: var(--color-surface-100);
		border-radius: var(--radius-lg);
		padding: var(--spacing-4);
	}

	.ytd-grid {
		display: grid;
		grid-template-columns: repeat(6, 1fr);
		gap: var(--spacing-3);
	}

	@media (max-width: 768px) {
		.ytd-grid {
			grid-template-columns: repeat(3, 1fr);
		}
	}

	@media (max-width: 480px) {
		.ytd-grid {
			grid-template-columns: repeat(2, 1fr);
		}
	}

	.ytd-item {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
		text-align: center;
		padding: var(--spacing-2);
		background: white;
		border-radius: var(--radius-md);
	}

	.ytd-item.highlight {
		background: var(--color-success-100);
	}

	.ytd-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.ytd-value {
		font-size: var(--font-size-body-content);
		font-family: monospace;
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.ytd-item.highlight .ytd-value {
		color: var(--color-success-700);
	}
</style>

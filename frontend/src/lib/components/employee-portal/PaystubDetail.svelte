<script lang="ts">
	/**
	 * PaystubDetail - Full paystub detail view component
	 */
	import type { PaystubDetail } from '$lib/types/employee-portal';
	import { formatShortDate } from '$lib/utils/dateUtils';

	interface Props {
		paystub: PaystubDetail;
		onDownload?: () => void;
	}

	let { paystub, onDownload }: Props = $props();

	function formatMoney(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD'
		}).format(amount);
	}
</script>

<div class="paystub-detail">
	<div class="paystub-document">
		<header class="document-header">
			<h2 class="document-title">PAYSTUB</h2>
			<div class="company-info">
				<span class="company-name">{paystub.companyName}</span>
				{#if paystub.companyAddress}
					<span class="company-address">{paystub.companyAddress}</span>
				{/if}
			</div>
			<div class="pay-date">Pay Date: {formatShortDate(paystub.payDate)}</div>
		</header>

		<div class="document-divider"></div>

		<div class="employee-period">
			<div class="employee-info">
				<span class="label">Employee:</span>
				<span class="value">{paystub.employeeName}</span>
			</div>
			<div class="period-info">
				<span class="label">Period:</span>
				<span class="value">{formatShortDate(paystub.payPeriodStart)} - {formatShortDate(paystub.payPeriodEnd)}</span>
			</div>
		</div>

		<div class="document-divider"></div>

		<div class="earnings-deductions">
			<!-- Earnings Column -->
			<div class="column">
				<h3 class="column-title">EARNINGS</h3>
				<div class="column-divider"></div>
				{#each paystub.earnings as earning}
					<div class="line-item">
						<span class="item-label">
							{earning.type}
							{#if earning.hours}({earning.hours}h){/if}
						</span>
						<span class="item-amount">{formatMoney(earning.amount)}</span>
					</div>
				{/each}
				<div class="column-divider"></div>
				<div class="line-item total">
					<span class="item-label">GROSS TOTAL</span>
					<span class="item-amount">{formatMoney(paystub.grossPay)}</span>
				</div>
			</div>

			<!-- Deductions Column -->
			<div class="column">
				<h3 class="column-title">DEDUCTIONS</h3>
				<div class="column-divider"></div>
				{#each paystub.deductions as deduction}
					<div class="line-item">
						<span class="item-label">{deduction.type}</span>
						<span class="item-amount">{formatMoney(deduction.amount)}</span>
					</div>
				{/each}
				<div class="column-divider"></div>
				<div class="line-item total">
					<span class="item-label">TOTAL DEDUCTIONS</span>
					<span class="item-amount">{formatMoney(paystub.totalDeductions)}</span>
				</div>
			</div>
		</div>

		<div class="document-divider"></div>

		<div class="net-pay-section">
			<span class="net-pay-label">NET PAY:</span>
			<span class="net-pay-amount">{formatMoney(paystub.netPay)}</span>
		</div>

		<div class="document-divider"></div>

		<div class="ytd-section">
			<h3 class="ytd-title">YTD TOTALS</h3>
			<div class="ytd-grid">
				<div class="ytd-item">
					<span class="ytd-label">Gross:</span>
					<span class="ytd-value">{formatMoney(paystub.ytd.grossEarnings)}</span>
				</div>
				<div class="ytd-item">
					<span class="ytd-label">CPP:</span>
					<span class="ytd-value">{formatMoney(paystub.ytd.cppPaid)}</span>
				</div>
				<div class="ytd-item">
					<span class="ytd-label">EI:</span>
					<span class="ytd-value">{formatMoney(paystub.ytd.eiPaid)}</span>
				</div>
				<div class="ytd-item">
					<span class="ytd-label">Tax:</span>
					<span class="ytd-value">{formatMoney(paystub.ytd.taxPaid)}</span>
				</div>
			</div>
		</div>

		<!-- Sick Leave Balance (if available) -->
		{#if paystub.sickBalanceHours !== undefined && paystub.sickBalanceHours > 0}
			<div class="leave-balance-section">
				<h3 class="ytd-title">LEAVE BALANCE</h3>
				<div class="ytd-grid">
					<div class="ytd-item">
						<span class="ytd-label">Sick Leave:</span>
						<span class="ytd-value highlight">{(paystub.sickBalanceHours / 8).toFixed(1)} days</span>
					</div>
					{#if paystub.sickHoursTaken && paystub.sickHoursTaken > 0}
						<div class="ytd-item">
							<span class="ytd-label">Used This Period:</span>
							<span class="ytd-value">{paystub.sickHoursTaken}h ({formatMoney(paystub.sickPayPaid ?? 0)})</span>
						</div>
					{/if}
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	.paystub-detail {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-2);
		overflow: hidden;
	}

	.paystub-document {
		padding: var(--spacing-6);
		font-family: var(--font-family-primary);
	}

	.document-header {
		text-align: center;
		margin-bottom: var(--spacing-4);
	}

	.document-title {
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-900);
		margin: 0 0 var(--spacing-3) 0;
		letter-spacing: 2px;
	}

	.company-info {
		display: flex;
		flex-direction: column;
		gap: 2px;
		margin-bottom: var(--spacing-2);
	}

	.company-name {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.company-address {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	.pay-date {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
	}

	.document-divider {
		height: 1px;
		background: var(--color-surface-300);
		margin: var(--spacing-4) 0;
	}

	.employee-period {
		display: flex;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: var(--spacing-4);
	}

	.employee-info,
	.period-info {
		display: flex;
		gap: var(--spacing-2);
	}

	.label {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
	}

	.value {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-900);
	}

	.earnings-deductions {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--spacing-6);
	}

	.column {
		min-width: 0;
	}

	.column-title {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-700);
		margin: 0 0 var(--spacing-2) 0;
		letter-spacing: 1px;
	}

	.column-divider {
		height: 1px;
		background: var(--color-surface-200);
		margin: var(--spacing-2) 0;
	}

	.line-item {
		display: flex;
		justify-content: space-between;
		padding: var(--spacing-1) 0;
	}

	.item-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-700);
	}

	.item-amount {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-900);
		text-align: right;
	}

	.line-item.total {
		padding-top: var(--spacing-2);
	}

	.line-item.total .item-label,
	.line-item.total .item-amount {
		font-weight: var(--font-weight-semibold);
	}

	.net-pay-section {
		display: flex;
		justify-content: center;
		align-items: baseline;
		gap: var(--spacing-3);
		padding: var(--spacing-4) 0;
	}

	.net-pay-label {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
	}

	.net-pay-amount {
		font-size: var(--font-size-headline-minimum);
		font-weight: var(--font-weight-semibold);
		color: var(--color-success-600);
	}

	.ytd-section {
		background: var(--color-surface-100);
		border-radius: var(--radius-md);
		padding: var(--spacing-4);
		margin-top: var(--spacing-2);
	}

	.ytd-title {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-700);
		margin: 0 0 var(--spacing-3) 0;
		letter-spacing: 1px;
	}

	.ytd-grid {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-4);
	}

	.ytd-item {
		display: flex;
		gap: var(--spacing-2);
	}

	.ytd-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	.ytd-value {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-900);
	}

	.ytd-value.highlight {
		color: var(--color-primary-600);
		font-weight: var(--font-weight-semibold);
	}

	.leave-balance-section {
		background: var(--color-primary-50);
		border-radius: var(--radius-md);
		padding: var(--spacing-4);
		margin-top: var(--spacing-3);
	}

	/* Mobile adjustments */
	@media (max-width: 640px) {
		.paystub-document {
			padding: var(--spacing-4);
		}

		.earnings-deductions {
			grid-template-columns: 1fr;
			gap: var(--spacing-4);
		}

		.employee-period {
			flex-direction: column;
			gap: var(--spacing-2);
		}

		.net-pay-amount {
			font-size: var(--font-size-title-large);
		}

		.ytd-grid {
			flex-direction: column;
			gap: var(--spacing-2);
		}
	}
</style>

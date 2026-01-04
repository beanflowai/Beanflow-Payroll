<script lang="ts">
	/**
	 * PaystubCard - Summary card for a single paystub
	 */
	import type { PaystubSummary } from '$lib/types/employee-portal';
	import { formatLongDate, formatDateNoYear } from '$lib/utils/dateUtils';
	import { formatCurrency } from '$lib/utils/formatUtils';

	interface Props {
		paystub: PaystubSummary;
		onView?: () => void;
		onDownload?: () => void;
	}

	let { paystub, onView, onDownload }: Props = $props();
</script>

<div class="paystub-card">
	<div class="paystub-header">
		<div class="paystub-date">{formatLongDate(paystub.payDate)}</div>
		<div class="paystub-period">
			Pay Period: {formatDateNoYear(paystub.payPeriodStart)} - {formatDateNoYear(
				paystub.payPeriodEnd
			)}
		</div>
	</div>

	<div class="paystub-divider"></div>

	<div class="paystub-amounts">
		<div class="amount-item">
			<span class="amount-label">Gross:</span>
			<span class="amount-value">{formatCurrency(paystub.grossPay)}</span>
		</div>
		<div class="amount-item">
			<span class="amount-label">Deductions:</span>
			<span class="amount-value deduction">{formatCurrency(paystub.totalDeductions)}</span>
		</div>
		<div class="amount-item net">
			<span class="amount-label">Net:</span>
			<span class="amount-value">{formatCurrency(paystub.netPay)}</span>
		</div>
	</div>

	<div class="paystub-actions">
		{#if onView}
			<button class="action-btn view-btn" onclick={onView} aria-label="View paystub details">
				View
			</button>
		{/if}
		<button class="action-btn download-btn" onclick={onDownload} aria-label="Download paystub PDF">
			<svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
				<path
					fill-rule="evenodd"
					d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
					clip-rule="evenodd"
				/>
			</svg>
		</button>
	</div>
</div>

<style>
	.paystub-card {
		background: white;
		border-radius: var(--radius-lg);
		padding: var(--spacing-5);
		box-shadow: var(--shadow-md3-1);
	}

	.paystub-header {
		margin-bottom: var(--spacing-3);
	}

	.paystub-date {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-900);
		margin-bottom: var(--spacing-1);
	}

	.paystub-period {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	.paystub-divider {
		height: 1px;
		background: var(--color-surface-200);
		margin: var(--spacing-3) 0;
	}

	.paystub-amounts {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-4);
		margin-bottom: var(--spacing-4);
	}

	.amount-item {
		display: flex;
		align-items: baseline;
		gap: var(--spacing-2);
	}

	.amount-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	.amount-value {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-900);
	}

	.amount-value.deduction {
		color: var(--color-error-600);
	}

	.amount-item.net .amount-value {
		font-size: var(--font-size-title-small);
		font-weight: var(--font-weight-semibold);
		color: var(--color-success-600);
	}

	.paystub-actions {
		display: flex;
		justify-content: flex-end;
		gap: var(--spacing-2);
	}

	.action-btn {
		padding: var(--spacing-2) var(--spacing-4);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
		text-decoration: none;
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-1);
	}

	.view-btn {
		background: var(--color-primary-500);
		color: white;
		border: none;
	}

	.view-btn:hover {
		background: var(--color-primary-600);
	}

	.download-btn {
		background: transparent;
		color: var(--color-surface-600);
		border: 1px solid var(--color-surface-300);
		padding: var(--spacing-2);
	}

	.download-btn:hover {
		background: var(--color-surface-100);
		color: var(--color-surface-800);
	}

	.download-btn svg {
		width: 16px;
		height: 16px;
	}

	/* Mobile adjustments */
	@media (max-width: 480px) {
		.paystub-amounts {
			flex-direction: column;
			gap: var(--spacing-2);
		}
	}
</style>

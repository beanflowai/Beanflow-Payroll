<script lang="ts">
	import type { UpcomingPayDate, PayGroupSummary } from '$lib/types/payroll';
	import { PAYROLL_STATUS_LABELS, PAY_FREQUENCY_LABELS, EMPLOYMENT_TYPE_LABELS } from '$lib/types/payroll';
	import { goto } from '$app/navigation';
	import { formatShortDate } from '$lib/utils/dateUtils';

	interface Props {
		payDateData: UpcomingPayDate;
		onPayGroupClick?: (payGroup: PayGroupSummary) => void;
	}

	let { payDateData, onPayGroupClick }: Props = $props();

	// Helpers
	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		}).format(amount);
	}

	function getDaysUntil(dateStr: string): string {
		const today = new Date();
		today.setHours(0, 0, 0, 0);
		const payDate = new Date(dateStr);
		payDate.setHours(0, 0, 0, 0);
		const diffTime = payDate.getTime() - today.getTime();
		const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

		if (diffDays < 0) return `${Math.abs(diffDays)} days overdue`;
		if (diffDays === 0) return 'Today';
		if (diffDays === 1) return 'Tomorrow';
		return `in ${diffDays} days`;
	}

	function getDaysUntilClass(dateStr: string): string {
		const today = new Date();
		today.setHours(0, 0, 0, 0);
		const payDate = new Date(dateStr);
		payDate.setHours(0, 0, 0, 0);
		const diffTime = payDate.getTime() - today.getTime();
		const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

		if (diffDays < 0) return 'overdue';
		if (diffDays <= 3) return 'urgent';
		if (diffDays <= 7) return 'soon';
		return 'normal';
	}

	function getStatusClass(status?: string): string {
		if (!status) return '';
		switch (status) {
			case 'paid':
				return 'status-paid';
			case 'approved':
				return 'status-approved';
			case 'pending_approval':
				return 'status-pending';
			case 'draft':
				return 'status-draft';
			default:
				return '';
		}
	}

	function handleRunPayroll() {
		// Navigate to the payroll run detail page
		goto(`/payroll/run/${payDateData.payDate}`);
	}

	function getButtonLabel(): string {
		if (!payDateData.runStatus) return 'Start Payroll';
		switch (payDateData.runStatus) {
			case 'draft':
				return 'Continue';
			case 'pending_approval':
				return 'Review & Approve';
			case 'approved':
			case 'paid':
				return 'View Details';
			default:
				return 'Run Payroll';
		}
	}

	const daysUntilClass = $derived(getDaysUntilClass(payDateData.payDate));
</script>

<div class="pay-date-card">
	<div class="card-header">
		<div class="date-info">
			<div class="date-icon">
				<i class="fas fa-calendar-alt"></i>
			</div>
			<div class="date-text">
				<h3 class="pay-date">{formatShortDate(payDateData.payDate)}</h3>
				<span class="days-until {daysUntilClass}">{getDaysUntil(payDateData.payDate)}</span>
			</div>
		</div>
		<div class="card-actions">
			{#if payDateData.runStatus}
				<span class="status-badge {getStatusClass(payDateData.runStatus)}">
					{PAYROLL_STATUS_LABELS[payDateData.runStatus]}
				</span>
			{/if}
			<button class="run-btn" onclick={handleRunPayroll}>
				{getButtonLabel()}
				<i class="fas fa-arrow-right"></i>
			</button>
		</div>
	</div>

	<div class="card-summary">
		<span class="summary-item">
			<i class="fas fa-layer-group"></i>
			{payDateData.payGroups.length} Pay Group{payDateData.payGroups.length > 1 ? 's' : ''}
		</span>
		<span class="summary-divider"></span>
		<span class="summary-item">
			<i class="fas fa-users"></i>
			{payDateData.totalEmployees} Employee{payDateData.totalEmployees > 1 ? 's' : ''}
		</span>
		<span class="summary-divider"></span>
		<span class="summary-item estimated">
			<i class="fas fa-dollar-sign"></i>
			Est. {formatCurrency(payDateData.totalEstimatedGross)}
		</span>
	</div>

	<div class="pay-groups-list">
		{#each payDateData.payGroups as group (group.id)}
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<div
				class="pay-group-chip"
				class:no-employees={group.employeeCount === 0}
				class:clickable={!!onPayGroupClick}
				onclick={() => onPayGroupClick?.(group)}
			>
				<div class="chip-header">
					<span class="chip-name">{group.name}</span>
					{#if onPayGroupClick}
						<i class="fas fa-chevron-right chip-arrow"></i>
					{/if}
				</div>
				{#if group.employeeCount === 0}
					<div class="chip-empty">
						<span class="chip-empty-text">No employees</span>
					</div>
				{:else}
					<div class="chip-details">
						<span class="chip-stat">{group.employeeCount} emp</span>
						<span class="chip-divider"></span>
						<span class="chip-stat">{formatCurrency(group.estimatedGross)}</span>
					</div>
				{/if}
			</div>
		{/each}
	</div>
</div>

<style>
	.pay-date-card {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		padding: var(--spacing-5);
		transition: var(--transition-fast);
	}

	.pay-date-card:hover {
		box-shadow: var(--shadow-md3-2);
	}

	.card-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		margin-bottom: var(--spacing-4);
		gap: var(--spacing-4);
	}

	.date-info {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
	}

	.date-icon {
		width: 44px;
		height: 44px;
		border-radius: var(--radius-lg);
		background: var(--color-primary-100);
		color: var(--color-primary-600);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 18px;
	}

	.date-text {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.pay-date {
		font-size: var(--font-size-title-small);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0;
	}

	.days-until {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		padding: var(--spacing-1) var(--spacing-2);
		border-radius: var(--radius-sm);
	}

	.days-until.normal {
		background: var(--color-surface-100);
		color: var(--color-surface-600);
	}

	.days-until.soon {
		background: var(--color-info-100);
		color: var(--color-info-700);
	}

	.days-until.urgent {
		background: var(--color-warning-100);
		color: var(--color-warning-700);
	}

	.days-until.overdue {
		background: var(--color-error-100);
		color: var(--color-error-700);
	}

	.card-actions {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
	}

	.status-badge {
		display: inline-flex;
		align-items: center;
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

	.run-btn {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		background: var(--gradient-primary);
		color: white;
		border: none;
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.run-btn:hover {
		opacity: 0.9;
		transform: translateY(-1px);
	}

	.run-btn i {
		font-size: 12px;
	}

	.card-summary {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-surface-50);
		border-radius: var(--radius-lg);
		margin-bottom: var(--spacing-4);
	}

	.summary-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
	}

	.summary-item i {
		color: var(--color-surface-500);
		font-size: 14px;
	}

	.summary-item.estimated {
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.summary-divider {
		width: 1px;
		height: 16px;
		background: var(--color-surface-200);
	}

	.pay-groups-list {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-3);
	}

	.pay-group-chip {
		flex: 1;
		min-width: 160px;
		max-width: 240px;
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-surface-50);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-lg);
		transition: var(--transition-fast);
	}

	.pay-group-chip.clickable {
		cursor: pointer;
	}

	.pay-group-chip.clickable:hover {
		background: var(--color-surface-100);
		border-color: var(--color-primary-300);
		box-shadow: var(--shadow-sm);
	}

	.chip-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: var(--spacing-2);
	}

	.chip-name {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.chip-arrow {
		font-size: 10px;
		color: var(--color-surface-400);
		transition: var(--transition-fast);
	}

	.pay-group-chip.clickable:hover .chip-arrow {
		color: var(--color-primary-500);
		transform: translateX(2px);
	}

	.chip-details {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
	}

	.chip-stat {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	.chip-divider {
		width: 4px;
		height: 4px;
		border-radius: 50%;
		background: var(--color-surface-300);
	}

	/* No employees state */
	.pay-group-chip.no-employees {
		border-color: var(--color-warning-200);
		background: var(--color-warning-50);
	}

	.chip-empty {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--spacing-2);
	}

	.chip-empty-text {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-warning-700);
	}

	@media (max-width: 768px) {
		.card-header {
			flex-direction: column;
		}

		.card-actions {
			width: 100%;
			justify-content: space-between;
		}

		.card-summary {
			flex-wrap: wrap;
		}

		.pay-group-chip {
			max-width: none;
		}
	}
</style>

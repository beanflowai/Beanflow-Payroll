<script lang="ts">
	// PayGroupDetailHeader - Header with back navigation, title, and actions
	import type { PayGroup } from '$lib/types/pay-group';
	import { PAY_FREQUENCY_INFO, EMPLOYMENT_TYPE_INFO } from '$lib/types/pay-group';
	import { formatShortDate } from '$lib/utils/dateUtils';

	interface Props {
		payGroup: PayGroup;
		isNew?: boolean;
		onBack: () => void;
		onDelete: () => void;
	}

	let { payGroup, isNew = false, onBack, onDelete }: Props = $props();

	// Calculate days until next pay date
	function getDaysUntilPayDate(dateStr: string): number {
		const today = new Date();
		today.setHours(0, 0, 0, 0);
		const payDate = new Date(dateStr);
		payDate.setHours(0, 0, 0, 0);
		const diffTime = payDate.getTime() - today.getTime();
		return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
	}

	// Get badge variant class based on days until pay
	function getBadgeVariant(days: number): string {
		if (days < 0) return 'overdue';
		if (days === 0) return 'today';
		if (days === 1) return 'tomorrow';
		if (days <= 7) return 'soon';
		return 'normal';
	}

	// Derived values
	const frequencyLabel = $derived(PAY_FREQUENCY_INFO[payGroup.payFrequency].label);
	const typeLabel = $derived(EMPLOYMENT_TYPE_INFO[payGroup.employmentType].label);
	const daysUntilPay = $derived(getDaysUntilPayDate(payGroup.nextPayDate));
	const badgeVariant = $derived(getBadgeVariant(daysUntilPay));
</script>

<div class="detail-header">
	<!-- Back Navigation -->
	<button class="back-button" onclick={onBack}>
		<i class="fas fa-arrow-left"></i>
		<span>Back to Pay Groups</span>
	</button>

	<!-- Main Header Content -->
	<div class="header-content">
		<!-- Delete button positioned absolutely in top-right -->
		{#if !isNew}
			<button class="btn-delete" onclick={onDelete} title="Delete pay group">
				<i class="fas fa-trash"></i>
				<span>Delete</span>
			</button>
		{/if}

		<div class="title-section">
			<div class="icon-wrapper" class:new-mode={isNew}>
				<i class="fas {isNew ? 'fa-plus' : 'fa-clipboard-list'}"></i>
			</div>
			<div class="title-info">
				{#if isNew}
					<h1 class="title">New Pay Group</h1>
					<p class="subtitle">Configure your new pay group</p>
				{:else}
					<h1 class="title">{payGroup.name}</h1>

					<!-- Metadata line: Frequency + Type + Next Pay Date -->
					<div class="metadata-line">
						<span class="metadata-item">{frequencyLabel}</span>
						<span class="metadata-separator">&middot;</span>
						<span class="metadata-item">{typeLabel}</span>

						{#if payGroup.nextPayDate}
							<span class="metadata-separator">&middot;</span>
							<span class="next-pay-inline">
								<i class="fas fa-calendar-alt"></i>
								<span class="pay-date">{formatShortDate(payGroup.nextPayDate)}</span>
								<span class="pay-badge {badgeVariant}">
									{#if daysUntilPay < 0}
										Overdue
									{:else if daysUntilPay === 0}
										Today
									{:else if daysUntilPay === 1}
										Tomorrow
									{:else}
										In {daysUntilPay} days
									{/if}
								</span>
							</span>
						{/if}
					</div>

					{#if payGroup.description}
						<p class="description">{payGroup.description}</p>
					{/if}
				{/if}
			</div>
		</div>
	</div>
</div>

<style>
	.detail-header {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
	}

	.back-button {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-3);
		background: transparent;
		border: none;
		color: var(--color-surface-600);
		font-size: var(--font-size-body-content);
		cursor: pointer;
		transition: var(--transition-fast);
		border-radius: var(--radius-md);
		margin-left: calc(-1 * var(--spacing-3));
	}

	.back-button:hover {
		background: var(--color-surface-100);
		color: var(--color-primary-600);
	}

	.header-content {
		position: relative;
		padding: var(--spacing-5);
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
	}

	/* Delete button - positioned top-right */
	.btn-delete {
		position: absolute;
		top: var(--spacing-4);
		right: var(--spacing-4);
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		background: transparent;
		color: var(--color-surface-500);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-md);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
		z-index: 1;
	}

	.btn-delete:hover {
		background: var(--color-error-50);
		color: var(--color-error-600);
		border-color: var(--color-error-200);
	}

	.title-section {
		display: flex;
		gap: var(--spacing-4);
		padding-right: 100px; /* Leave space for delete button */
	}

	.icon-wrapper {
		width: 56px;
		height: 56px;
		border-radius: var(--radius-lg);
		background: var(--color-primary-50);
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.icon-wrapper i {
		font-size: 24px;
		color: var(--color-primary-500);
	}

	.icon-wrapper.new-mode {
		background: var(--color-success-50);
	}

	.icon-wrapper.new-mode i {
		color: var(--color-success-600);
	}

	.title-info {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
		min-width: 0; /* Allow text truncation */
	}

	.title {
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-bold);
		color: var(--color-surface-900);
		margin: 0;
	}

	.subtitle {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-500);
		margin: 0;
	}

	/* Metadata line with frequency, type, and pay date */
	.metadata-line {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: var(--spacing-1);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-500);
		line-height: 1.5;
	}

	.metadata-item {
		color: var(--color-surface-500);
	}

	.metadata-separator {
		color: var(--color-surface-300);
		margin: 0 var(--spacing-1);
	}

	/* Next pay date inline display */
	.next-pay-inline {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
	}

	.next-pay-inline i {
		font-size: 14px;
		color: var(--color-primary-500);
	}

	.pay-date {
		color: var(--color-surface-700);
		font-weight: var(--font-weight-medium);
	}

	/* Pay date badge - inline style */
	.pay-badge {
		display: inline-flex;
		align-items: center;
		padding: 2px var(--spacing-2);
		border-radius: var(--radius-full);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		white-space: nowrap;
		line-height: 1.2;
	}

	.pay-badge.normal {
		background: var(--color-surface-100);
		color: var(--color-surface-600);
	}

	.pay-badge.soon {
		background: var(--color-warning-100);
		color: var(--color-warning-700);
	}

	.pay-badge.today {
		background: var(--color-success-100);
		color: var(--color-success-700);
	}

	.pay-badge.tomorrow {
		background: var(--color-success-50);
		color: var(--color-success-600);
	}

	.pay-badge.overdue {
		background: var(--color-error-100);
		color: var(--color-error-700);
	}

	.description {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: var(--spacing-2) 0 0;
	}

	/* ===== Responsive Design ===== */

	/* Tablet: < 900px */
	@media (max-width: 900px) {
		.title-section {
			padding-right: 0;
		}

		.btn-delete {
			position: static;
			margin-top: var(--spacing-4);
		}

		.header-content {
			display: flex;
			flex-direction: column;
		}
	}

	/* Mobile: < 640px */
	@media (max-width: 640px) {
		.title-section {
			flex-direction: column;
			align-items: flex-start;
		}

		.metadata-line {
			flex-direction: column;
			align-items: flex-start;
			gap: var(--spacing-2);
		}

		.metadata-separator {
			display: none;
		}

		.next-pay-inline {
			margin-top: var(--spacing-1);
			padding: var(--spacing-2) var(--spacing-3);
			background: var(--color-surface-50);
			border-radius: var(--radius-md);
			border: 1px solid var(--color-surface-100);
		}

		.btn-delete {
			width: 100%;
			justify-content: center;
		}
	}
</style>

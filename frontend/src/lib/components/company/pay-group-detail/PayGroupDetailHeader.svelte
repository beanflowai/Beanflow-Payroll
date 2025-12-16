<script lang="ts">
	// PayGroupDetailHeader - Header with back navigation, title, and actions
	import type { PayGroup } from '$lib/types/pay-group';
	import { PAY_FREQUENCY_INFO, EMPLOYMENT_TYPE_INFO } from '$lib/types/pay-group';

	interface Props {
		payGroup: PayGroup;
		isNew?: boolean;
		onBack: () => void;
		onDelete: () => void;
	}

	let { payGroup, isNew = false, onBack, onDelete }: Props = $props();

	// Format date for display
	function formatDate(dateStr: string): string {
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-CA', {
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	}

	// Calculate days until next pay date
	function getDaysUntilPayDate(dateStr: string): number {
		const today = new Date();
		today.setHours(0, 0, 0, 0);
		const payDate = new Date(dateStr);
		payDate.setHours(0, 0, 0, 0);
		const diffTime = payDate.getTime() - today.getTime();
		return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
	}

	// Derived values
	const frequencyLabel = $derived(PAY_FREQUENCY_INFO[payGroup.payFrequency].label);
	const typeLabel = $derived(EMPLOYMENT_TYPE_INFO[payGroup.employmentType].label);
	const daysUntilPay = $derived(getDaysUntilPayDate(payGroup.nextPayDate));
</script>

<div class="detail-header">
	<!-- Back Navigation -->
	<button class="back-button" onclick={onBack}>
		<i class="fas fa-arrow-left"></i>
		<span>Back to Pay Groups</span>
	</button>

	<!-- Main Header Content -->
	<div class="header-content">
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
					<p class="subtitle">{frequencyLabel} &middot; {typeLabel}</p>
					{#if payGroup.description}
						<p class="description">{payGroup.description}</p>
					{/if}
				{/if}
			</div>
		</div>

		{#if !isNew}
			<div class="actions">
				<button class="btn-delete" onclick={onDelete} title="Delete pay group">
					<i class="fas fa-trash"></i>
					<span>Delete</span>
				</button>
			</div>
		{/if}
	</div>

	<!-- Pay Date Info (only show for existing pay groups with valid date) -->
	{#if !isNew && payGroup.nextPayDate}
		<div class="pay-date-info">
			<div class="info-card">
				<i class="fas fa-calendar-alt"></i>
				<div class="info-content">
					<span class="info-label">Next Pay Date</span>
					<span class="info-value">{formatDate(payGroup.nextPayDate)}</span>
					{#if daysUntilPay >= 0}
						<span class="info-badge" class:soon={daysUntilPay <= 7}>
							{#if daysUntilPay === 0}
								Today
							{:else if daysUntilPay === 1}
								Tomorrow
							{:else}
								In {daysUntilPay} days
							{/if}
						</span>
					{:else}
						<span class="info-badge overdue">Overdue</span>
					{/if}
				</div>
			</div>
		</div>
	{/if}
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
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: var(--spacing-4);
		padding: var(--spacing-5);
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
	}

	.title-section {
		display: flex;
		gap: var(--spacing-4);
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

	.description {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: var(--spacing-2) 0 0;
	}

	.actions {
		display: flex;
		gap: var(--spacing-2);
	}

	.btn-delete {
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
	}

	.btn-delete:hover {
		background: var(--color-error-50);
		color: var(--color-error-600);
		border-color: var(--color-error-200);
	}

	.pay-date-info {
		display: flex;
		gap: var(--spacing-4);
	}

	.info-card {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		background: white;
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-md3-1);
	}

	.info-card > i {
		font-size: 20px;
		color: var(--color-primary-500);
	}

	.info-content {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.info-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.info-value {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.info-badge {
		display: inline-block;
		padding: var(--spacing-1) var(--spacing-2);
		background: var(--color-surface-100);
		border-radius: var(--radius-full);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
		width: fit-content;
	}

	.info-badge.soon {
		background: var(--color-warning-100);
		color: var(--color-warning-700);
	}

	.info-badge.overdue {
		background: var(--color-error-100);
		color: var(--color-error-700);
	}

	@media (max-width: 640px) {
		.header-content {
			flex-direction: column;
		}

		.actions {
			width: 100%;
		}

		.btn-delete {
			width: 100%;
			justify-content: center;
		}

		.title-section {
			flex-direction: column;
			align-items: flex-start;
		}
	}
</style>

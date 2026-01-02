<script lang="ts">
	// PayGroupCard - Individual pay group display card with policy badges
	import type { PayGroup } from '$lib/types/pay-group';
	import {
		PAY_FREQUENCY_INFO,
		EMPLOYMENT_TYPE_INFO,
		getPayGroupPolicySummary,
		countEnabledBenefits,
		calculatePayDate
	} from '$lib/types/pay-group';
	import { formatShortDate } from '$lib/utils/dateUtils';

	interface Props {
		payGroup: PayGroup;
		companyProvince?: string;
		onView: (payGroup: PayGroup) => void;
		onDelete: (payGroup: PayGroup) => void;
	}

	let { payGroup, companyProvince = 'SK', onView, onDelete }: Props = $props();

	// Get policy summary for badges
	const policySummary = $derived(getPayGroupPolicySummary(payGroup));

	// Count benefits for display
	const enabledBenefitsCount = $derived(countEnabledBenefits(payGroup.groupBenefits));

	// Calculate pay date from period end based on company province
	const computedPayDate = $derived(
		payGroup.nextPeriodEnd ? calculatePayDate(payGroup.nextPeriodEnd, companyProvince) : ''
	);

	// Handle card click (navigate to detail)
	function handleCardClick() {
		onView(payGroup);
	}

	// Handle keyboard navigation
	function handleKeyDown(event: KeyboardEvent) {
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			onView(payGroup);
		}
	}

	// Stop propagation for action buttons
	function handleDeleteClick(event: MouseEvent) {
		event.stopPropagation();
		onDelete(payGroup);
	}
</script>

<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
<div
	class="pay-group-card"
	onclick={handleCardClick}
	onkeydown={handleKeyDown}
	tabindex="0"
	role="button"
	aria-label="View {payGroup.name} details"
>
	<div class="card-header">
		<div class="header-content">
			<i class="fas fa-clipboard-list card-icon"></i>
			<div class="title-group">
				<h3 class="card-title">{payGroup.name}</h3>
				{#if payGroup.description}
					<p class="card-description">{payGroup.description}</p>
				{/if}
			</div>
		</div>
		<i class="fas fa-chevron-right view-arrow"></i>
	</div>

	<div class="card-body">
		<div class="stats-row">
			<div class="stat-item">
				<span class="stat-label">Frequency</span>
				<span class="stat-value">{PAY_FREQUENCY_INFO[payGroup.payFrequency].label}</span>
			</div>
			<div class="stat-item">
				<span class="stat-label">Type</span>
				<span class="stat-value">{EMPLOYMENT_TYPE_INFO[payGroup.employmentType].label}</span>
			</div>
			<div class="stat-item">
				<span class="stat-label">Next Pay</span>
				<span class="stat-value">{computedPayDate ? formatShortDate(computedPayDate) : '—'}</span>
			</div>
		</div>

		<!-- Policy Badges -->
		<div class="policy-badges">
			<span class="policy-label">Policies:</span>
			<div class="badges-row">
				<span class="badge" class:enabled={policySummary.wcb} title="Workers Compensation">
					{#if policySummary.wcb}
						<i class="fas fa-check-circle"></i>
					{:else}
						<i class="fas fa-circle"></i>
					{/if}
					WCB
				</span>
				<span class="badge" class:enabled={policySummary.benefits} title="Group Benefits">
					{#if policySummary.benefits}
						<i class="fas fa-check-circle"></i>
						Benefits ({enabledBenefitsCount})
					{:else}
						<i class="fas fa-circle"></i>
						Benefits
					{/if}
				</span>
				<span class="badge" class:enabled={policySummary.bankTime} title="Bank Time / TOIL">
					{#if policySummary.bankTime}
						<i class="fas fa-check-circle"></i>
					{:else}
						<i class="fas fa-circle"></i>
					{/if}
					Bank Time
				</span>
			</div>
		</div>
	</div>

	<div class="card-footer">
		<button class="btn-view" onclick={handleCardClick}>
			<span>View Details</span>
			<i class="fas fa-arrow-right"></i>
		</button>
		<button class="btn-delete" onclick={handleDeleteClick} title="Delete pay group">
			<i class="fas fa-trash"></i>
		</button>
	</div>
</div>

<style>
	.pay-group-card {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		overflow: hidden;
		transition: var(--transition-fast);
		cursor: pointer;
	}

	.pay-group-card:hover {
		box-shadow: var(--shadow-md3-2);
		transform: translateY(-2px);
	}

	.pay-group-card:focus {
		outline: 2px solid var(--color-primary-500);
		outline-offset: 2px;
	}

	.card-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--spacing-4) var(--spacing-5);
		background: var(--color-surface-50);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.header-content {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-3);
	}

	.card-icon {
		font-size: 20px;
		color: var(--color-primary-500);
		margin-top: 2px;
	}

	.title-group {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.card-title {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0;
	}

	.card-description {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
		margin: 0;
	}

	.view-arrow {
		color: var(--color-surface-400);
		transition: var(--transition-fast);
	}

	.pay-group-card:hover .view-arrow {
		color: var(--color-primary-500);
		transform: translateX(4px);
	}

	.card-body {
		padding: var(--spacing-5);
	}

	.stats-row {
		display: flex;
		gap: var(--spacing-3);
		margin-bottom: var(--spacing-4);
	}

	.stat-item {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
		padding: var(--spacing-3);
		background: var(--color-surface-50);
		border-radius: var(--radius-md);
		text-align: center;
	}

	.stat-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.stat-value {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	/* Policy Badges */
	.policy-badges {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.policy-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.badges-row {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-2);
	}

	.badge {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-1);
		padding: var(--spacing-1) var(--spacing-2);
		background: var(--color-surface-100);
		border-radius: var(--radius-full);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.badge i {
		font-size: 10px;
	}

	.badge.enabled {
		background: var(--color-success-50);
		color: var(--color-success-700);
	}

	.badge.enabled i {
		color: var(--color-success-500);
	}

	.badge.exempt {
		background: var(--color-warning-50);
		color: var(--color-warning-700);
	}

	.badge.exempt i {
		color: var(--color-warning-500);
	}

	.card-footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-3) var(--spacing-5);
		border-top: 1px solid var(--color-surface-100);
		background: var(--color-surface-50);
	}

	.btn-view {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		background: var(--color-primary-500);
		color: white;
		border: none;
		border-radius: var(--radius-md);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-view:hover {
		background: var(--color-primary-600);
	}

	.btn-view i {
		transition: var(--transition-fast);
	}

	.btn-view:hover i {
		transform: translateX(4px);
	}

	.btn-delete {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 36px;
		height: 36px;
		background: transparent;
		color: var(--color-surface-400);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-delete:hover {
		background: var(--color-error-50);
		color: var(--color-error-600);
		border-color: var(--color-error-200);
	}

	@media (max-width: 640px) {
		.stats-row {
			flex-direction: column;
		}

		.badges-row {
			flex-direction: column;
		}

		.card-footer {
			flex-direction: column;
			gap: var(--spacing-2);
		}

		.btn-view {
			width: 100%;
			justify-content: center;
		}

		.btn-delete {
			width: 100%;
		}
	}
</style>

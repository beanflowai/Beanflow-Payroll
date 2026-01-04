<script lang="ts">
	/**
	 * LeaveBalanceCard - Display leave balance with circular progress
	 */
	import { formatCurrency } from '$lib/utils/formatUtils';

	interface Props {
		type: 'vacation' | 'sick';
		hoursRemaining: number;
		hoursTotal?: number;
		dollarsValue?: number;
		accrualRate?: number;
		ytdAccrued?: number;
		ytdUsed?: number;
		allowance?: number;
		usedThisYear?: number;
	}

	let {
		type,
		hoursRemaining,
		hoursTotal: _hoursTotal,
		dollarsValue,
		accrualRate,
		ytdAccrued,
		ytdUsed,
		allowance,
		usedThisYear
	}: Props = $props();

	const title = $derived(type === 'vacation' ? 'Vacation' : 'Sick Leave');
	const _icon = $derived(type === 'vacation' ? 'vacation' : 'sick');

	// Calculate percentage for progress ring
	const percentage = $derived(() => {
		if (type === 'vacation' && ytdAccrued) {
			return Math.min(100, (hoursRemaining / ytdAccrued) * 100);
		}
		if (type === 'sick' && allowance) {
			return Math.min(100, (hoursRemaining / allowance) * 100);
		}
		return 100;
	});

	// SVG circle calculations
	const radius = 45;
	const circumference = 2 * Math.PI * radius;
	const strokeDashoffset = $derived(circumference - (percentage() / 100) * circumference);
</script>

<div class="leave-card" class:vacation={type === 'vacation'} class:sick={type === 'sick'}>
	<div class="card-header">
		<span class="card-icon">
			{#if type === 'vacation'}
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<circle cx="12" cy="12" r="10" />
					<path d="M12 6v6l4 2" />
				</svg>
			{:else}
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M22 12h-4l-3 9L9 3l-3 9H2" />
				</svg>
			{/if}
		</span>
		<h3 class="card-title">{title}</h3>
	</div>

	<div class="card-body">
		<div class="progress-ring-container">
			<svg class="progress-ring" viewBox="0 0 100 100">
				<circle class="progress-bg" cx="50" cy="50" r={radius} />
				<circle
					class="progress-value"
					cx="50"
					cy="50"
					r={radius}
					stroke-dasharray={circumference}
					stroke-dashoffset={strokeDashoffset}
				/>
			</svg>
			<div class="progress-text">
				<span class="hours-value">{hoursRemaining}h</span>
				{#if dollarsValue}
					<span class="dollars-value">{formatCurrency(dollarsValue)}</span>
				{:else}
					<span class="hours-label">remaining</span>
				{/if}
			</div>
		</div>

		<div class="card-details">
			{#if type === 'vacation'}
				{#if accrualRate}
					<div class="detail-row">
						<span class="detail-label">Accrual Rate</span>
						<span class="detail-value">{accrualRate.toFixed(2)}%</span>
					</div>
				{/if}
				{#if ytdAccrued !== undefined}
					<div class="detail-row">
						<span class="detail-label">YTD Accrued</span>
						<span class="detail-value">{ytdAccrued}h</span>
					</div>
				{/if}
				{#if ytdUsed !== undefined}
					<div class="detail-row">
						<span class="detail-label">YTD Used</span>
						<span class="detail-value">{ytdUsed}h</span>
					</div>
				{/if}
			{:else}
				{#if allowance}
					<div class="detail-row">
						<span class="detail-label">Provincial Allowance</span>
						<span class="detail-value">{allowance}h/year</span>
					</div>
				{/if}
				{#if usedThisYear !== undefined}
					<div class="detail-row">
						<span class="detail-label">Used This Year</span>
						<span class="detail-value">{usedThisYear}h</span>
					</div>
				{/if}
			{/if}
		</div>
	</div>
</div>

<style>
	.leave-card {
		background: white;
		border-radius: var(--radius-xl);
		padding: var(--spacing-5);
		box-shadow: var(--shadow-md3-1);
	}

	.card-header {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		margin-bottom: var(--spacing-4);
	}

	.card-icon {
		width: 24px;
		height: 24px;
	}

	.leave-card.vacation .card-icon {
		color: var(--color-primary-500);
	}

	.leave-card.sick .card-icon {
		color: var(--color-warning-500);
	}

	.card-icon svg {
		width: 100%;
		height: 100%;
	}

	.card-title {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-900);
		margin: 0;
	}

	.card-body {
		display: flex;
		gap: var(--spacing-6);
		align-items: center;
	}

	.progress-ring-container {
		position: relative;
		width: 120px;
		height: 120px;
		flex-shrink: 0;
	}

	.progress-ring {
		width: 100%;
		height: 100%;
		transform: rotate(-90deg);
	}

	.progress-bg {
		fill: none;
		stroke: var(--color-surface-200);
		stroke-width: 8;
	}

	.progress-value {
		fill: none;
		stroke-width: 8;
		stroke-linecap: round;
		transition: stroke-dashoffset 0.5s ease;
	}

	.leave-card.vacation .progress-value {
		stroke: var(--color-primary-500);
	}

	.leave-card.sick .progress-value {
		stroke: var(--color-warning-500);
	}

	.progress-text {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		text-align: center;
	}

	.hours-value {
		display: block;
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-900);
	}

	.dollars-value {
		display: block;
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-success-600);
	}

	.hours-label {
		display: block;
		font-size: var(--font-size-caption-text);
		color: var(--color-surface-600);
	}

	.card-details {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.detail-row {
		display: flex;
		justify-content: space-between;
		padding: var(--spacing-2) 0;
		border-bottom: 1px solid var(--color-surface-100);
	}

	.detail-row:last-child {
		border-bottom: none;
	}

	.detail-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	.detail-value {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	/* Mobile adjustments */
	@media (max-width: 480px) {
		.card-body {
			flex-direction: column;
			gap: var(--spacing-4);
		}

		.progress-ring-container {
			width: 100px;
			height: 100px;
		}

		.card-details {
			width: 100%;
		}
	}
</style>

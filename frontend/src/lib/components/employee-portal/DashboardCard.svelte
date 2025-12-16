<script lang="ts">
	/**
	 * DashboardCard - Summary card for dashboard metrics
	 * Shows icon, label, value, and optional action button
	 */
	import type { Snippet } from 'svelte';

	interface Props {
		icon: 'money' | 'vacation' | 'sick';
		label: string;
		value: string;
		subValue?: string;
		actionLabel?: string;
		actionHref?: string;
		onAction?: () => void;
		children?: Snippet;
	}

	let {
		icon,
		label,
		value,
		subValue,
		actionLabel,
		actionHref,
		onAction,
		children
	}: Props = $props();
</script>

<div class="dashboard-card">
	<div class="card-icon" class:money={icon === 'money'} class:vacation={icon === 'vacation'} class:sick={icon === 'sick'}>
		{#if icon === 'money'}
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<line x1="12" y1="1" x2="12" y2="23" />
				<path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
			</svg>
		{:else if icon === 'vacation'}
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
				<circle cx="9" cy="7" r="4" />
				<path d="M23 21v-2a4 4 0 0 0-3-3.87" />
				<path d="M16 3.13a4 4 0 0 1 0 7.75" />
			</svg>
		{:else if icon === 'sick'}
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<path d="M22 12h-4l-3 9L9 3l-3 9H2" />
			</svg>
		{/if}
	</div>

	<div class="card-content">
		<span class="card-label">{label}</span>
		<span class="card-value">{value}</span>
		{#if subValue}
			<span class="card-subvalue">{subValue}</span>
		{/if}
	</div>

	{#if actionLabel}
		{#if actionHref}
			<a href={actionHref} class="card-action">{actionLabel}</a>
		{:else}
			<button class="card-action" onclick={onAction}>{actionLabel}</button>
		{/if}
	{/if}

	{#if children}
		{@render children()}
	{/if}
</div>

<style>
	.dashboard-card {
		background: white;
		border-radius: var(--radius-xl);
		padding: var(--spacing-5);
		box-shadow: var(--shadow-md3-1);
		display: flex;
		flex-direction: column;
		gap: var(--spacing-3);
		min-width: 160px;
	}

	.card-icon {
		width: 40px;
		height: 40px;
		border-radius: var(--radius-md);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.card-icon svg {
		width: 20px;
		height: 20px;
	}

	.card-icon.money {
		background: var(--color-success-100);
		color: var(--color-success-600);
	}

	.card-icon.vacation {
		background: var(--color-primary-100);
		color: var(--color-primary-600);
	}

	.card-icon.sick {
		background: var(--color-warning-100);
		color: var(--color-warning-600);
	}

	.card-content {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.card-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	.card-value {
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-900);
	}

	.card-subvalue {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.card-action {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-primary-500);
		text-decoration: none;
		background: none;
		border: none;
		padding: 0;
		cursor: pointer;
		text-align: left;
		transition: color var(--transition-fast);
	}

	.card-action:hover {
		color: var(--color-primary-600);
		text-decoration: underline;
	}
</style>

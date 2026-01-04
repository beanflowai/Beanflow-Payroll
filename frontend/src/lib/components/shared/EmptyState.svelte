<script lang="ts">
	/**
	 * EmptyState - Reusable empty state component
	 * Displays a friendly message when there's no data
	 */
	import type { Snippet } from 'svelte';

	interface Props {
		icon?: string;
		title: string;
		description?: string;
		actionLabel?: string;
		onAction?: () => void;
		variant?: 'default' | 'compact' | 'card';
		children?: Snippet;
	}

	let {
		icon = 'fa-inbox',
		title,
		description,
		actionLabel,
		onAction,
		variant = 'default',
		children
	}: Props = $props();
</script>

<div class="empty-state" class:compact={variant === 'compact'} class:card={variant === 'card'}>
	<div class="empty-icon">
		<i class="fas {icon}"></i>
	</div>
	<h3 class="empty-title">{title}</h3>
	{#if description}
		<p class="empty-description">{description}</p>
	{/if}
	{#if children}
		<div class="empty-content">
			{@render children()}
		</div>
	{/if}
	{#if actionLabel && onAction}
		<button class="empty-action" onclick={onAction}>
			{actionLabel}
		</button>
	{/if}
</div>

<style>
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-10);
		text-align: center;
	}

	.empty-state.compact {
		padding: var(--spacing-6);
	}

	.empty-state.card {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
	}

	.empty-icon {
		width: 64px;
		height: 64px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--color-surface-100);
		border-radius: 50%;
		margin-bottom: var(--spacing-4);
	}

	.empty-icon i {
		font-size: 24px;
		color: var(--color-surface-400);
	}

	.compact .empty-icon {
		width: 48px;
		height: 48px;
	}

	.compact .empty-icon i {
		font-size: 18px;
	}

	.empty-title {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-700);
		margin: 0 0 var(--spacing-2);
	}

	.compact .empty-title {
		font-size: var(--font-size-body-content);
	}

	.empty-description {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-500);
		margin: 0 0 var(--spacing-4);
		max-width: 400px;
	}

	.compact .empty-description {
		font-size: var(--font-size-body-small);
		margin-bottom: var(--spacing-3);
	}

	.empty-content {
		margin-bottom: var(--spacing-4);
	}

	.empty-action {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		background: var(--color-primary-500);
		color: white;
		border: none;
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.empty-action:hover {
		background: var(--color-primary-600);
	}

	.compact .empty-action {
		padding: var(--spacing-1) var(--spacing-3);
		font-size: var(--font-size-body-small);
	}
</style>

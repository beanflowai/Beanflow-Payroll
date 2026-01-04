<script lang="ts">
	/**
	 * AlertBanner - Reusable alert/notification banner
	 * For displaying success, error, warning, and info messages
	 */
	import type { Snippet } from 'svelte';

	interface Props {
		type?: 'success' | 'error' | 'warning' | 'info';
		title?: string;
		message?: string;
		dismissible?: boolean;
		onDismiss?: () => void;
		class?: string;
		children?: Snippet;
	}

	let {
		type = 'info',
		title,
		message,
		dismissible = false,
		onDismiss,
		class: className = '',
		children
	}: Props = $props();

	const icons = {
		success: 'fa-check-circle',
		error: 'fa-exclamation-circle',
		warning: 'fa-exclamation-triangle',
		info: 'fa-info-circle'
	};
</script>

<div class="alert-banner {type} {className}" role="alert">
	<div class="alert-icon">
		<i class="fas {icons[type]}"></i>
	</div>
	<div class="alert-content">
		{#if title}
			<p class="alert-title">{title}</p>
		{/if}
		{#if message}
			<p class="alert-message">{message}</p>
		{/if}
		{#if children}
			<div class="alert-body">
				{@render children()}
			</div>
		{/if}
	</div>
	{#if dismissible && onDismiss}
		<button class="alert-dismiss" onclick={onDismiss} aria-label="Dismiss">
			<i class="fas fa-times"></i>
		</button>
	{/if}
</div>

<style>
	.alert-banner {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-3);
		padding: var(--spacing-3) var(--spacing-4);
		border-radius: var(--radius-lg);
		border: 1px solid;
	}

	/* Type variants */
	.alert-banner.success {
		background: var(--color-tertiary-50);
		border-color: var(--color-tertiary-200);
	}

	.alert-banner.success .alert-icon {
		color: var(--color-tertiary-600);
	}

	.alert-banner.success .alert-title {
		color: var(--color-tertiary-800);
	}

	.alert-banner.error {
		background: var(--color-error-50);
		border-color: var(--color-error-200);
	}

	.alert-banner.error .alert-icon {
		color: var(--color-error-600);
	}

	.alert-banner.error .alert-title {
		color: var(--color-error-800);
	}

	.alert-banner.warning {
		background: #fef3c7;
		border-color: #fcd34d;
	}

	.alert-banner.warning .alert-icon {
		color: #d97706;
	}

	.alert-banner.warning .alert-title {
		color: #92400e;
	}

	.alert-banner.info {
		background: var(--color-primary-50);
		border-color: var(--color-primary-200);
	}

	.alert-banner.info .alert-icon {
		color: var(--color-primary-600);
	}

	.alert-banner.info .alert-title {
		color: var(--color-primary-800);
	}

	.alert-icon {
		flex-shrink: 0;
		font-size: 18px;
		margin-top: 1px;
	}

	.alert-content {
		flex: 1;
		min-width: 0;
	}

	.alert-title {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		margin: 0;
		line-height: 1.4;
	}

	.alert-message {
		font-size: var(--font-size-body-small);
		color: var(--color-surface-600);
		margin: var(--spacing-1) 0 0;
		line-height: 1.5;
	}

	.alert-body {
		margin-top: var(--spacing-2);
	}

	.alert-dismiss {
		flex-shrink: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		background: transparent;
		border: none;
		border-radius: var(--radius-sm);
		color: var(--color-surface-500);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.alert-dismiss:hover {
		background: rgba(0, 0, 0, 0.05);
		color: var(--color-surface-700);
	}
</style>

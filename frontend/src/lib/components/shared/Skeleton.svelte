<script lang="ts">
	/**
	 * Skeleton - Reusable loading placeholder component
	 * Creates animated skeleton placeholders for loading states
	 */

	interface Props {
		variant?: 'text' | 'circular' | 'rectangular' | 'rounded';
		width?: string;
		height?: string;
		lines?: number;
		class?: string;
	}

	let { variant = 'text', width, height, lines = 1, class: className = '' }: Props = $props();

	const variantStyles = {
		text: 'skeleton-text',
		circular: 'skeleton-circular',
		rectangular: 'skeleton-rectangular',
		rounded: 'skeleton-rounded'
	};
</script>

{#if lines > 1}
	<div class="skeleton-lines">
		{#each Array(lines) as _unused, i (i)}
			<div
				class="skeleton {variantStyles[variant]} {className}"
				class:last-line={i === lines - 1}
				style:width={i === lines - 1 ? '70%' : width}
				style:height
			></div>
		{/each}
	</div>
{:else}
	<div class="skeleton {variantStyles[variant]} {className}" style:width style:height></div>
{/if}

<style>
	.skeleton {
		background: linear-gradient(
			90deg,
			var(--color-surface-200) 25%,
			var(--color-surface-100) 50%,
			var(--color-surface-200) 75%
		);
		background-size: 200% 100%;
		animation: shimmer 1.5s infinite ease-in-out;
	}

	@keyframes shimmer {
		0% {
			background-position: 200% 0;
		}
		100% {
			background-position: -200% 0;
		}
	}

	.skeleton-text {
		height: 1em;
		border-radius: var(--radius-sm);
		width: 100%;
	}

	.skeleton-circular {
		width: 40px;
		height: 40px;
		border-radius: 50%;
	}

	.skeleton-rectangular {
		width: 100%;
		height: 100px;
		border-radius: 0;
	}

	.skeleton-rounded {
		width: 100%;
		height: 100px;
		border-radius: var(--radius-lg);
	}

	.skeleton-lines {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.skeleton-lines .last-line {
		width: 70%;
	}
</style>

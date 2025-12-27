<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		content: string;
		children: Snippet;
		position?: 'top' | 'bottom' | 'left' | 'right';
	}

	let { content, children, position = 'top' }: Props = $props();
	let isVisible = $state(false);

	// Generate unique ID for accessibility
	const tooltipId = `tooltip-${Math.random().toString(36).slice(2, 9)}`;
</script>

<div
	class="tooltip-wrapper"
	aria-describedby={isVisible && content ? tooltipId : undefined}
	onmouseenter={() => (isVisible = true)}
	onmouseleave={() => (isVisible = false)}
	onfocus={() => (isVisible = true)}
	onblur={() => (isVisible = false)}
>
	{@render children()}
	{#if isVisible && content}
		<div id={tooltipId} role="tooltip" class="tooltip-content {position}">
			{content}
			<span class="tooltip-arrow"></span>
		</div>
	{/if}
</div>

<style>
	.tooltip-wrapper {
		position: relative;
		display: block;
		width: 100%;
		height: 100%;
		cursor: help;
	}

	.tooltip-content {
		position: absolute;
		z-index: 1000;
		padding: var(--spacing-2) var(--spacing-3);
		background: var(--color-surface-800);
		color: white;
		font-size: var(--font-size-auxiliary-text);
		line-height: 1.4;
		border-radius: var(--radius-md);
		white-space: normal;
		max-width: 280px;
		pointer-events: none;
		box-shadow: var(--shadow-md3-2);
	}

	.tooltip-arrow {
		position: absolute;
		width: 8px;
		height: 8px;
		background: var(--color-surface-800);
		transform: rotate(45deg);
	}

	/* Top position (default) */
	.tooltip-content.top {
		bottom: calc(100% + 8px);
		left: 50%;
		transform: translateX(-50%);
	}

	.tooltip-content.top .tooltip-arrow {
		bottom: -4px;
		left: 50%;
		transform: translateX(-50%) rotate(45deg);
	}

	/* Bottom position */
	.tooltip-content.bottom {
		top: calc(100% + 8px);
		left: 50%;
		transform: translateX(-50%);
	}

	.tooltip-content.bottom .tooltip-arrow {
		top: -4px;
		left: 50%;
		transform: translateX(-50%) rotate(45deg);
	}

	/* Left position */
	.tooltip-content.left {
		right: calc(100% + 8px);
		top: 50%;
		transform: translateY(-50%);
	}

	.tooltip-content.left .tooltip-arrow {
		right: -4px;
		top: 50%;
		transform: translateY(-50%) rotate(45deg);
	}

	/* Right position */
	.tooltip-content.right {
		left: calc(100% + 8px);
		top: 50%;
		transform: translateY(-50%);
	}

	.tooltip-content.right .tooltip-arrow {
		left: -4px;
		top: 50%;
		transform: translateY(-50%) rotate(45deg);
	}
</style>

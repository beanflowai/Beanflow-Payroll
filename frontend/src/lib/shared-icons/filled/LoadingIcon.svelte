<script lang="ts">
	import type { BaseIconProps } from '../types';

	let {
		size = 20,
		color = 'currentColor',
		class: className = '',
		ariaLabel,
		ariaHidden = false,
		...restProps
	}: BaseIconProps = $props();
</script>

<div
	class="icon-loading {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Loading'}
	aria-hidden={ariaHidden}
	role="img"
	{...restProps}
>
	<svg
		width={size}
		height={size}
		viewBox="0 0 20 20"
		fill="none"
		xmlns="http://www.w3.org/2000/svg"
	>
		<path fill={color} d="M10 3a1 1 0 0 1 1 1v5a1 1 0 1 1-2 0V4a1 1 0 0 1 1-1Z" />
		<path
			fill={color}
			d="M13.5 6.5a1 1 0 0 1 0 1.414L10.414 11A1 1 0 0 1 9 11V7a1 1 0 0 1 1.414-.586L13.5 6.5Z"
		/>
		<circle
			cx="10"
			cy="10"
			r="7"
			stroke={color}
			stroke-width="2"
			fill="none"
			stroke-dasharray="4 2"
			opacity="0.3"
		/>
	</svg>
</div>

<style>
	.icon-loading {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		from {
			transform: rotate(0deg);
		}
		to {
			transform: rotate(360deg);
		}
	}
</style>

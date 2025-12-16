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
	class="icon-dashboard {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Dashboard'}
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
		<path
			fill={color}
			d="M3 4a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v5a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V4ZM12 3a1 1 0 0 0-1 1v2a1 1 0 0 0 1 1h3a1 1 0 0 0 1-1V4a1 1 0 0 0-1-1h-3ZM11 9a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1h-3a1 1 0 0 1-1-1V9ZM3 12a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1v-4Z"
		/>
	</svg>
</div>

<style>
	.icon-dashboard {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

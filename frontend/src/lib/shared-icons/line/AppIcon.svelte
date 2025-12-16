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
	class="icon-app {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'App'}
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
		<rect x="3" y="3" width="6.5" height="6.5" rx="1" stroke={color} stroke-width="1.5" />
		<rect x="10.5" y="3" width="6.5" height="6.5" rx="1" stroke={color} stroke-width="1.5" />
		<rect x="3" y="10.5" width="6.5" height="6.5" rx="1" stroke={color} stroke-width="1.5" />
		<rect x="10.5" y="10.5" width="6.5" height="6.5" rx="1" stroke={color} stroke-width="1.5" />
	</svg>
</div>

<style>
	.icon-app {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

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
	class="icon-pause {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Pause'}
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
		<rect x="6" y="4" width="3" height="12" rx="0.5" stroke={color} stroke-width="1.5" />
		<rect x="11" y="4" width="3" height="12" rx="0.5" stroke={color} stroke-width="1.5" />
	</svg>
</div>

<style>
	.icon-pause {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

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
	class="icon-checkbox {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Checkbox'}
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
		<rect x="3" y="3" width="14" height="14" rx="2" stroke={color} stroke-width="2" fill="none" />
	</svg>
</div>

<style>
	.icon-checkbox {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

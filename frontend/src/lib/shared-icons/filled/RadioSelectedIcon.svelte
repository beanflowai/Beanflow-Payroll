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
	class="icon-radio-selected {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Radio Selected'}
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
		<circle cx="10" cy="10" r="7" fill={color} />
		<circle cx="10" cy="10" r="3" fill="white" />
	</svg>
</div>

<style>
	.icon-radio-selected {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

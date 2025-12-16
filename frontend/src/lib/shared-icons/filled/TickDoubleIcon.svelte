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
	class="icon-tick-double {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Tick Double'}
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
			d="M16 6L8 14L4 10"
			stroke={color}
			stroke-width="2"
			stroke-linecap="round"
			stroke-linejoin="round"
			fill="none"
		/>
		<path
			d="M16 10L12 14L10 12"
			stroke={color}
			stroke-width="2"
			stroke-linecap="round"
			stroke-linejoin="round"
			fill="none"
		/>
	</svg>
</div>

<style>
	.icon-tick-double {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

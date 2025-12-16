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
	class="icon-bluetooth {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Bluetooth'}
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
			d="M10.3125 2.5L15.3125 7.5L10.3125 12.5L15.3125 17.5"
			fill={color}
			stroke={color}
			stroke-width="0.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<path
			d="M15.3125 7.5L7.8125 12.5M15.3125 12.5L7.8125 7.5"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-bluetooth {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

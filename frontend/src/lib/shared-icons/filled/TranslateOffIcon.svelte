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
	class="icon-translate-off {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Translate Off'}
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
		<rect
			x="3.125"
			y="3.125"
			width="8.125"
			height="8.125"
			rx="1.25"
			fill={color}
			stroke={color}
			stroke-width="0.5"
		/>
		<rect
			x="8.75"
			y="8.75"
			width="8.125"
			height="8.125"
			rx="1.25"
			fill={color}
			stroke={color}
			stroke-width="0.5"
		/>
		<path
			d="M5.3125 5.3125H9.0625M7.1875 3.75V11.25M3.75 7.1875H10.625"
			stroke="white"
			stroke-width="1"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<path
			d="M11.25 11.25L14.375 15.3125M11.25 15.3125H16.25M13.125 11.25V16.875"
			stroke="white"
			stroke-width="1"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<path
			d="M2.5 2.5L17.5 17.5"
			stroke="white"
			stroke-width="2"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-translate-off {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

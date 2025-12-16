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
	class="icon-wifi-off {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'WiFi Off'}
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
			d="M2.8125 7.1875C4.0625 5.9375 5.625 5.125 7.1875 4.6875"
			fill={color}
			stroke={color}
			stroke-width="0.5"
			stroke-linecap="round"
		/>
		<path
			d="M17.1875 7.1875C15.9375 5.9375 14.375 5.125 12.8125 4.6875"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
		/>
		<path
			d="M5.3125 9.6875C6.5625 8.4375 8.125 7.8125 10 7.8125"
			fill={color}
			stroke={color}
			stroke-width="0.5"
			stroke-linecap="round"
		/>
		<path
			d="M14.6875 9.6875C13.4375 8.4375 11.875 7.8125 10 7.8125"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
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
	.icon-wifi-off {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

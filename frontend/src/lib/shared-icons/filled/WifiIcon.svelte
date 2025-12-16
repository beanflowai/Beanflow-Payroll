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
	class="icon-wifi {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'WiFi'}
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
			d="M2.8125 7.1875C7.1875 2.8125 12.8125 2.8125 17.1875 7.1875"
			fill={color}
			stroke={color}
			stroke-width="0.5"
			stroke-linecap="round"
		/>
		<path
			d="M5.3125 9.6875C8.4375 6.5625 11.5625 6.5625 14.6875 9.6875"
			fill={color}
			stroke={color}
			stroke-width="0.5"
			stroke-linecap="round"
		/>
		<path
			d="M7.8125 12.1875C9.6875 10.3125 10.3125 10.3125 12.1875 12.1875"
			fill={color}
			stroke={color}
			stroke-width="0.5"
			stroke-linecap="round"
		/>
		<circle cx="10" cy="15.625" r="1.5625" fill={color} stroke={color} stroke-width="0.5" />
	</svg>
</div>

<style>
	.icon-wifi {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

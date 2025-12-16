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
	class="icon-eye-off {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Eye Off'}
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
			d="M10 3.125C6.25 3.125 3.125 6.25 1.25 10C2.1875 11.875 3.4375 13.4375 5 14.5313"
			fill={color}
			stroke={color}
			stroke-width="0.5"
		/>
		<path
			d="M15 14.5313C16.5625 13.4375 17.8125 11.875 18.75 10C17.8125 8.125 16.5625 6.5625 15 5.46875"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
		/>
		<circle cx="10" cy="10" r="3.125" fill={color} stroke={color} stroke-width="0.5" />
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
	.icon-eye-off {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

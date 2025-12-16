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
	class="icon-mic-off {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Microphone Off'}
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
			d="M10 11.875C11.7259 11.875 13.125 10.4759 13.125 8.75V5.625C13.125 3.89911 11.7259 2.5 10 2.5C9.4375 2.5 8.90625 2.65625 8.4375 2.9375"
			fill={color}
			stroke={color}
			stroke-width="0.5"
		/>
		<path
			d="M6.875 8.75C6.875 10.4759 8.27411 11.875 10 11.875C10.3125 11.875 10.625 11.8281 10.9375 11.7188"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
		/>
		<path
			d="M5.3125 9.6875H3.75C3.75 13.1283 6.55922 15.9375 10 15.9375C10.625 15.9375 11.2188 15.8438 11.7813 15.6875"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
		/>
		<path d="M10 15.9375V17.5" stroke={color} stroke-width="1.5" stroke-linecap="round" />
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
	.icon-mic-off {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

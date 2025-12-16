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
	class="icon-video-off {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Video Off'}
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
			y="5.625"
			width="11.25"
			height="8.75"
			rx="1.25"
			fill={color}
			stroke={color}
			stroke-width="0.5"
		/>
		<path
			d="M14.375 8.125L17.5 6.25V13.75L14.375 11.875"
			fill={color}
			stroke={color}
			stroke-width="0.5"
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
	.icon-video-off {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

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
	class="icon-picture {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Picture'}
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
			x="2.5"
			y="4.375"
			width="15"
			height="11.25"
			rx="1.25"
			fill={color}
			stroke={color}
			stroke-width="0.5"
		/>
		<circle cx="7.5" cy="8.75" r="1.25" fill="white" stroke="white" stroke-width="0.5" />
		<path
			d="M4.375 13.125L7.5 10L10 12.5L14.375 8.125L17.5 11.25"
			stroke="white"
			stroke-width="1"
			stroke-linecap="round"
			stroke-linejoin="round"
			fill="none"
		/>
	</svg>
</div>

<style>
	.icon-picture {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

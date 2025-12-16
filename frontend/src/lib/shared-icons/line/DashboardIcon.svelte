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
	class="icon-dashboard {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Dashboard icon'}
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
			x="2"
			y="3"
			width="7"
			height="8"
			rx="1"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<rect
			x="11"
			y="3"
			width="7"
			height="4"
			rx="1"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<rect
			x="11"
			y="9"
			width="7"
			height="8"
			rx="1"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<rect
			x="2"
			y="13"
			width="7"
			height="4"
			rx="1"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-dashboard {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

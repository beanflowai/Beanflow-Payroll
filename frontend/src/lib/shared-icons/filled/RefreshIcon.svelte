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
	class="icon-refresh {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Refresh'}
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
			d="M10 2.5C5.85786 2.5 2.5 5.85786 2.5 10C2.5 12.2321 3.44643 14.2321 4.9375 15.5625M17.5 10C17.5 14.1421 14.1421 17.5 10 17.5C8.67857 17.5 7.46429 17.0893 6.4375 16.375"
			fill={color}
			stroke={color}
			stroke-width="0.5"
			stroke-linecap="round"
		/>
		<path
			d="M2.1875 11.5625V4.9375H8.8125"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<path
			d="M17.8125 8.4375V15.0625H11.1875"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-refresh {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

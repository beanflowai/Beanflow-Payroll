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
	class="icon-link {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Link'}
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
			d="M8.75 11.25L4.375 15.625C3.75 16.25 2.8125 16.25 2.1875 15.625C1.5625 15 1.5625 14.0625 2.1875 13.4375L5.3125 10.3125"
			fill={color}
			stroke={color}
			stroke-width="0.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<path
			d="M11.25 8.75L15.625 4.375C16.25 3.75 17.1875 3.75 17.8125 4.375C18.4375 5 18.4375 5.9375 17.8125 6.5625L14.6875 9.6875"
			fill={color}
			stroke={color}
			stroke-width="0.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<circle cx="7.5" cy="12.5" r="2.1875" fill={color} stroke={color} stroke-width="0.5" />
		<circle cx="12.5" cy="7.5" r="2.1875" fill={color} stroke={color} stroke-width="0.5" />
	</svg>
</div>

<style>
	.icon-link {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

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
	class="icon-like {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Like'}
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
			d="M10 17.5C10 17.5 2.5 13.75 2.5 8.125C2.5 6.5625 3.75 5.3125 5.3125 5.3125C6.5625 5.3125 7.5 6.25 8.125 7.5C8.75 6.25 9.6875 5.3125 10.9375 5.3125C12.5 5.3125 13.75 6.5625 13.75 8.125C13.75 13.75 10 17.5 10 17.5Z"
			fill={color}
			stroke={color}
			stroke-width="0.5"
		/>
		<circle cx="15.625" cy="5.625" r="2.5" fill={color} stroke={color} stroke-width="0.5" />
	</svg>
</div>

<style>
	.icon-like {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

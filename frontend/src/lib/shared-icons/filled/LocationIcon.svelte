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
	class="icon-location {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Location'}
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
			d="M10 2.5C7.23858 2.5 5 4.73858 5 7.5C5 11.875 10 17.5 10 17.5C10 17.5 15 11.875 15 7.5C15 4.73858 12.7614 2.5 10 2.5Z"
			fill={color}
			stroke={color}
			stroke-width="0.5"
		/>
		<circle cx="10" cy="7.5" r="2.1875" fill="white" stroke="white" stroke-width="0.5" />
	</svg>
</div>

<style>
	.icon-location {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

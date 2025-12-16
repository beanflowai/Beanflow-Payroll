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
	class="icon-eye {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Eye'}
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
			d="M10 3.125C6.25 3.125 3.125 6.25 1.25 10C3.125 13.75 6.25 16.875 10 16.875C13.75 16.875 16.875 13.75 18.75 10C16.875 6.25 13.75 3.125 10 3.125Z"
			fill={color}
			stroke={color}
			stroke-width="0.5"
		/>
		<circle cx="10" cy="10" r="3.125" fill="white" stroke="white" stroke-width="0.5" />
		<circle cx="10" cy="10" r="1.25" fill={color} stroke={color} stroke-width="0.5" />
	</svg>
</div>

<style>
	.icon-eye {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

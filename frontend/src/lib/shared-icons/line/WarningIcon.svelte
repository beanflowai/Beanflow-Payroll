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
	class="icon-warning {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Warning icon'}
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
			d="M10 2L2 17H18L10 2Z"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<path
			d="M10 8V11"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<circle cx="10" cy="14" r="0.5" fill={color} />
	</svg>
</div>

<style>
	.icon-warning {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

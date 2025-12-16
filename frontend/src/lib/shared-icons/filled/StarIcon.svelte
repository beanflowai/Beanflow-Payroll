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
	class="icon-star {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Star'}
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
			d="M10 1.875L12.125 7.125H17.875L13.375 10.625L15.5 15.875L10 12.375L4.5 15.875L6.625 10.625L2.125 7.125H7.875L10 1.875Z"
			fill={color}
			stroke={color}
			stroke-width="0.5"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-star {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

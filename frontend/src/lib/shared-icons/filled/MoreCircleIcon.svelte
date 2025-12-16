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
	class="icon-more-circle {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'More Circle'}
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
			fill-rule="evenodd"
			clip-rule="evenodd"
			fill={color}
			d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16ZM7 9a1 1 0 1 1 0 2 1 1 0 0 1 0-2Zm3 1a1 1 0 1 0 2 0 1 1 0 0 0-2 0Zm5-1a1 1 0 1 1 0 2 1 1 0 0 1 0-2Z"
		/>
	</svg>
</div>

<style>
	.icon-more-circle {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

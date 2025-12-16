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
	class="icon-more {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'More'}
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
			d="M5 10a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0ZM11.5 10a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0ZM18 10a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0Z"
			fill={color}
		/>
	</svg>
</div>

<style>
	.icon-more {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

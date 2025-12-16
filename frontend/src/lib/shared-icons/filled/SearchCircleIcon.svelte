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
	class="icon-search-circle {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'SearchCircle'}
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
			d="M8 16a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm0-2a6 6 0 1 0 0-12 6 6 0 0 0 0 12Zm7.707 2.293a1 1 0 0 1-1.414 1.414l-3-3a1 1 0 0 1 1.414-1.414l3 3ZM10 7a1 1 0 1 1 0 2 1 1 0 0 1 0-2Z"
		/>
	</svg>
</div>

<style>
	.icon-search-circle {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

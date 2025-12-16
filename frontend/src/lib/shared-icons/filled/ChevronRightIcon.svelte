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
	class="icon-chevron-right {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Chevron Right'}
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
			d="M8.21967 4.21967C8.51256 3.92678 8.98744 3.92678 9.28033 4.21967L14.7803 9.71967C15.0732 10.0126 15.0732 10.4874 14.7803 10.7803L9.28033 16.2803C8.98744 16.5732 8.51256 16.5732 8.21967 16.2803C7.92678 15.9874 7.92678 15.5126 8.21967 15.2197L12.9393 10L8.21967 4.78033C7.92678 4.48744 7.92678 4.01256 8.21967 3.71967Z"
		/>
	</svg>
</div>

<style>
	.icon-chevron-right {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

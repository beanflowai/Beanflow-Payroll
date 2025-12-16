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
	class="icon-chevron-up {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Chevron Up'}
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
			d="M14.7803 11.7803C15.0732 11.4874 15.0732 11.0126 14.7803 10.7197L9.28033 5.21967C8.98744 4.92678 8.51256 4.92678 8.21967 5.21967L2.71967 10.7197C2.42678 11.0126 2.42678 11.4874 2.71967 11.7803C3.01256 12.0732 3.48744 12.0732 3.78033 11.7803L8.75 6.81066L13.7197 11.7803C14.0126 12.0732 14.4874 12.0732 14.7803 11.7803Z"
		/>
	</svg>
</div>

<style>
	.icon-chevron-up {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

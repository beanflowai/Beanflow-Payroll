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
	class="icon-close {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Close'}
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
			d="M4.21967 4.21967C4.51256 3.92678 4.98744 3.92678 5.28033 4.21967L10 8.93934L14.7197 4.21967C15.0126 3.92678 15.4874 3.92678 15.7803 4.21967C16.0732 4.51256 16.0732 4.98744 15.7803 5.28033L11.0607 10L15.7803 14.7197C16.0732 15.0126 16.0732 15.4874 15.7803 15.7803C15.4874 16.0732 15.0126 16.0732 14.7197 15.7803L10 11.0607L5.28033 15.7803C4.98744 16.0732 4.51256 16.0732 4.21967 15.7803C3.92678 15.4874 3.92678 15.0126 4.21967 14.7197L8.93934 10L4.21967 5.28033C3.92678 4.98744 3.92678 4.51256 4.21967 4.21967Z"
		/>
	</svg>
</div>

<style>
	.icon-close {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

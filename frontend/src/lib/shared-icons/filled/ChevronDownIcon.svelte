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
	class="icon-chevron-down {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Chevron Down'}
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
			d="M5.21967 8.21967C4.92678 8.51256 4.92678 8.98744 5.21967 9.28033L10.7197 14.7803C11.0126 15.0732 11.4874 15.0732 11.7803 14.7803L17.2803 9.28033C17.5732 8.98744 17.5732 8.51256 17.2803 8.21967C16.9874 7.92678 16.5126 7.92678 16.2197 8.21967L11.25 13.1893L6.28033 8.21967C5.98744 7.92678 5.51256 7.92678 5.21967 8.21967Z"
		/>
	</svg>
</div>

<style>
	.icon-chevron-down {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

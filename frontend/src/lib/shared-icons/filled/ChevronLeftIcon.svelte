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
	class="icon-chevron-left {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Chevron Left'}
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
			d="M11.7803 4.21967C12.0732 4.51256 12.0732 4.98744 11.7803 5.28033L7.06066 10L11.7803 14.7197C12.0732 15.0126 12.0732 15.4874 11.7803 15.7803C11.4874 16.0732 11.0126 16.0732 10.7197 15.7803L5.21967 10.2803C4.92678 9.98744 4.92678 9.51256 5.21967 9.21967L10.7197 4.21967C11.0126 3.92678 11.4874 3.92678 11.7803 4.21967Z"
		/>
	</svg>
</div>

<style>
	.icon-chevron-left {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

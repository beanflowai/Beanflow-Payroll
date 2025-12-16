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
	class="icon-file {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'File'}
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
			d="M4 4a2 2 0 0 1 2-2h4.586a2 2 0 0 1 1.414.586l3.414 3.414A2 2 0 0 1 16 8.414V16a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4Zm2-1a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V9h-3a2 2 0 0 1-2-2V4H6Zm5 1.414V7h1.586L11 5.414Z"
		/>
	</svg>
</div>

<style>
	.icon-file {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

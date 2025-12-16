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
	class="icon-copy {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Copy'}
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
			d="M8 3a1 1 0 0 1 1-1h7a1 1 0 0 1 1 1v7a1 1 0 1 1-2 0V4h-6a1 1 0 0 1-1-1Zm0 4a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h7a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2H8Z"
		/>
	</svg>
</div>

<style>
	.icon-copy {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

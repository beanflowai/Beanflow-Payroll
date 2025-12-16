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
	class="icon-picture-2 {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Picture 2'}
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
			d="M3 4C3 3.44772 3.44772 3 4 3H16C16.5523 3 17 3.44772 17 4V16C17 16.5523 16.5523 17 16 17H4C3.44772 17 3 16.5523 3 16V4ZM4 4V16H16V4H4Z"
		/>
		<circle cx="6.5" cy="6.5" r="1.5" fill={color} />
		<path fill={color} d="M5 12L8 9L10 11L14 7L16 9V15H5V12Z" />
	</svg>
</div>

<style>
	.icon-picture-2 {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

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
	aria-label={ariaLabel || 'File icon'}
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
			d="M5 3H11L16 8V17C16 17.5523 15.5523 18 15 18H5C4.44772 18 4 17.5523 4 17V4C4 3.44772 4.44772 3 5 3Z"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<path
			d="M11 3V8H16"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
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

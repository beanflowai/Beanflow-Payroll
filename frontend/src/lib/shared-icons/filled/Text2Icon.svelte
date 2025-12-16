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
	class="icon-text-2 {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Text 2'}
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
			d="M2 3C2 2.44772 2.44772 2 3 2H7C7.55228 2 8 2.44772 8 3V17C8 17.5523 7.55228 18 7 18C6.44772 18 6 17.5523 6 17V4H4V17C4 17.5523 3.55228 18 3 18C2.44772 18 2 17.5523 2 17V3Z"
		/>
		<path
			fill-rule="evenodd"
			clip-rule="evenodd"
			fill={color}
			d="M10 3C10 2.44772 10.4477 2 11 2H13C13.5523 2 14 2.44772 14 3V17C14 17.5523 13.5523 18 13 18H11C10.4477 18 10 17.5523 10 17V3ZM12 4V16H12V4Z"
		/>
		<path
			fill-rule="evenodd"
			clip-rule="evenodd"
			fill={color}
			d="M16 3C16 2.44772 16.4477 2 17 2C17.5523 2 18 2.44772 18 3V17C18 17.5523 17.5523 18 17 18C16.4477 18 16 17.5523 16 17V3Z"
		/>
	</svg>
</div>

<style>
	.icon-text-2 {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

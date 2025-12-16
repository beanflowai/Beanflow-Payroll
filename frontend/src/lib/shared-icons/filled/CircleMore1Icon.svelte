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
	class="icon-circle-more-1 {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Circle More 1'}
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
			d="M10 18C14.4183 18 18 14.4183 18 10C18 5.58172 14.4183 2 10 2C5.58172 2 2 5.58172 2 10C2 14.4183 5.58172 18 10 18ZM6 10C6 9.44772 6.44772 9 7 9C7.55228 9 8 9.44772 8 10C8 10.5523 7.55228 11 7 11C6.44772 11 6 10.5523 6 10ZM9 10C9 9.44772 9.44772 9 10 9C10.5523 9 11 9.44772 11 10C11 10.5523 10.5523 11 10 11C9.44772 11 9 10.5523 9 10ZM12 10C12 9.44772 12.4477 9 13 9C13.5523 9 14 9.44772 14 10C14 10.5523 13.5523 11 13 11C12.4477 11 12 10.5523 12 10Z"
		/>
	</svg>
</div>

<style>
	.icon-circle-more-1 {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

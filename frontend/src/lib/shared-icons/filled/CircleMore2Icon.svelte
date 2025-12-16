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
	class="icon-circle-more-2 {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Circle More 2'}
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
			d="M10 18C14.4183 18 18 14.4183 18 10C18 5.58172 14.4183 2 10 2C5.58172 2 2 5.58172 2 10C2 14.4183 5.58172 18 10 18ZM10 9C10.5523 9 11 9.44772 11 10C11 10.5523 10.5523 11 10 11C9.44772 11 9 10.5523 9 10C9 9.44772 9.44772 9 10 9ZM14 10C14 9.44772 13.5523 9 13 9C12.4477 9 12 9.44772 12 10C12 10.5523 12.4477 11 13 11C13.5523 11 14 10.5523 14 10ZM7 10C7 9.44772 6.55228 9 6 9C5.44772 9 5 9.44772 5 10C5 10.5523 5.44772 11 6 11C6.55228 11 7 10.5523 7 10Z"
		/>
	</svg>
</div>

<style>
	.icon-circle-more-2 {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

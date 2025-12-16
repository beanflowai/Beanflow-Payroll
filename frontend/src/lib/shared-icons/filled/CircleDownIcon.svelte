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
	class="icon-circle-down {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Circle Down'}
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
			d="M10 18C14.4183 18 18 14.4183 18 10C18 5.58172 14.4183 2 10 2C5.58172 2 2 5.58172 2 10C2 14.4183 5.58172 18 10 18ZM13.865 8.91C14.1579 8.61707 14.6328 8.61707 14.9257 8.91C15.2186 9.20289 15.2186 9.67777 14.9257 9.97066L10.5303 14.3661C10.2374 14.659 9.76256 14.659 9.46967 14.3661L5.07425 9.97066C4.78136 9.67777 4.78136 9.20289 5.07425 8.91C5.36714 8.61707 5.84201 8.61707 6.13491 8.91L9.25 12.025V4.5C9.25 4.08579 9.58579 3.75 10 3.75C10.4142 3.75 10.75 4.08579 10.75 4.5V12.025L13.865 8.91Z"
		/>
	</svg>
</div>

<style>
	.icon-circle-down {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

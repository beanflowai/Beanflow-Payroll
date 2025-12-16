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
	class="icon-down {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Down'}
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
			d="M10 3.75C10.4142 3.75 10.75 4.08579 10.75 4.5V13.025L13.865 9.91C14.1579 9.61707 14.6328 9.61707 14.9257 9.91C15.2186 10.2029 15.2186 10.6778 14.9257 10.9707L10.5303 15.3661C10.2374 15.659 9.76256 15.659 9.46967 15.3661L5.07425 10.9707C4.78136 10.6778 4.78136 10.2029 5.07425 9.91C5.36714 9.61707 5.84201 9.61707 6.13491 9.91L9.25 13.025V4.5C9.25 4.08579 9.58579 3.75 10 3.75Z"
		/>
	</svg>
</div>

<style>
	.icon-down {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

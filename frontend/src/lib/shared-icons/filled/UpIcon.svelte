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
	class="icon-up {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Up'}
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
			d="M10 16.25C9.58579 16.25 9.25 15.9142 9.25 15.5L9.25 6.97502L6.13491 10.09C5.84201 10.3829 5.36714 10.3829 5.07425 10.09C4.78136 9.79708 4.78136 9.32221 5.07425 9.02932L9.46967 4.6339C9.76256 4.34101 10.2374 4.34101 10.5303 4.6339L14.9257 9.02932C15.2186 9.32221 15.2186 9.79708 14.9257 10.09C14.6328 10.3829 14.1579 10.3829 13.865 10.09L10.75 6.97502V15.5C10.75 15.9142 10.4142 16.25 10 16.25Z"
		/>
	</svg>
</div>

<style>
	.icon-up {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

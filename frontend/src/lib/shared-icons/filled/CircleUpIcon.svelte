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
	class="icon-circle-up {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Circle Up'}
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
			d="M10 2C14.4183 2 18 5.58172 18 10C18 14.4183 14.4183 18 10 18C5.58172 18 2 14.4183 2 10C2 5.58172 5.58172 2 10 2ZM6.13491 11.09C5.84201 11.3829 5.36714 11.3829 5.07425 11.09C4.78136 10.7971 4.78136 10.3222 5.07425 10.0293L9.46967 5.6339C9.76256 5.34101 10.2374 5.34101 10.5303 5.6339L14.9257 10.0293C15.2186 10.3222 15.2186 10.7971 14.9257 11.09C14.6328 11.3829 14.1579 11.3829 13.865 11.09L10.75 7.97502V15.5C10.75 15.9142 10.4142 16.25 10 16.25C9.58579 16.25 9.25 15.9142 9.25 15.5V7.97502L6.13491 11.09Z"
		/>
	</svg>
</div>

<style>
	.icon-circle-up {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

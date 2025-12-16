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
	class="icon-user {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'User'}
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
			d="M10 10C12.7614 10 15 7.76142 15 5C15 2.23858 12.7614 0 10 0C7.23858 0 5 2.23858 5 5C5 7.76142 7.23858 10 10 10Z"
			fill={color}
		/>
		<path
			d="M10 12.5C5.85786 12.5 2.5 15.8579 2.5 20H17.5C17.5 15.8579 14.1421 12.5 10 12.5Z"
			fill={color}
		/>
	</svg>
</div>

<style>
	.icon-user {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

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
	class="icon-search-1 {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Search 1'}
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
			d="M8.75 3.75C5.8505 3.75 3.5 6.1005 3.5 9C3.5 11.8995 5.8505 14.25 8.75 14.25C11.6495 14.25 14 11.8995 14 9C14 6.1005 11.6495 3.75 8.75 3.75ZM2 9C2 5.27208 5.02208 2.25 8.75 2.25C12.4779 2.25 15.5 5.27208 15.5 9C15.5 12.7279 12.4779 15.75 8.75 15.75C5.02208 15.75 2 12.7279 2 9Z"
		/>
		<path
			fill-rule="evenodd"
			clip-rule="evenodd"
			fill={color}
			d="M13.2803 13.2803C13.5732 12.9874 14.0481 12.9874 14.341 13.2803L17.7803 16.7197C18.0732 17.0126 18.0732 17.4874 17.7803 17.7803C17.4874 18.0732 17.0126 18.0732 16.7197 17.7803L13.2803 14.341C12.9874 14.0481 12.9874 13.5732 13.2803 13.2803Z"
		/>
	</svg>
</div>

<style>
	.icon-search-1 {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

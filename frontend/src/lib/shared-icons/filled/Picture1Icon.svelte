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
	class="icon-picture-1 {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Picture 1'}
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
			d="M2 5C2 3.34315 3.34315 2 5 2H15C16.6569 2 18 3.34315 18 5V15C18 16.6569 16.6569 18 15 18H5C3.34315 18 2 16.6569 2 15V5ZM5 4C4.44772 4 4 4.44772 4 5V15C4 15.5523 4.44772 16 5 16H15C15.5523 16 16 15.5523 16 15V5C16 4.44772 15.5523 4 15 4H5Z"
		/>
		<path
			fill-rule="evenodd"
			clip-rule="evenodd"
			fill={color}
			d="M7 7C7 6.44772 7.44772 6 8 6C8.55228 6 9 6.44772 9 7C9 7.55228 8.55228 8 8 8C7.44772 8 7 7.55228 7 7Z"
		/>
		<path
			fill-rule="evenodd"
			clip-rule="evenodd"
			fill={color}
			d="M4 13L8 9L10 11L14 7L16 9V15H4V13Z"
		/>
	</svg>
</div>

<style>
	.icon-picture-1 {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

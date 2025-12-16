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
	class="icon-app {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'App'}
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
			d="M4 3C3.44772 3 3 3.44772 3 4V8C3 8.55228 3.44772 9 4 9H8C8.55228 9 9 8.55228 9 8V4C9 3.44772 8.55228 3 8 3H4Z"
		/>
		<path
			fill-rule="evenodd"
			clip-rule="evenodd"
			fill={color}
			d="M12 3C11.4477 3 11 3.44772 11 4V8C11 8.55228 11.4477 9 12 9H16C16.5523 9 17 8.55228 17 8V4C17 3.44772 16.5523 3 16 3H12Z"
		/>
		<path
			fill-rule="evenodd"
			clip-rule="evenodd"
			fill={color}
			d="M4 11C3.44772 11 3 11.4477 3 12V16C3 16.5523 3.44772 17 4 17H8C8.55228 17 9 16.5523 9 16V12C9 11.4477 8.55228 11 8 11H4Z"
		/>
		<path
			fill-rule="evenodd"
			clip-rule="evenodd"
			fill={color}
			d="M12 11C11.4477 11 11 11.4477 11 12V16C11 16.5523 11.4477 17 12 17H16C16.5523 17 17 16.5523 17 16V12C17 11.4477 16.5523 11 16 11H12Z"
		/>
	</svg>
</div>

<style>
	.icon-app {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

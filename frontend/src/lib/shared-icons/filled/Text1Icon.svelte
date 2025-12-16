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
	class="icon-text-1 {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Text 1'}
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
			d="M3 4C3 3.44772 3.44772 3 4 3H16C16.5523 3 17 3.44772 17 4V5C17 5.55228 16.5523 6 16 6H4C3.44772 6 3 5.55228 3 5V4Z"
		/>
		<path
			fill-rule="evenodd"
			clip-rule="evenodd"
			fill={color}
			d="M3 8C3 7.44772 3.44772 7 4 7H16C16.5523 7 17 7.44772 17 8V9C17 9.55228 16.5523 10 16 10H4C3.44772 10 3 9.55228 3 9V8Z"
		/>
		<path
			fill-rule="evenodd"
			clip-rule="evenodd"
			fill={color}
			d="M3 12C3 11.4477 3.44772 11 4 11H13C13.5523 11 14 11.4477 14 12V13C14 13.5523 13.5523 14 13 14H4C3.44772 14 3 13.5523 3 13V12Z"
		/>
		<path
			fill-rule="evenodd"
			clip-rule="evenodd"
			fill={color}
			d="M16 11C16.5523 11 17 11.4477 17 12V16C17 16.5523 16.5523 17 16 17C15.4477 17 15 16.5523 15 16V12C15 11.4477 15.4477 11 16 11Z"
		/>
	</svg>
</div>

<style>
	.icon-text-1 {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

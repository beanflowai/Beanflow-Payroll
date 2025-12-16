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
	class="icon-voice {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Voice'}
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
			d="M10 2C11.6569 2 13 3.34315 13 5V9C13 10.6569 11.6569 12 10 12C8.34315 12 7 10.6569 7 9V5C7 3.34315 8.34315 2 10 2Z"
		/>
		<path
			fill-rule="evenodd"
			clip-rule="evenodd"
			fill={color}
			d="M5 9C5.55228 9 6 9.44772 6 10C6 12.7614 8.23858 15 11 15C13.7614 15 16 12.7614 16 10C16 9.44772 16.4477 9 17 9C17.5523 9 18 9.44772 18 10C18 13.866 14.866 17 11 17C7.13401 17 4 13.866 4 10C4 9.44772 4.44772 9 5 9Z"
		/>
		<path
			fill-rule="evenodd"
			clip-rule="evenodd"
			fill={color}
			d="M11 15V18C11 18.5523 10.5523 19 10 19C9.44772 19 9 18.5523 9 18V15H11Z"
		/>
	</svg>
</div>

<style>
	.icon-voice {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

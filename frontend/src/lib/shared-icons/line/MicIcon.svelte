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
	class="icon-mic {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Microphone icon'}
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
			d="M10 12C11.6569 12 13 10.6569 13 9V5C13 3.34315 11.6569 2 10 2C8.34315 2 7 3.34315 7 5V9C7 10.6569 8.34315 12 10 12Z"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<path
			d="M16 9C16 12.3137 13.3137 15 10 15C6.68629 15 4 12.3137 4 9"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<path
			d="M10 15V18"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<path
			d="M7 18H13"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-mic {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

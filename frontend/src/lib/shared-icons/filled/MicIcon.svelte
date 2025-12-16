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
	aria-label={ariaLabel || 'Microphone'}
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
			d="M10 11.875C11.7259 11.875 13.125 10.4759 13.125 8.75V5.625C13.125 3.89911 11.7259 2.5 10 2.5C8.27411 2.5 6.875 3.89911 6.875 5.625V8.75C6.875 10.4759 8.27411 11.875 10 11.875Z"
			fill={color}
			stroke={color}
			stroke-width="0.5"
		/>
		<path
			d="M10 14.375C7.42411 14.375 5.3125 12.2634 5.3125 9.6875H3.75C3.75 13.1283 6.55922 15.9375 10 15.9375C13.4408 15.9375 16.25 13.1283 16.25 9.6875H14.6875C14.6875 12.2634 12.5759 14.375 10 14.375Z"
			fill={color}
			stroke={color}
			stroke-width="0.5"
		/>
		<path d="M10 15.9375V17.5" stroke={color} stroke-width="1.5" stroke-linecap="round" />
	</svg>
</div>

<style>
	.icon-mic {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

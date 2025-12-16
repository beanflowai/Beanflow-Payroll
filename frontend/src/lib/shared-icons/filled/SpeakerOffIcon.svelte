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
	class="icon-speaker-off {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Speaker Off'}
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
			d="M4.375 8.125H6.875L10 5.625V14.375L6.875 11.875H4.375C4.02982 11.875 3.75 11.5952 3.75 11.25V8.75C3.75 8.40482 4.02982 8.125 4.375 8.125Z"
			fill={color}
			stroke={color}
			stroke-width="0.5"
		/>
		<path
			d="M2.5 2.5L17.5 17.5"
			stroke="white"
			stroke-width="2"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-speaker-off {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

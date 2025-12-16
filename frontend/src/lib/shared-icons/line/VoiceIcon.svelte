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
			d="M10 11C11.5 11 12.5 10 12.5 8.5V5.5C12.5 4 11.5 3 10 3C8.5 3 7.5 4 7.5 5.5V8.5C7.5 10 8.5 11 10 11Z"
			stroke={color}
			stroke-width="1.5"
		/>
		<path
			d="M5 8.5C5 12 7 14 10 14C13 14 15 12 15 8.5"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<path
			d="M10 14V17"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
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

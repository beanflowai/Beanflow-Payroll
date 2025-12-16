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
	class="icon-picture1 {className}"
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
		<rect x="3" y="3" width="14" height="14" rx="2" stroke={color} stroke-width="1.5" />
		<circle cx="7.5" cy="8.5" r="1.5" fill={color} />
		<path
			d="M4 14L8 10L10 12L14 8L16 10V16H4V14Z"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-picture1 {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

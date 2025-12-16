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
	class="icon-input {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Input'}
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
		<rect x="3" y="6" width="14" height="8" rx="1" stroke={color} stroke-width="1.5" />
		<path
			d="M6 10H14"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<circle cx="16" cy="10" r="1.5" stroke={color} stroke-width="1.5" />
	</svg>
</div>

<style>
	.icon-input {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

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
	class="icon-picture2 {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Picture 2'}
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
		<rect x="2" y="2" width="16" height="16" rx="2" stroke={color} stroke-width="1.5" />
		<circle cx="8" cy="9" r="2" stroke={color} stroke-width="1.5" />
		<path
			d="M3 15L7 11L9 13L15 7L17 9V17H3V15Z"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-picture2 {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

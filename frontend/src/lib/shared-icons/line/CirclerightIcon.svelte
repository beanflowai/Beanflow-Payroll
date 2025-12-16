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
	class="icon-circleright {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Circle right'}
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
		<circle cx="10" cy="10" r="7.5" stroke={color} stroke-width="1.5" />
		<path
			d="M8.5 7.5L11.5 10L8.5 12.5"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-circleright {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

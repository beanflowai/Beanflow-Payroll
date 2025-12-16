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
	class="icon-circle-add {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Circle Add'}
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
		<circle cx="10" cy="10" r="9" fill={color} />
		<path
			d="M10 6V14M6 10H14"
			stroke="white"
			stroke-width="1.5"
			stroke-linecap="round"
			fill="none"
		/>
	</svg>
</div>

<style>
	.icon-circle-add {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

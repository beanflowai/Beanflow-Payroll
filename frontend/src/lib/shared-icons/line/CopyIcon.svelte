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
	class="icon-copy {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Copy icon'}
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
		<rect
			x="5"
			y="7"
			width="11"
			height="11"
			rx="1"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<path
			d="M9 7V4C9 3.44772 8.55228 3 8 3H4C3.44772 3 3 3.44772 3 4V12C3 12.5523 3.44772 13 4 13H7"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-copy {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

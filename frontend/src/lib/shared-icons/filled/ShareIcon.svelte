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
	class="icon-share {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Share'}
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
			d="M15 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM15 14a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM5 14a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"
			fill={color}
		/>
		<path
			d="M7.592 12.952 13.408 9.048M7.592 7.048 13.408 10.952"
			stroke={color}
			stroke-width="2"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-share {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

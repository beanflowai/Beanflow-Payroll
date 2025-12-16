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
	class="icon-help {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Help icon'}
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
		<circle
			cx="10"
			cy="10"
			r="7"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<path
			d="M8 8C8 7.44772 8.44772 7 9 7H11C11.5523 7 12 7.44772 12 8C12 8.55228 11.5523 9 11 9H10C9.44772 9 9 9.44772 9 10V11"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<circle cx="10" cy="14" r="0.5" fill={color} />
	</svg>
</div>

<style>
	.icon-help {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

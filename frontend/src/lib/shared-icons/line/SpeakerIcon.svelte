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
	class="icon-speaker {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Speaker icon'}
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
			d="M4 8H7L11 4V16L7 12H4C3.44772 12 3 11.5523 3 11V9C3 8.44772 3.44772 8 4 8Z"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<path
			d="M14 8C14.5523 8 15 8.44772 15 9C15 9.55228 14.5523 10 14 10"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<path
			d="M16 6C17.1046 6 18 6.89543 18 8V12C18 13.1046 17.1046 14 16 14"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-speaker {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

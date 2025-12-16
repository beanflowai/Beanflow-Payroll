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
	class="icon-group {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Group'}
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
		<circle cx="7" cy="7" r="2.5" stroke={color} stroke-width="1.5" />
		<path
			d="M3.5 15.5C3.5 13.5 5 11.5 7 11.5C9 11.5 10.5 13.5 10.5 15.5"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<circle cx="14" cy="8" r="2" stroke={color} stroke-width="1.5" />
		<path
			d="M11.5 14.5C11.5 13 12.5 11.5 14 11.5C15.5 11.5 16.5 13 16.5 14.5"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-group {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

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
	class="icon-search1 {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Search 1'}
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
		<circle cx="8.5" cy="8.5" r="5.5" stroke={color} stroke-width="1.5" />
		<path
			d="M12.5 12.5L16.5 16.5"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-search1 {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

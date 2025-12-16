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
	class="icon-search2 {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Search 2'}
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
		<circle cx="9" cy="9" r="6" stroke={color} stroke-width="1.5" />
		<path
			d="M13 13L17 17"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-search2 {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

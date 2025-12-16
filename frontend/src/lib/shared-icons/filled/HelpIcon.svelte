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
	aria-label={ariaLabel || 'Help'}
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
			fill-rule="evenodd"
			clip-rule="evenodd"
			fill={color}
			d="M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0ZM8.965 14.169a1 1 0 1 0 1.07 1.699A3.999 3.999 0 0 0 15 10c0-1.085-.577-2.037-1.441-2.568A4.002 4.002 0 0 0 10 4a4 4 0 0 0-3.98 4.6 1 1 0 0 0 1.98-.2A2 2 0 0 1 10 6c1.103 0 2 .897 2 2s-.897 2-2 2a1 1 0 0 0-1 1v2a1 1 0 1 0 2 0v-1.06A4.002 4.002 0 0 0 14 12c1.103 0 2-.897 2-2 0-1.925-1.367-3.531-3.186-3.89A2.001 2.001 0 0 1 11 14.169ZM10 17a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z"
		/>
	</svg>
</div>

<style>
	.icon-help {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

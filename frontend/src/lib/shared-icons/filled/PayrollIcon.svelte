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
	class="icon-payroll {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Payroll'}
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
			fill={color}
			d="M4 4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4Zm2 0v12h8V4H6Zm2 2a1 1 0 0 0 0 2h4a1 1 0 1 0 0-2H8Zm-1 4a1 1 0 0 1 1-1h4a1 1 0 1 1 0 2H8a1 1 0 0 1-1-1Zm1 3a1 1 0 0 0 0 2h4a1 1 0 1 0 0-2H8Z"
		/>
		<circle cx="14" cy="6" r="2" fill={color} />
		<path
			fill={color}
			d="M13 11a1 1 0 0 1 1-1h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1a1 1 0 0 1-1-1v-3Z"
		/>
	</svg>
</div>

<style>
	.icon-payroll {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

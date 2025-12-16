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
	class="icon-reports {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Reports'}
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
			d="M4 3a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V4a1 1 0 0 0-1-1H4Zm2 3a1 1 0 0 1 1-1h6a1 1 0 1 1 0 2H7a1 1 0 0 1-1-1Zm1 2a1 1 0 0 0 0 2h3a1 1 0 1 0 0-2H7Zm-1 4a1 1 0 0 1 1-1h3a1 1 0 1 1 0 2H7a1 1 0 0 1-1-1Zm5 0a1 1 0 0 1 1-1h2a1 1 0 1 1 0 2h-2a1 1 0 0 1-1-1Z"
		/>
	</svg>
</div>

<style>
	.icon-reports {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

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
	class="icon-report {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Report'}
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
			d="M3 4a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4Zm3 1a1 1 0 0 0 0 2h8a1 1 0 1 0 0-2H6Zm0 3a1 1 0 0 0 0 2h8a1 1 0 1 0 0-2H6Zm-1 4a1 1 0 0 1 1-1h8a1 1 0 1 1 0 2H6a1 1 0 0 1-1-1Z"
		/>
	</svg>
</div>

<style>
	.icon-report {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

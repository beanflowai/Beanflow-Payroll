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
	class="icon-documents {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Documents'}
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
			d="M6 2a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7.414a2 2 0 0 0-.586-1.414l-3.414-3.414A2 2 0 0 0 12.586 2H6ZM6 4h6v3a1 1 0 0 0 1 1h3v8H6V4Zm2 2a1 1 0 0 0 0 2h4a1 1 0 1 0 0-2H8Zm0 3a1 1 0 0 0 0 2h4a1 1 0 1 0 0-2H8Zm-1 4a1 1 0 0 1 1-1h4a1 1 0 1 1 0 2H8a1 1 0 0 1-1-1Z"
		/>
	</svg>
</div>

<style>
	.icon-documents {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

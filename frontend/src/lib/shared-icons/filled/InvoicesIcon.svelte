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
	class="icon-invoices {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Invoices'}
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
			d="M4 2a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.414a2 2 0 0 0-.586-1.414l-3.414-3.414A2 2 0 0 0 12.586 2H4ZM4 4h8v3a1 1 0 0 0 1 1h3v8H4V4Zm7 5a1 1 0 0 1 0 2h4a1 1 0 1 0 0-2h-4Zm-4 3a1 1 0 0 0 0 2h8a1 1 0 1 0 0-2H7Zm-1 3a1 1 0 0 1 1-1h8a1 1 0 1 1 0 2H7a1 1 0 0 1-1-1Z"
		/>
	</svg>
</div>

<style>
	.icon-invoices {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

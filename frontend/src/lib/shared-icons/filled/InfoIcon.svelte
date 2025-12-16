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
	class="icon-info {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Info'}
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
			d="M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0ZM11 15a1 1 0 1 1-2 0v-4a1 1 0 1 1 2 0v4Zm1-7a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z"
		/>
	</svg>
</div>

<style>
	.icon-info {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

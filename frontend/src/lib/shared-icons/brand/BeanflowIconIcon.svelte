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
	class="icon-beanflow-icon {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'BeanflowIcon'}
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
			d="M10 2a8 8 0 1 0 0 16 8 8 0 0 0 0-16Zm0 2a6 6 0 1 0 0 12 6 6 0 0 0 0-12Z"
		/>
		<path
			fill={color}
			d="M10 6a1 1 0 1 0 0 2 1 1 0 0 0 0-2Zm0 3a1 1 0 0 0-1 1v2a1 1 0 1 0 2 0v-2a1 1 0 0 0-1-1Z"
		/>
		<path fill={color} d="M6 8h1v1H6V8Zm7 0h1v1h-1V8Z" />
	</svg>
</div>

<style>
	.icon-beanflow-icon {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

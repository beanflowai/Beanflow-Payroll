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
	class="icon-beanflow-logo {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'BeanflowLogo'}
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
			d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm3.707-8.293a1 1 0 0 0-1.414-1.414L9 11.586 7.707 10.293a1 1 0 0 0-1.414 1.414l2 2a1 1 0 0 0 1.414 0l4-4Z"
		/>
		<circle cx="6" cy="8" r="1" fill={color} />
		<circle cx="14" cy="8" r="1" fill={color} />
		<path fill={color} d="M7 13h6v1H7v-1Z" />
	</svg>
</div>

<style>
	.icon-beanflow-logo {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

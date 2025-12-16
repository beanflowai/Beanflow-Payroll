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
	class="icon-reply {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Reply'}
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
			d="M7.707 3.293a1 1 0 0 0-1.414 1.414L10.586 9H3a1 1 0 0 0 0 2h7.586l-4.293 4.293a1 1 0 1 0 1.414 1.414l6-6a1 1 0 0 0 0-1.414l-6-6z"
		/>
	</svg>
</div>

<style>
	.icon-reply {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

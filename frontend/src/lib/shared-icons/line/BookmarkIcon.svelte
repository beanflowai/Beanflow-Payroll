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
	class="icon-bookmark {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Bookmark icon'}
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
			d="M5 2H15C15.5523 2 16 2.44772 16 3V18L10 15L4 18V3C4 2.44772 4.44772 2 5 2Z"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-bookmark {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

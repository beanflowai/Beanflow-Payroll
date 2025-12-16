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
	aria-label={ariaLabel || 'Bookmark'}
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
			d="M5 3.125C5 2.43464 5.55964 1.875 6.25 1.875H13.75C14.4404 1.875 15 2.43464 15 3.125V16.875L10 13.75L5 16.875V3.125Z"
			fill={color}
			stroke={color}
			stroke-width="0.5"
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

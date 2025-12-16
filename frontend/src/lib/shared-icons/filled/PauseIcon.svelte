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
	class="icon-pause {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Pause'}
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
			d="M6 3C5.44772 3 5 3.44772 5 4V16C5 16.5523 5.44772 17 6 17C6.55228 17 7 16.5523 7 16V4C7 3.44772 6.55228 3 6 3Z"
		/>
		<path
			fill-rule="evenodd"
			clip-rule="evenodd"
			fill={color}
			d="M14 3C13.4477 3 13 3.44772 13 4V16C13 16.5523 13.4477 17 14 17C14.5523 17 15 16.5523 15 16V4C15 3.44772 14.5523 3 14 3Z"
		/>
	</svg>
</div>

<style>
	.icon-pause {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

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
	class="icon-menu {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Menu'}
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
			d="M2 5C2 4.44772 2.44772 4 3 4H17C17.5523 4 18 4.44772 18 5C18 5.55228 17.5523 6 17 6H3C2.44772 6 2 5.55228 2 5ZM2 10C2 9.44772 2.44772 9 3 9H17C17.5523 9 18 9.44772 18 10C18 10.5523 17.5523 11 17 11H3C2.44772 11 2 10.5523 2 10ZM3 14C2.44772 14 2 14.4477 2 15C2 15.5523 2.44772 16 3 16H17C17.5523 16 18 15.5523 18 15C18 14.4477 17.5523 14 17 14H3Z"
		/>
	</svg>
</div>

<style>
	.icon-menu {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

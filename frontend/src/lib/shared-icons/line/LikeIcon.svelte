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
	class="icon-like {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Like icon'}
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
			d="M10 18C10 18 2 13 2 7C2 4.23858 4.23858 2 7 2C8.30508 2 9.47257 2.67157 10 3.67157C10.5274 2.67157 11.6949 2 13 2C15.7614 2 18 4.23858 18 7C18 13 10 18 10 18Z"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-like {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

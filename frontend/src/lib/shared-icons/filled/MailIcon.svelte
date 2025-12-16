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
	class="icon-mail {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Mail'}
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
		<rect
			x="2.5"
			y="5"
			width="15"
			height="10"
			rx="1.25"
			fill={color}
			stroke={color}
			stroke-width="0.5"
		/>
		<path
			d="M2.5 5.625L10 11.25L17.5 5.625"
			stroke="white"
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
			fill="none"
		/>
	</svg>
</div>

<style>
	.icon-mail {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

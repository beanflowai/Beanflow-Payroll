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
	class="icon-home {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Home'}
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
			d="M2.8125 10.3125L10 3.125L17.1875 10.3125V16.875C17.1875 17.1734 17.069 17.4595 16.858 17.6705C16.647 17.8815 16.3609 18 16.0625 18H13.4375C13.1391 18 12.853 17.8815 12.642 17.6705C12.431 17.4595 12.3125 17.1734 12.3125 16.875V12.8125C12.3125 12.6633 12.253 12.5202 12.1475 12.4148C12.042 12.3093 11.899 12.25 11.75 12.25H8.25C8.10082 12.25 7.95774 12.3093 7.85225 12.4148C7.74676 12.5202 7.6875 12.6633 7.6875 12.8125V16.875C7.6875 17.1734 7.56897 17.4595 7.35798 17.6705C7.14699 17.8815 6.86087 18 6.5625 18H3.9375C3.63913 18 3.35301 17.8815 3.14202 17.6705C2.93103 17.4595 2.8125 17.1734 2.8125 16.875V10.3125Z"
			fill={color}
			stroke={color}
			stroke-width="0.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<path
			d="M1.25 10L10 1.25L18.75 10"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-home {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

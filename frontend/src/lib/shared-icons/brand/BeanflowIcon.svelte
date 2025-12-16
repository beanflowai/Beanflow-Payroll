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
	class="icon-beanflow {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Beanflow'}
	aria-hidden={ariaHidden}
	role="img"
	{...restProps}
>
	<svg
		width={size}
		height={size}
		viewBox="0 0 32 32"
		fill="none"
		xmlns="http://www.w3.org/2000/svg"
	>
		<defs>
			<linearGradient id="beanflow-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
				<stop offset="0%" style="stop-color:#9810fa;stop-opacity:1" />
				<stop offset="100%" style="stop-color:#612AE1;stop-opacity:1" />
			</linearGradient>
		</defs>
		<path
			d="M16 2C8.26801 2 2 8.26801 2 16C2 23.732 8.26801 30 16 30C23.732 30 30 23.732 30 16C30 8.26801 23.732 2 16 2Z"
			fill="url(#beanflow-gradient)"
		/>
		<path
			d="M16 8C13.7909 8 12 9.79086 12 12C12 14.2091 13.7909 16 16 16C18.2091 16 20 14.2091 20 12C20 9.79086 18.2091 8 16 8Z"
			fill="white"
		/>
		<path
			d="M10 22C10 19.7909 11.7909 18 14 18H18C20.2091 18 22 19.7909 22 22C22 24.2091 20.2091 26 18 26H14C11.7909 26 10 24.2091 10 22Z"
			fill="white"
		/>
	</svg>
</div>

<style>
	.icon-beanflow {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

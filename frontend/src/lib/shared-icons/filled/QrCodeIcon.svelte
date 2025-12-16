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
	class="icon-qr-code {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'QR Code'}
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
			y="2.5"
			width="6.25"
			height="6.25"
			rx="1.25"
			fill={color}
			stroke={color}
			stroke-width="0.5"
		/>
		<rect
			x="11.25"
			y="2.5"
			width="6.25"
			height="6.25"
			rx="1.25"
			fill={color}
			stroke={color}
			stroke-width="0.5"
		/>
		<rect
			x="2.5"
			y="11.25"
			width="6.25"
			height="6.25"
			rx="1.25"
			fill={color}
			stroke={color}
			stroke-width="0.5"
		/>
		<rect x="5.3125" y="5.3125" width="0.625" height="0.625" fill="white" />
		<rect x="14.0625" y="5.3125" width="0.625" height="0.625" fill="white" />
		<rect x="5.3125" y="14.0625" width="0.625" height="0.625" fill="white" />
		<rect x="11.875" y="11.875" width="0.625" height="0.625" fill={color} />
		<rect x="13.75" y="13.75" width="0.625" height="0.625" fill={color} />
		<rect x="13.75" y="11.875" width="0.625" height="0.625" fill={color} />
		<rect x="11.875" y="13.75" width="0.625" height="0.625" fill={color} />
	</svg>
</div>

<style>
	.icon-qr-code {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

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
	class="icon-download {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Download'}
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
			d="M2.5 12.5V15C2.5 15.6904 2.5 16.0355 2.61887 16.3016C2.72342 16.5347 2.91281 16.7241 3.14586 16.8286C3.41197 16.9475 3.75714 16.9475 4.4475 16.9475H15.5525C16.2429 16.9475 16.588 16.9475 16.8541 16.8286C17.0872 16.7241 17.2765 16.5347 17.3811 16.3016C17.5 16.0355 17.5 15.6904 17.5 15V12.5"
			fill={color}
			stroke={color}
			stroke-width="0.5"
		/>
		<path d="M10 2.5V12.5" stroke={color} stroke-width="1.5" stroke-linecap="round" />
		<path
			d="M6.25 8.75L10 12.5L13.75 8.75"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-download {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

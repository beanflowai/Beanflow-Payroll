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
	class="icon-upload {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Upload'}
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
			d="M2.5 7.5V5C2.5 4.30964 2.5 3.96447 2.61887 3.69836C2.72342 3.46531 2.91281 3.27592 3.14586 3.17137C3.41197 3.0525 3.75714 3.0525 4.4475 3.0525H15.5525C16.2429 3.0525 16.588 3.0525 16.8541 3.17137C17.0872 3.27592 17.2765 3.46531 17.3811 3.69836C17.5 3.96447 17.5 4.30964 17.5 5V7.5"
			fill={color}
			stroke={color}
			stroke-width="0.5"
		/>
		<path d="M10 17.5V7.5" stroke={color} stroke-width="1.5" stroke-linecap="round" />
		<path
			d="M6.25 11.25L10 7.5L13.75 11.25"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-upload {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

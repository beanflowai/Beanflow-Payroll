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
	class="icon-payroll {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Payroll icon'}
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
		<circle
			cx="10"
			cy="7"
			r="3"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<path
			d="M16 17C16 14.2386 13.3137 12 10 12C6.68629 12 4 14.2386 4 17"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<circle
			cx="15"
			cy="5"
			r="2"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<path
			d="M17.5 8.5C18.3284 8.5 19 7.82843 19 7C19 6.17157 18.3284 5.5 17.5 5.5C16.6716 5.5 16 6.17157 16 7C16 7.82843 16.6716 8.5 17.5 8.5Z"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-payroll {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

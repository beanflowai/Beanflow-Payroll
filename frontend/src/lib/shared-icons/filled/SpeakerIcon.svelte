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
	class="icon-speaker {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Speaker'}
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
			d="M4.375 8.125H6.875L10 5.625V14.375L6.875 11.875H4.375C4.02982 11.875 3.75 11.5952 3.75 11.25V8.75C3.75 8.40482 4.02982 8.125 4.375 8.125Z"
			fill={color}
			stroke={color}
			stroke-width="0.5"
		/>
		<path
			d="M12.5 7.5C13.125 8.125 13.125 11.875 12.5 12.5"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
		/>
		<path
			d="M14.375 5.625C15.3125 6.5625 15.3125 13.4375 14.375 14.375"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
		/>
	</svg>
</div>

<style>
	.icon-speaker {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

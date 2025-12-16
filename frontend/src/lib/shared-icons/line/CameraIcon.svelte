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
	class="icon-camera {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Camera icon'}
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
			d="M4 5H6.58579C7.11621 5 7.62491 4.78929 7.99998 4.41421L8.58579 3.82843C8.96086 3.45336 9.46957 3.24264 10 3.24264H10C10.5304 3.24264 11.0391 3.45336 11.4142 3.82843L12 4.41421C12.3751 4.78929 12.8838 5 13.4142 5H16C16.5523 5 17 5.44772 17 6V15C17 15.5523 16.5523 16 16 16H4C3.44772 16 3 15.5523 3 15V6C3 5.44772 3.44772 5 4 5Z"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
		<circle
			cx="10"
			cy="11"
			r="2.5"
			stroke={color}
			stroke-width="1.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
</div>

<style>
	.icon-camera {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

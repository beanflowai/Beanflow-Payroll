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
	class="icon-group {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Group'}
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
			fill-rule="evenodd"
			clip-rule="evenodd"
			fill={color}
			d="M7 7C8.10457 7 9 6.10457 9 5C9 3.89543 8.10457 3 7 3C5.89543 3 5 3.89543 5 5C5 6.10457 5.89543 7 7 7Z"
		/>
		<path
			fill-rule="evenodd"
			clip-rule="evenodd"
			fill={color}
			d="M14 8C15.1046 8 16 7.10457 16 6C16 4.89543 15.1046 4 14 4C12.8954 4 12 4.89543 12 6C12 7.10457 12.8954 8 14 8Z"
		/>
		<path
			fill-rule="evenodd"
			clip-rule="evenodd"
			fill={color}
			d="M10 11C11.6569 11 13 9.65685 13 8C13 6.34315 11.6569 5 10 5C8.34315 5 7 6.34315 7 8C7 9.65685 8.34315 11 10 11Z"
		/>
		<path
			fill-rule="evenodd"
			clip-rule="evenodd"
			fill={color}
			d="M5 13C6.10457 13 7 12.1046 7 11C7 9.89543 6.10457 9 5 9C3.89543 9 3 9.89543 3 11C3 12.1046 3.89543 13 5 13Z"
		/>
		<path
			fill-rule="evenodd"
			clip-rule="evenodd"
			fill={color}
			d="M16 14C17.1046 14 18 13.1046 18 12C18 10.8954 17.1046 10 16 10C14.8954 10 14 10.8954 14 12C14 13.1046 14.8954 14 16 14Z"
		/>
		<path
			fill-rule="evenodd"
			clip-rule="evenodd"
			fill={color}
			d="M10 17C11.6569 17 13 15.6569 13 14C13 12.3431 11.6569 11 10 11C8.34315 11 7 12.3431 7 14C7 15.6569 8.34315 17 10 17Z"
		/>
	</svg>
</div>

<style>
	.icon-group {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

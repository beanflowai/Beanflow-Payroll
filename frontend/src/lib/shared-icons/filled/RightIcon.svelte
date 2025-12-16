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
	class="icon-right {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Right'}
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
			d="M13.5 10C13.5 9.72386 13.2761 9.5 13 9.5H7C6.72386 9.5 6.5 9.72386 6.5 10C6.5 10.2761 6.72386 10.5 7 10.5H13C13.2761 10.5 13.5 10.2761 13.5 10ZM9.78033 6.21967C9.48744 5.92678 9.01256 5.92678 8.71967 6.21967C8.42678 6.51256 8.42678 6.98744 8.71967 7.28033L10.1893 8.75H7C6.72386 8.75 6.5 8.97386 6.5 9.25C6.5 9.52614 6.72386 9.75 7 9.75H10.1893L8.71967 11.2197C8.42678 11.5126 8.42678 11.9874 8.71967 12.2803C9.01256 12.5732 9.48744 12.5732 9.78033 12.2803L12.2803 9.78033C12.5732 9.48744 12.5732 9.01256 12.2803 8.71967L9.78033 6.21967Z"
		/>
	</svg>
</div>

<style>
	.icon-right {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

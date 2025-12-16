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
	class="icon-left {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Left'}
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
			d="M6.5 10C6.5 9.72386 6.72386 9.5 7 9.5H13C13.2761 9.5 13.5 9.72386 13.5 10C13.5 10.2761 13.2761 10.5 13 10.5H7C6.72386 10.5 6.5 10.2761 6.5 10ZM10.2197 6.21967C10.5126 5.92678 10.9874 5.92678 11.2803 6.21967L13.7803 8.71967C14.0732 9.01256 14.0732 9.48744 13.7803 9.78033L11.2803 12.2803C10.9874 12.5732 10.5126 12.5732 10.2197 12.2803C9.92678 11.9874 9.92678 11.5126 10.2197 11.2197L11.6893 9.75H7C6.72386 9.75 6.5 9.52614 6.5 9.25C6.5 8.97386 6.72386 8.75 7 8.75H11.6893L10.2197 7.28033C9.92678 6.98744 9.92678 6.51256 10.2197 6.21967Z"
		/>
	</svg>
</div>

<style>
	.icon-left {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

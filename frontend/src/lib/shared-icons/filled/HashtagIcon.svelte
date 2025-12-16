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
	class="icon-hashtag {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Hashtag'}
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
			d="M8.5 2.5C8.5 1.94772 8.94772 1.5 9.5 1.5C10.0523 1.5 10.5 1.94772 10.5 2.5V6.5H14.5C15.0523 6.5 15.5 6.94772 15.5 7.5C15.5 8.05228 15.0523 8.5 14.5 8.5H10.5V11.5H14.5C15.0523 11.5 15.5 11.9477 15.5 12.5C15.5 13.0523 15.0523 13.5 14.5 13.5H10.5V17.5C10.5 18.0523 10.0523 18.5 9.5 18.5C8.94772 18.5 8.5 18.0523 8.5 17.5V13.5H5.5C4.94772 13.5 4.5 13.0523 4.5 12.5C4.5 11.9477 4.94772 11.5 5.5 11.5H8.5V8.5H5.5C4.94772 8.5 4.5 8.05228 4.5 7.5C4.5 6.94772 4.94772 6.5 5.5 6.5H8.5V2.5Z"
		/>
	</svg>
</div>

<style>
	.icon-hashtag {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

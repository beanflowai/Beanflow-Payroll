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
	class="icon-logo {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Logo'}
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
			d="M4 4a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2H4Zm0 2h12v8H4V6Z"
		/>
		<path fill={color} d="M6 8h8v1H6V8Zm0 2h6v1H6v-1Z" />
		<circle cx="15" cy="15" r="2" fill={color} />
	</svg>
</div>

<style>
	.icon-logo {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

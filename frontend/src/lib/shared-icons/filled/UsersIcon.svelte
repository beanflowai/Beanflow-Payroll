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
	class="icon-users {className}"
	style="width: {size}px; height: {size}px;"
	aria-label={ariaLabel || 'Users'}
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
		<circle cx="7" cy="7" r="3" fill={color} />
		<path
			fill={color}
			d="M2 17a5 5 0 0 1 5-5h0a5 5 0 0 1 5 5v1H2v-1ZM13 7a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z"
		/>
		<path fill={color} d="M13 10a3 3 0 0 0-3 3v2h6v-2a3 3 0 0 0-3-3Z" />
	</svg>
</div>

<style>
	.icon-users {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
</style>

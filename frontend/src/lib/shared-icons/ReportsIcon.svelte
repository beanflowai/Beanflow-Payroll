<script lang="ts">
	interface ReportsIconProps {
		size?: number;
		color?: string;
		class?: string;
	}

	let { size = 18, color = 'currentColor', class: className = '' }: ReportsIconProps = $props();
</script>

<svg
	width={size}
	height={size}
	viewBox="0 0 18 18"
	fill="none"
	xmlns="http://www.w3.org/2000/svg"
	class={className}
>
	<rect
		x="1.80005"
		y="1.3501"
		width="14.4"
		height="12.6"
		rx="2.025"
		stroke={color}
		stroke-width="1.35"
	/>
	<path
		d="M8.99988 5.0249L8.99988 10.2749"
		stroke={color}
		stroke-width="1.35"
		stroke-linecap="round"
	/>
	<path
		d="M11.9999 8.0249L11.9999 10.2749"
		stroke={color}
		stroke-width="1.35"
		stroke-linecap="round"
	/>
	<path d="M6 6.5249L6 10.2749" stroke={color} stroke-width="1.35" stroke-linecap="round" />
	<path d="M3.59998 16.6499H14.4" stroke={color} stroke-width="1.35" stroke-linecap="round" />
</svg>

<script lang="ts">
	interface ActionListIconProps {
		size?: number;
		color?: string;
		class?: string;
	}

	let { size = 18, color = 'currentColor', class: className = '' }: ActionListIconProps = $props();
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
		x="2.47505"
		y="1.5749"
		width="5.85"
		height="5.85"
		rx="1.125"
		stroke={color}
		stroke-width="1.35"
	/>
	<rect
		x="2.47505"
		y="10.5749"
		width="5.85"
		height="5.85"
		rx="1.125"
		stroke={color}
		stroke-width="1.35"
	/>
	<path d="M10.8 2.4751H15.3" stroke={color} stroke-width="1.35" stroke-linecap="round" />
	<path d="M10.8 6.0752H15.3" stroke={color} stroke-width="1.35" stroke-linecap="round" />
	<path d="M10.8 11.4751H15.3" stroke={color} stroke-width="1.35" stroke-linecap="round" />
	<path d="M10.8 15.0752H15.3" stroke={color} stroke-width="1.35" stroke-linecap="round" />
</svg>

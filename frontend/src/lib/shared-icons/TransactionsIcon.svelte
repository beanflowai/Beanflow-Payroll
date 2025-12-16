<script lang="ts">
	interface TransactionsIconProps {
		size?: number;
		color?: string;
		class?: string;
	}

	let {
		size = 18,
		color = 'currentColor',
		class: className = ''
	}: TransactionsIconProps = $props();
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
		y="1.80005"
		width="14.4"
		height="14.4"
		rx="1.8"
		stroke={color}
		stroke-width="1.35"
	/>
	<path
		d="M5.13 7.2001H12.78L11.43 5.8501"
		stroke={color}
		stroke-width="1.35"
		stroke-linecap="round"
		stroke-linejoin="round"
	/>
	<path
		d="M12.7799 10.7999H5.12991L6.47991 12.1499"
		stroke={color}
		stroke-width="1.35"
		stroke-linecap="round"
		stroke-linejoin="round"
	/>
</svg>

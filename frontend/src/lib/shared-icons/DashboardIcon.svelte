<script lang="ts">
	interface DashboardIconProps {
		size?: number;
		color?: string;
		class?: string;
	}

	let { size = 18, color = 'currentColor', class: className = '' }: DashboardIconProps = $props();
</script>

<svg
	width={size}
	height={size}
	viewBox="0 0 18 18"
	fill="none"
	xmlns="http://www.w3.org/2000/svg"
	class={className}
>
	<g clip-path="url(#clip0_1_7181)">
		<circle cx="8.99998" cy="9.0001" r="7.65" stroke={color} stroke-width="1.35" />
		<path
			d="M4.67993 10.8L7.37993 8.09995L9.62993 10.8L13.2299 7.19995"
			stroke={color}
			stroke-width="1.35"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</g>
	<defs>
		<clipPath id="clip0_1_7181">
			<rect width="18" height="18" fill="white" />
		</clipPath>
	</defs>
</svg>

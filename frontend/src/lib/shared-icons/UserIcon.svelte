<script lang="ts">
	interface UserIconProps {
		size?: number;
		color?: string;
		class?: string;
	}

	let { size = 16, color = 'currentColor', class: className = '' }: UserIconProps = $props();
</script>

<svg
	width={size}
	height={size}
	viewBox="0 0 18 18"
	fill="none"
	xmlns="http://www.w3.org/2000/svg"
	class={className}
>
	<g clip-path="url(#clip0_14_1927)">
		<circle cx="9.00002" cy="8.9999" r="8.1" stroke={color} stroke-width="1.35" />
		<circle cx="9.00005" cy="7.2" r="2.7" stroke={color} stroke-width="1.35" />
		<line x1="1.80005" y1="12.825" x2="16.2" y2="12.825" stroke={color} stroke-width="1.35" />
	</g>
	<defs>
		<clipPath id="clip0_14_1927">
			<rect width="18" height="18" fill="white" />
		</clipPath>
	</defs>
</svg>

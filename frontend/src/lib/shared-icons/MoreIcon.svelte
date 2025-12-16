<script lang="ts">
	interface MoreIconProps {
		size?: number;
		color?: string;
		class?: string;
	}

	let { size = 16, color = 'currentColor', class: className = '' }: MoreIconProps = $props();
</script>

<svg
	width={size}
	height={size}
	viewBox="0 0 18 18"
	fill="none"
	xmlns="http://www.w3.org/2000/svg"
	class={className}
>
	<circle cx="3.6" cy="8.9999" r="1.35" fill={color} />
	<circle cx="9.00002" cy="8.9999" r="1.35" fill={color} />
	<circle cx="14.4" cy="8.9999" r="1.35" fill={color} />
</svg>

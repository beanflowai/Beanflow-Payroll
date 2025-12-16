<script lang="ts">
	interface UpdatesIconProps {
		size?: number;
		color?: string;
		class?: string;
	}

	let { size = 16, color = 'currentColor', class: className = '' }: UpdatesIconProps = $props();
</script>

<svg
	width={size}
	height={size}
	viewBox="0 0 18 18"
	fill="none"
	xmlns="http://www.w3.org/2000/svg"
	class={className}
>
	<path
		d="M4.13743 14.4871H14.0665M3.71122 11.1179L2.81119 13.0791C2.50915 13.7373 2.99005 14.4871 3.71422 14.4871H14.5328C15.2647 14.4871 15.7454 13.7225 15.4282 13.0629L14.4927 11.1179L14.4927 7.80332C14.4927 4.82611 12.0792 2.4126 9.10196 2.4126C6.12475 2.4126 3.71124 4.82611 3.71124 7.80332L3.71122 11.1179Z"
		stroke={color}
		stroke-width="1.35"
	/>
	<path
		d="M10.5705 16.2246C10.5705 16.965 9.97029 17.5651 9.22993 17.5651C8.48958 17.5651 7.8894 16.965 7.8894 16.2246H10.5705Z"
		fill={color}
	/>
	<line
		x1="9.27654"
		y1="1.32879"
		x2="9.27654"
		y2="1.51816"
		stroke={color}
		stroke-width="1.78844"
		stroke-linecap="round"
	/>
</svg>

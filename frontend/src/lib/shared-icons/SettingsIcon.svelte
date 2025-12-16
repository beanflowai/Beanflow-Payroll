<script lang="ts">
	interface Props {
		class?: string;
		size?: number;
		color?: string;
	}

	let { class: className = '', size = 18, color = 'currentColor' }: Props = $props();
</script>

<svg
	width={size}
	height={size}
	viewBox="0 0 18 18"
	fill="none"
	xmlns="http://www.w3.org/2000/svg"
	class={className}
>
	<circle cx="9.00005" cy="8.9998" r="2.7" stroke={color} stroke-width="1.35" />
	<path
		d="M16.3206 7.6499C16.8029 8.48529 16.8029 9.51452 16.3206 10.3499L13.8294 14.6647C13.3471 15.5001 12.4557 16.0147 11.4911 16.0147L6.50882 16.0147C5.5442 16.0147 4.65286 15.5001 4.17055 14.6647L1.6794 10.3499C1.19709 9.51452 1.19709 8.48528 1.6794 7.6499L4.17055 3.3351C4.65286 2.49971 5.5442 1.9851 6.50882 1.9851L11.4911 1.9851C12.4557 1.9851 13.3471 2.49971 13.8294 3.3351L16.3206 7.6499Z"
		stroke={color}
		stroke-width="1.35"
	/>
</svg>

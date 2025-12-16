<script lang="ts">
	interface ArrowUpFilledIconProps {
		size?: number;
		color?: string;
		class?: string;
	}

	let {
		size = 18,
		color = 'currentColor',
		class: className = ''
	}: ArrowUpFilledIconProps = $props();
</script>

<svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
	<path
		d="M8.13575 11.3379C8.58552 11.8776 9.41448 11.8776 9.86425 11.3379L13.0873 7.47021C13.6979 6.73747 13.1769 5.625 12.2231 5.625H5.77692C4.8231 5.625 4.30205 6.73746 4.91267 7.47021L8.13575 11.3379Z"
		fill="#612AE1"
	/>
</svg>

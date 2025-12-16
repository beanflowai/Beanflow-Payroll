<script lang="ts">
	interface InvoicesIconProps {
		size?: number;
		color?: string;
		class?: string;
	}

	let { size = 18, color = 'currentColor', class: className = '' }: InvoicesIconProps = $props();
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
		d="M16.2 2.25C16.6971 2.25 17.1 2.65294 17.1 3.15V14.85C17.1 15.3471 16.6971 15.75 16.2 15.75H15.3C14.803 15.75 14.4187 15.3229 14.18 14.8869C13.8744 14.3286 13.2814 13.95 12.6 13.95C11.9186 13.95 11.3257 14.3286 11.02 14.8869C10.7814 15.3229 10.3971 15.75 9.90002 15.75H8.10002C7.60297 15.75 7.21868 15.3229 6.98 14.8869C6.67437 14.3286 6.08141 13.95 5.40002 13.95C4.71864 13.95 4.12568 14.3286 3.82005 14.8869C3.58137 15.3229 3.19708 15.75 2.70002 15.75H1.80002C1.30297 15.75 0.900024 15.3471 0.900024 14.85V3.15C0.900025 2.65294 1.30297 2.25 1.80002 2.25H16.2Z"
		stroke={color}
		stroke-width="1.35"
	/>
	<path d="M4.5 5.8501H13.5" stroke={color} stroke-width="1.35" stroke-linecap="round" />
	<path d="M5.40002 9.44995H12.6" stroke={color} stroke-width="1.35" stroke-linecap="round" />
</svg>

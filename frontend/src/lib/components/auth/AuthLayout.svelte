<script lang="ts">
	interface Props {
		children?: import('svelte').Snippet;
	}

	let { children }: Props = $props();
</script>

<div
	class="min-h-screen flex items-center justify-center bg-gradient-to-br from-surface-50 via-surface-100 to-surface-50 p-4 relative overflow-hidden sm:items-center max-sm:items-start max-sm:pt-8 max-sm:p-3"
>
	<!-- Decorative gradient - top right -->
	<div
		class="absolute top-[-50%] right-[-20%] w-[80%] h-[150%] bg-[radial-gradient(ellipse_at_center,rgba(37,99,235,0.08)_0%,transparent_70%)] pointer-events-none"
		aria-hidden="true"
	></div>

	<!-- Decorative gradient - bottom left -->
	<div
		class="absolute bottom-[-30%] left-[-10%] w-[60%] h-full bg-[radial-gradient(ellipse_at_center,rgba(139,92,246,0.06)_0%,transparent_70%)] pointer-events-none"
		aria-hidden="true"
	></div>

	<!-- Content -->
	<div class="w-full max-w-[420px] max-sm:max-w-full relative z-10">
		{@render children?.()}
	</div>
</div>

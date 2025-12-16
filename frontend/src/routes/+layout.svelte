<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<!-- Font Awesome for icons -->
	<link
		rel="stylesheet"
		href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
		crossorigin="anonymous"
	/>
	<meta name="viewport" content="width=device-width, initial-scale=1" />
	<title>BeanFlow Payroll</title>
</svelte:head>

<!-- Root Layout -->
<div class="root-layout">
	{@render children()}
</div>

<style>
	.root-layout {
		width: 100%;
		min-height: 100vh;
	}

	/* Global base styles */
	:global(html) {
		box-sizing: border-box;
		font-size: var(--font-size-body-content-large);
		line-height: 1.5;
	}

	:global(*),
	:global(*::before),
	:global(*::after) {
		box-sizing: inherit;
	}

	:global(body) {
		margin: 0;
		padding: 0;
		font-family: var(--font-family-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
		-webkit-font-smoothing: antialiased;
		-moz-osx-font-smoothing: grayscale;
	}
</style>

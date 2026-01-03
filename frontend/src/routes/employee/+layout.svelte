<script lang="ts">
	/**
	 * Employee Portal - Root Layout
	 * Simply passes through to child layouts ([slug]/+layout.svelte handles company validation)
	 */
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
	}

	let { children }: Props = $props();
</script>

{@render children()}

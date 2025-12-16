<script lang="ts">
	/**
	 * Employee Portal Layout
	 * Provides the main layout structure for employee self-service portal
	 * - Header with logo and user info
	 * - Sidebar navigation (desktop)
	 * - Bottom navigation (mobile)
	 */
	import type { Snippet } from 'svelte';
	import { page } from '$app/stores';
	import PortalHeader from '$lib/components/employee-portal/PortalHeader.svelte';
	import PortalSidebar from '$lib/components/employee-portal/PortalSidebar.svelte';
	import PortalNav from '$lib/components/employee-portal/PortalNav.svelte';

	interface Props {
		children: Snippet;
	}

	let { children }: Props = $props();

	// Check if current page is auth page (no header/nav needed)
	const isAuthPage = $derived($page.url.pathname.startsWith('/employee/auth'));

	// Mock data for static UI
	const companyName = 'Acme Corporation';
	const employeeName = 'Sarah Johnson';

	function handleSignOut() {
		// TODO: Implement sign out logic
		console.log('Sign out clicked');
	}
</script>

<div class="portal-layout" class:auth-layout={isAuthPage}>
	{#if !isAuthPage}
		<PortalHeader {companyName} {employeeName} onSignOut={handleSignOut} />

		<div class="portal-body">
			<PortalSidebar />

			<main class="portal-main">
				{@render children()}
			</main>
		</div>

		<PortalNav />
	{:else}
		<!-- Auth pages get full-screen layout without nav -->
		<main class="auth-main">
			{@render children()}
		</main>
	{/if}
</div>

<style>
	.portal-layout {
		min-height: 100vh;
		background: var(--color-surface-100);
		display: flex;
		flex-direction: column;
	}

	.portal-layout.auth-layout {
		background: white;
	}

	.portal-body {
		display: flex;
		flex: 1;
		overflow: hidden;
	}

	.portal-main {
		flex: 1;
		overflow-y: auto;
		padding: var(--spacing-6);
		padding-bottom: calc(var(--spacing-6) + 80px); /* Account for mobile bottom nav */
	}

	/* Desktop: no extra padding for bottom nav */
	@media (min-width: 768px) {
		.portal-main {
			padding-bottom: var(--spacing-6);
		}
	}

	.auth-main {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-6);
	}
</style>

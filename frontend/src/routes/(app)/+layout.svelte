<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import type { Snippet } from 'svelte';
	import AppShell from '$lib/components/layout/AppShell.svelte';
	import { initializeAuth, logout, authState } from '$lib/stores/auth.svelte';

	interface Props {
		children: Snippet;
	}

	let { children }: Props = $props();

	// Local UI state
	let sidebarCollapsed = $state(false);
	let isReady = $state(false);

	onMount(async () => {
		// Initialize auth
		await initializeAuth();

		// Check if user is authenticated
		if (!authState.isAuthenticated && !authState.isLoading) {
			goto('/login');
			return;
		}

		isReady = true;
	});

	function handleToggleSidebar() {
		sidebarCollapsed = !sidebarCollapsed;
	}

	async function handleLogout() {
		await logout();
		goto('/login');
	}

	// Derived values for user display
	// Supabase User stores name in user_metadata.name or user_metadata.full_name
	const userName = $derived(
		authState.user?.user_metadata?.name ||
			authState.user?.user_metadata?.full_name ||
			authState.user?.email?.split('@')[0] ||
			'User'
	);
	const companyName = $derived('My Company'); // TODO: Get from company store
</script>

{#if authState.isLoading}
	<!-- Loading state -->
	<div class="loading-page">
		<div class="loading-content">
			<div class="spinner"></div>
			<p class="loading-text">Loading...</p>
		</div>
	</div>
{:else if !authState.isAuthenticated}
	<!-- Redirect happening -->
	<div class="loading-page">
		<div class="loading-content">
			<div class="spinner"></div>
			<p class="loading-text">Redirecting to login...</p>
		</div>
	</div>
{:else if isReady}
	<AppShell
		{userName}
		{companyName}
		{sidebarCollapsed}
		onLogout={handleLogout}
		onToggleSidebar={handleToggleSidebar}
	>
		{@render children()}
	</AppShell>
{/if}

<style>
	.loading-page {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--color-surface-50);
	}

	.loading-content {
		text-align: center;
	}

	.spinner {
		width: 48px;
		height: 48px;
		border: 3px solid var(--color-surface-200);
		border-top-color: var(--color-primary-500);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
		margin: 0 auto var(--spacing-4);
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.loading-text {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0;
	}
</style>

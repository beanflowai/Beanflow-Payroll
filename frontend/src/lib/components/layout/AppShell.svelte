<script lang="ts">
	import type { Snippet } from 'svelte';
	import { navigating } from '$app/stores';
	import Sidebar from './Sidebar.svelte';
	import Header from './Header.svelte';

	interface Props {
		userName?: string;
		companyName?: string;
		sidebarCollapsed?: boolean;
		isLoading?: boolean;
		onLogout?: () => void;
		onToggleSidebar?: () => void;
		onAddCompany?: () => void;
		children: Snippet;
	}

	let {
		userName = 'User',
		companyName = 'My Company',
		sidebarCollapsed = false,
		isLoading = false,
		onLogout,
		onToggleSidebar,
		onAddCompany,
		children
	}: Props = $props();

	// Show loading indicator during navigation
	const isNavigating = $derived($navigating !== null || isLoading);
</script>

<div class="app-shell">
	<!-- Navigation Progress Bar -->
	{#if isNavigating}
		<div class="nav-progress-bar">
			<div class="nav-progress-indicator"></div>
		</div>
	{/if}

	<!-- Mobile Header (only visible on mobile) -->
	<div class="mobile-header-wrapper">
		<Header {userName} {companyName} {onLogout} />
	</div>

	<div class="app-layout" class:sidebar-collapsed={sidebarCollapsed}>
		<!-- Left Sidebar (hidden on mobile) -->
		<Sidebar collapsed={sidebarCollapsed} onToggleCollapse={onToggleSidebar} {onAddCompany} />

		<!-- Main Content Area -->
		<div class="main-area">
			<!-- Desktop Header -->
			<div class="desktop-header">
				<Header {userName} {companyName} {onLogout} />
			</div>

			<!-- Page Content -->
			<main class="main-content" class:loading={isNavigating}>
				{@render children()}
			</main>
		</div>
	</div>
</div>

<style>
	.app-shell {
		min-height: 100vh;
		background: var(--color-surface-50);
		position: relative;
	}

	/* Navigation Progress Bar */
	.nav-progress-bar {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		height: 3px;
		z-index: 9999;
		background: var(--color-surface-200);
		overflow: hidden;
	}

	.nav-progress-indicator {
		height: 100%;
		width: 30%;
		background: linear-gradient(
			90deg,
			var(--color-primary-400),
			var(--color-primary-600),
			var(--color-primary-400)
		);
		animation: progress 1.5s ease-in-out infinite;
	}

	@keyframes progress {
		0% {
			transform: translateX(-100%);
		}
		100% {
			transform: translateX(400%);
		}
	}

	.mobile-header-wrapper {
		display: none;
	}

	.app-layout {
		display: flex;
		min-height: 100vh;
	}

	.main-area {
		flex: 1;
		display: flex;
		flex-direction: column;
		min-width: 0; /* Allow flex item to shrink below content size */
	}

	.desktop-header {
		display: block;
	}

	.main-content {
		flex: 1;
		padding: var(--spacing-6);
		overflow-y: auto;
		transition: opacity 0.15s ease-out;
	}

	.main-content.loading {
		opacity: 0.7;
		pointer-events: none;
	}

	/* Responsive */
	@media (max-width: 1024px) {
		.mobile-header-wrapper {
			display: block;
		}

		.desktop-header {
			display: none;
		}

		.main-content {
			padding: var(--spacing-4);
			padding-top: calc(var(--spacing-4) + 64px); /* Account for mobile header */
		}
	}
</style>

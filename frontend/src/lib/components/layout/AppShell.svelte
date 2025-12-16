<script lang="ts">
	import type { Snippet } from 'svelte';
	import Sidebar from './Sidebar.svelte';
	import Header from './Header.svelte';

	interface Props {
		userName?: string;
		companyName?: string;
		sidebarCollapsed?: boolean;
		onLogout?: () => void;
		onToggleSidebar?: () => void;
		children: Snippet;
	}

	let {
		userName = 'User',
		companyName = 'My Company',
		sidebarCollapsed = false,
		onLogout,
		onToggleSidebar,
		children
	}: Props = $props();
</script>

<div class="app-shell">
	<!-- Mobile Header (only visible on mobile) -->
	<Header {userName} {companyName} {onLogout} />

	<div class="app-layout" class:sidebar-collapsed={sidebarCollapsed}>
		<!-- Left Sidebar (hidden on mobile) -->
		<Sidebar collapsed={sidebarCollapsed} onToggleCollapse={onToggleSidebar} />

		<!-- Main Content Area -->
		<div class="main-area">
			<!-- Desktop Header -->
			<div class="desktop-header">
				<Header {userName} {companyName} {onLogout} />
			</div>

			<!-- Page Content -->
			<main class="main-content">
				{@render children()}
			</main>
		</div>
	</div>
</div>

<style>
	.app-shell {
		min-height: 100vh;
		background: var(--color-surface-50);
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
	}

	/* Responsive */
	@media (max-width: 1024px) {
		.desktop-header {
			display: none;
		}

		.main-content {
			padding: var(--spacing-4);
			padding-top: calc(var(--spacing-4) + 64px); /* Account for mobile header */
		}
	}
</style>

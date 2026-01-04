<script lang="ts">
	/**
	 * PortalSidebar - Employee Portal Desktop Sidebar Navigation
	 * Shows navigation links for desktop view
	 */
	import { page } from '$app/stores';

	interface Props {
		/** Company slug from URL - required for navigation links */
		slug: string;
	}

	let { slug }: Props = $props();

	interface NavItem {
		id: string;
		label: string;
		path: string; // Relative path after /employee/{slug}
		icon: 'home' | 'paystubs' | 'profile' | 'leave';
	}

	const navItems: NavItem[] = [
		{ id: 'home', label: 'Dashboard', path: '', icon: 'home' },
		{ id: 'paystubs', label: 'Paystubs', path: '/paystubs', icon: 'paystubs' },
		{ id: 'profile', label: 'My Profile', path: '/profile', icon: 'profile' },
		{ id: 'leave', label: 'Leave Balances', path: '/leave', icon: 'leave' }
	];

	// Build href with slug (slug is required)
	function getHref(path: string): string {
		return `/employee/${slug}${path}`;
	}

	function isActive(path: string, currentPath: string): boolean {
		const href = getHref(path);
		if (path === '') {
			// Dashboard: exact match or trailing slash
			return currentPath === href || currentPath === href + '/';
		}
		return currentPath.startsWith(href);
	}
</script>

<aside class="portal-sidebar">
	<nav class="sidebar-nav">
		{#each navItems as item (item.id)}
			<a
				href={getHref(item.path)}
				class="nav-item"
				class:active={isActive(item.path, $page.url.pathname)}
				aria-current={isActive(item.path, $page.url.pathname) ? 'page' : undefined}
			>
				<span class="nav-icon">
					{#if item.icon === 'home'}
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
							<polyline points="9,22 9,12 15,12 15,22" />
						</svg>
					{:else if item.icon === 'paystubs'}
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
							<polyline points="14,2 14,8 20,8" />
							<line x1="16" y1="13" x2="8" y2="13" />
							<line x1="16" y1="17" x2="8" y2="17" />
							<polyline points="10,9 9,9 8,9" />
						</svg>
					{:else if item.icon === 'profile'}
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
							<circle cx="12" cy="7" r="4" />
						</svg>
					{:else if item.icon === 'leave'}
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
							<line x1="16" y1="2" x2="16" y2="6" />
							<line x1="8" y1="2" x2="8" y2="6" />
							<line x1="3" y1="10" x2="21" y2="10" />
						</svg>
					{/if}
				</span>
				<span class="nav-label">{item.label}</span>
			</a>
		{/each}
	</nav>
</aside>

<style>
	.portal-sidebar {
		width: 220px;
		background: white;
		border-right: 1px solid var(--color-surface-200);
		padding: var(--spacing-4);
		display: none;
		flex-direction: column;
		height: calc(100vh - 64px);
	}

	/* Show sidebar on desktop */
	@media (min-width: 768px) {
		.portal-sidebar {
			display: flex;
		}
	}

	.sidebar-nav {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.nav-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-3) var(--spacing-4);
		text-decoration: none;
		color: var(--color-surface-600);
		border-radius: var(--radius-md);
		transition: all var(--transition-fast);
	}

	.nav-item:hover {
		background: var(--color-surface-100);
		color: var(--color-surface-800);
	}

	.nav-item.active {
		background: var(--color-primary-50);
		color: var(--color-primary-600);
	}

	.nav-icon {
		width: 20px;
		height: 20px;
		flex-shrink: 0;
	}

	.nav-icon svg {
		width: 100%;
		height: 100%;
	}

	.nav-label {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-regular);
	}

	.nav-item.active .nav-label {
		font-weight: var(--font-weight-medium);
	}
</style>

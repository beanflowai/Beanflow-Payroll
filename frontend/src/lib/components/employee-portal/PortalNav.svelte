<script lang="ts">
	/**
	 * PortalNav - Employee Portal Bottom Navigation (Mobile-First)
	 * Tab-based navigation for mobile, can be adapted for desktop sidebar
	 */
	import { page } from '$app/stores';

	interface NavItem {
		id: string;
		label: string;
		href: string;
		icon: 'home' | 'paystubs' | 'profile' | 'settings';
	}

	const navItems: NavItem[] = [
		{ id: 'home', label: 'Home', href: '/employee', icon: 'home' },
		{ id: 'paystubs', label: 'Paystubs', href: '/employee/paystubs', icon: 'paystubs' },
		{ id: 'profile', label: 'Profile', href: '/employee/profile', icon: 'profile' },
		{ id: 'leave', label: 'Leave', href: '/employee/leave', icon: 'settings' }
	];

	function isActive(href: string, currentPath: string): boolean {
		if (href === '/employee') {
			return currentPath === '/employee' || currentPath === '/employee/';
		}
		return currentPath.startsWith(href);
	}
</script>

<nav class="portal-nav">
	{#each navItems as item}
		<a
			href={item.href}
			class="nav-item"
			class:active={isActive(item.href, $page.url.pathname)}
			aria-current={isActive(item.href, $page.url.pathname) ? 'page' : undefined}
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
				{:else if item.icon === 'settings'}
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

<style>
	.portal-nav {
		display: flex;
		align-items: center;
		justify-content: space-around;
		background: white;
		border-top: 1px solid var(--color-surface-200);
		padding: var(--spacing-2) 0;
		position: fixed;
		bottom: 0;
		left: 0;
		right: 0;
		z-index: var(--z-navigation);
	}

	.nav-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-1);
		padding: var(--spacing-2) var(--spacing-4);
		text-decoration: none;
		color: var(--color-surface-500);
		transition: color var(--transition-fast);
		border-radius: var(--radius-md);
	}

	.nav-item:hover {
		color: var(--color-surface-700);
	}

	.nav-item.active {
		color: var(--color-primary-500);
	}

	.nav-icon {
		width: 24px;
		height: 24px;
	}

	.nav-icon svg {
		width: 100%;
		height: 100%;
	}

	.nav-label {
		font-size: var(--font-size-caption-text);
		font-weight: var(--font-weight-medium);
	}

	/* Desktop: Hide bottom nav, could show sidebar instead */
	@media (min-width: 768px) {
		.portal-nav {
			display: none;
		}
	}
</style>

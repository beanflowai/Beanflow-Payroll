<script lang="ts">
	import { page } from '$app/stores';
	import { navigationItems } from './navigation';

	interface Props {
		userName?: string;
		companyName?: string;
		onLogout?: () => void;
	}

	let { userName = 'User', companyName = 'My Company', onLogout }: Props = $props();

	let userMenuOpen = $state(false);
	let mobileMenuOpen = $state(false);

	const currentPath = $derived($page.url.pathname);

	function isActive(href: string): boolean {
		if (href === '/dashboard') {
			return currentPath === '/dashboard';
		}
		return currentPath.startsWith(href);
	}

	function toggleUserMenu() {
		userMenuOpen = !userMenuOpen;
	}

	function toggleMobileMenu() {
		mobileMenuOpen = !mobileMenuOpen;
	}

	function handleLogout() {
		userMenuOpen = false;
		onLogout?.();
	}

	// Close menus when clicking outside
	function handleWindowClick(event: MouseEvent) {
		const target = event.target as HTMLElement;
		if (!target.closest('.user-menu-container')) {
			userMenuOpen = false;
		}
		if (!target.closest('.mobile-menu-container') && !target.closest('.mobile-menu-toggle')) {
			mobileMenuOpen = false;
		}
	}
</script>

<svelte:window onclick={handleWindowClick} />

<style>
	.header {
		background: rgba(255, 255, 255, 0.95);
		backdrop-filter: blur(10px);
		border-bottom: 1px solid var(--color-surface-200);
	}

	/* Desktop Header */
	.header-desktop {
		display: flex;
		align-items: center;
		justify-content: space-between;
		height: 64px;
		padding: 0 var(--spacing-6);
	}

	.header-left {
		display: flex;
		align-items: center;
	}

	.company-name {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.header-right {
		display: flex;
		align-items: center;
		gap: var(--spacing-4);
	}

	/* User Menu */
	.user-menu-container {
		position: relative;
	}

	.user-menu-trigger {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-3);
		background: transparent;
		border: none;
		border-radius: var(--radius-lg);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.user-menu-trigger:hover {
		background: var(--color-surface-100);
	}

	.user-avatar {
		width: 32px;
		height: 32px;
		border-radius: var(--radius-full);
		background: var(--gradient-primary);
		display: flex;
		align-items: center;
		justify-content: center;
		color: white;
		font-size: 14px;
	}

	.user-name {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
	}

	.user-menu-trigger i.fa-chevron-down {
		font-size: 10px;
		color: var(--color-surface-500);
		transition: transform var(--transition-fast);
	}

	.user-menu-trigger i.rotate {
		transform: rotate(180deg);
	}

	.user-dropdown {
		position: absolute;
		top: 100%;
		right: 0;
		margin-top: var(--spacing-2);
		min-width: 180px;
		background: white;
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-md3-2);
		overflow: hidden;
		z-index: 100;
	}

	.dropdown-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		width: 100%;
		padding: var(--spacing-3) var(--spacing-4);
		background: none;
		border: none;
		text-decoration: none;
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.dropdown-item:hover {
		background: var(--color-surface-100);
		color: var(--color-primary-600);
	}

	.dropdown-item i {
		width: 16px;
		text-align: center;
	}

	/* Mobile Header */
	.header-mobile {
		display: none;
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		z-index: 1000;
		background: rgba(255, 255, 255, 0.95);
		backdrop-filter: blur(10px);
		border-bottom: 1px solid var(--color-surface-200);
	}

	.mobile-nav-content {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--spacing-3) var(--spacing-4);
	}

	.mobile-brand {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
	}

	.brand-logo {
		width: 32px;
		height: 32px;
		background: var(--gradient-primary);
		border-radius: var(--radius-lg);
		display: flex;
		align-items: center;
		justify-content: center;
		color: white;
		font-size: 14px;
	}

	.brand-text {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.mobile-menu-toggle {
		background: none;
		border: none;
		font-size: var(--font-size-title-large);
		color: var(--color-surface-700);
		cursor: pointer;
		padding: var(--spacing-2);
		border-radius: var(--radius-md);
		transition: var(--transition-fast);
	}

	.mobile-menu-toggle:hover {
		background: var(--color-surface-100);
		color: var(--color-primary-600);
	}

	.mobile-menu {
		position: absolute;
		top: 100%;
		left: 0;
		right: 0;
		background: white;
		border-top: 1px solid var(--color-surface-200);
		box-shadow: var(--shadow-md3-2);
		max-height: calc(100vh - 64px);
		overflow-y: auto;
	}

	.mobile-company-section {
		padding: var(--spacing-4);
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.mobile-company-name {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.mobile-user-name {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	.mobile-menu-divider {
		height: 1px;
		background: var(--color-surface-200);
	}

	.mobile-menu-section {
		padding: var(--spacing-2);
	}

	.mobile-menu-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		width: 100%;
		padding: var(--spacing-3) var(--spacing-4);
		border-radius: var(--radius-md);
		background: none;
		border: none;
		text-decoration: none;
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.mobile-menu-item:hover {
		background: linear-gradient(135deg, var(--color-primary-50), var(--color-secondary-50));
		color: var(--color-primary-600);
	}

	.mobile-menu-item.active {
		background: var(--gradient-primary);
		color: white;
	}

	.mobile-menu-item.logout {
		color: var(--color-error-600);
	}

	.mobile-menu-item.logout:hover {
		background: var(--color-error-50);
		color: var(--color-error-700);
	}

	.mobile-menu-item i {
		width: 20px;
		text-align: center;
	}

	/* Responsive */
	@media (max-width: 1024px) {
		.header-desktop {
			display: none;
		}

		.header-mobile {
			display: block;
		}
	}
</style>

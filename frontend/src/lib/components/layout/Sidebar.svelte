<script lang="ts">
	import { page } from '$app/stores';
	import { navigationItems } from './navigation';

	interface Props {
		collapsed?: boolean;
		onToggleCollapse?: () => void;
	}

	let { collapsed = false, onToggleCollapse }: Props = $props();

	const currentPath = $derived($page.url.pathname);

	function isActive(href: string): boolean {
		// Exact match for specific routes to avoid parent/child conflicts
		if (href === '/dashboard' || href === '/payroll') {
			return currentPath === href;
		}
		return currentPath.startsWith(href);
	}
</script>

<aside class="sidebar" class:collapsed>
	<!-- Brand Section -->
	<div class="sidebar-brand">
		<div class="brand-logo">
			<i class="fas fa-money-check-alt"></i>
		</div>
		{#if !collapsed}
			<span class="brand-text">BeanFlow Payroll</span>
		{/if}
	</div>

	<!-- Navigation -->
	<nav class="sidebar-nav">
		{#each navigationItems as item (item.href)}
			<a
				href={item.href}
				class="nav-item"
				class:active={isActive(item.href)}
				title={collapsed ? item.label : undefined}
			>
				<i class="fas {item.icon}"></i>
				{#if !collapsed}
					<span>{item.label}</span>
				{/if}
			</a>
		{/each}
	</nav>

	<!-- Collapse Toggle -->
	<button class="sidebar-toggle" onclick={onToggleCollapse} aria-label="Toggle sidebar">
		<i class="fas" class:fa-chevron-left={!collapsed} class:fa-chevron-right={collapsed}></i>
	</button>
</aside>

<style>
	.sidebar {
		display: flex;
		flex-direction: column;
		width: 240px;
		height: 100vh;
		background: rgba(255, 255, 255, 0.95);
		backdrop-filter: blur(10px);
		border-right: 1px solid var(--color-surface-200);
		transition: width var(--transition-standard);
		position: relative;
	}

	.sidebar.collapsed {
		width: 72px;
	}

	/* Brand Section */
	.sidebar-brand {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		border-bottom: 1px solid var(--color-surface-200);
	}

	.brand-logo {
		width: 40px;
		height: 40px;
		min-width: 40px;
		background: var(--gradient-primary);
		border-radius: var(--radius-lg);
		display: flex;
		align-items: center;
		justify-content: center;
		color: white;
		font-size: 18px;
		box-shadow: var(--shadow-md3-1);
	}

	.brand-text {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		white-space: nowrap;
		overflow: hidden;
	}

	/* Navigation */
	.sidebar-nav {
		flex: 1;
		display: flex;
		flex-direction: column;
		padding: var(--spacing-3);
		gap: var(--spacing-1);
		overflow-y: auto;
	}

	.nav-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-3) var(--spacing-4);
		border-radius: var(--radius-lg);
		color: var(--color-surface-700);
		text-decoration: none;
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		transition: var(--transition-fast);
		white-space: nowrap;
	}

	.nav-item:hover {
		background: linear-gradient(135deg, var(--color-primary-50), var(--color-secondary-50));
		color: var(--color-primary-600);
	}

	.nav-item.active {
		background: var(--gradient-primary);
		color: white;
		box-shadow: var(--shadow-md3-1);
	}

	.nav-item i {
		width: 20px;
		text-align: center;
		font-size: 16px;
	}

	.sidebar.collapsed .nav-item {
		justify-content: center;
		padding: var(--spacing-3);
	}

	.sidebar.collapsed .nav-item span {
		display: none;
	}

	/* Toggle Button */
	.sidebar-toggle {
		position: absolute;
		bottom: var(--spacing-4);
		right: calc(-12px);
		width: 24px;
		height: 24px;
		border-radius: var(--radius-full);
		background: white;
		border: 1px solid var(--color-surface-200);
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--color-surface-600);
		box-shadow: var(--shadow-md3-1);
		transition: var(--transition-fast);
	}

	.sidebar-toggle:hover {
		background: var(--color-primary-50);
		color: var(--color-primary-600);
		border-color: var(--color-primary-200);
	}

	.sidebar-toggle i {
		font-size: 10px;
	}

	/* Responsive */
	@media (max-width: 1024px) {
		.sidebar {
			display: none;
		}
	}
</style>

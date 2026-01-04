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

<!-- Desktop Header -->
<header class="flex items-center justify-between h-16 px-6 bg-white/95 backdrop-blur-sm border-b border-surface-200">
	<div class="flex items-center">
		<span class="text-title-medium font-semibold text-surface-800">{companyName}</span>
	</div>
	<div class="flex items-center gap-4">
		<div class="user-menu-container relative">
			<button
				type="button"
				class="flex items-center gap-2 py-2 px-3 bg-transparent border-none rounded-lg cursor-pointer transition-fast hover:bg-surface-100"
				onclick={toggleUserMenu}
				aria-expanded={userMenuOpen}
				aria-haspopup="true"
				aria-label="User menu"
			>
				<span class="w-8 h-8 rounded-full bg-gradient-to-br from-primary-600 to-secondary-600 flex items-center justify-center text-white text-sm">
					<i class="fa-solid fa-user"></i>
				</span>
				<span class="text-body-content font-medium text-surface-700">{userName}</span>
				<i
					class="fa-solid fa-chevron-down text-[10px] text-surface-500 transition-transform duration-150"
					class:rotate-180={userMenuOpen}
				></i>
			</button>
			{#if userMenuOpen}
				<div class="absolute top-full right-0 mt-2 min-w-[180px] bg-white border border-surface-200 rounded-lg shadow-md3-2 overflow-hidden z-[100]" role="menu">
					<button
						type="button"
						class="flex items-center gap-3 w-full py-3 px-4 bg-transparent border-none no-underline text-body-content text-surface-700 cursor-pointer transition-fast hover:bg-surface-100 hover:text-primary-600"
						onclick={handleLogout}
						role="menuitem"
					>
						<i class="fa-solid fa-right-from-bracket w-4 text-center"></i>
						<span>Log out</span>
					</button>
				</div>
			{/if}
		</div>
	</div>
</header>

<!-- Mobile Header -->
<header class="hidden fixed top-0 left-0 right-0 z-[1000] bg-white/95 backdrop-blur-sm border-b border-surface-200">
	<nav class="flex items-center justify-between py-3 px-4">
		<div class="flex items-center gap-2">
			<div class="w-8 h-8 bg-gradient-to-br from-primary-600 to-secondary-600 rounded-lg flex items-center justify-center text-white text-sm">
				<i class="fa-solid fa-seedling"></i>
			</div>
			<span class="text-title-medium font-semibold text-surface-800">Beanflow</span>
		</div>
		<button
			type="button"
			class="mobile-menu-toggle bg-transparent border-none text-xl text-surface-700 cursor-pointer p-2 rounded-md transition-fast hover:bg-surface-100 hover:text-primary-600"
			onclick={toggleMobileMenu}
			aria-expanded={mobileMenuOpen}
			aria-label="Toggle menu"
		>
			<i class="fa-solid" class:fa-bars={!mobileMenuOpen} class:fa-xmark={mobileMenuOpen}></i>
		</button>
	</nav>
	{#if mobileMenuOpen}
		<div class="absolute top-full left-0 right-0 bg-white border-t border-surface-200 shadow-md3-2 max-h-[calc(100vh-64px)] overflow-y-auto">
			<div class="p-4 flex flex-col gap-1">
				<span class="text-body-content font-semibold text-surface-800">{companyName}</span>
				<span class="text-auxiliary-text text-surface-600">{userName}</span>
			</div>
			<div class="h-px bg-surface-200"></div>
			<div class="p-2">
				{#each navigationItems as item}
					<a
						href={item.href}
						class="flex items-center gap-3 w-full py-3 px-4 rounded-md bg-transparent border-none no-underline text-body-content text-surface-700 cursor-pointer transition-fast hover:bg-gradient-to-br hover:from-primary-50 hover:to-secondary-50 hover:text-primary-600"
						class:active={isActive(item.href)}
					>
						<i class="fa-solid {item.icon} w-5 text-center"></i>
						<span>{item.label}</span>
					</a>
				{/each}
			</div>
			<div class="h-px bg-surface-200"></div>
			<div class="p-2">
				<button
					type="button"
					class="flex items-center gap-3 w-full py-3 px-4 rounded-md bg-transparent border-none no-underline text-body-content text-error-600 cursor-pointer transition-fast hover:bg-error-50 hover:text-error-700"
					onclick={handleLogout}
				>
					<i class="fa-solid fa-right-from-bracket w-5 text-center"></i>
					<span>Log out</span>
				</button>
			</div>
		</div>
	{/if}
</header>

<style>
	/* Active state for mobile menu items - requires gradient background */
	.active {
		background: var(--gradient-primary);
		color: white;
	}
	.active:hover {
		background: var(--gradient-primary);
		color: white;
	}
</style>

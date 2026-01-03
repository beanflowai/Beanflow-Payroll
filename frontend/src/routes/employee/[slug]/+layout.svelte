<script lang="ts">
	/**
	 * Employee Portal Layout with Company Slug
	 * Loads company info from URL slug and provides context to child routes
	 */
	import { onMount, onDestroy, setContext } from 'svelte';
	import type { Snippet } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { supabase } from '$lib/api/supabase';
	import type { User, Subscription } from '@supabase/supabase-js';
	import PortalHeader from '$lib/components/employee-portal/PortalHeader.svelte';
	import PortalSidebar from '$lib/components/employee-portal/PortalSidebar.svelte';
	import PortalNav from '$lib/components/employee-portal/PortalNav.svelte';
	import { PORTAL_COMPANY_CONTEXT_KEY, type PortalCompanyContext } from '$lib/types/employee-portal';

	interface Props {
		children: Snippet;
	}

	let { children }: Props = $props();

	// Company info from slug
	let companyInfo = $state<{ id: string; companyName: string; slug: string; logoUrl?: string } | null>(null);
	let companyLoading = $state(true);
	let companyError = $state<string | null>(null);

	// Auth state
	let user = $state<User | null>(null);
	let isLoading = $state(true);
	let employeeData = $state<{ firstName: string; lastName: string; employeeId: string } | null>(null);
	let authSubscription: Subscription | null = null;

	// Get slug from URL (always defined in [slug] route, fallback for type safety)
	const slug = $derived($page.params.slug ?? '');

	// Check if current page is auth page (no header/nav needed)
	const isAuthPage = $derived($page.url.pathname.includes('/auth'));

	// Employee name from auth or fallback
	const employeeName = $derived(
		employeeData ? `${employeeData.firstName} ${employeeData.lastName}` : user?.email ?? ''
	);

	// Company name from loaded company info
	const companyName = $derived(companyInfo?.companyName ?? 'Employee Portal');

	// Provide company context to child components
	setContext<PortalCompanyContext>(PORTAL_COMPANY_CONTEXT_KEY, {
		get company() { return companyInfo; },
		get slug() { return slug ?? ''; },
		get employeeId() { return employeeData?.employeeId ?? null; }
	});

	onMount(async () => {
		// Load company info from slug first
		await loadCompanyInfo();

		// Check initial auth state
		const { data: { session } } = await supabase.auth.getSession();
		user = session?.user ?? null;
		if (user && companyInfo) {
			await fetchEmployeeData(user.email!, companyInfo.id);
		}
		isLoading = false;

		// Redirect to auth if not logged in (and not on auth page)
		if (!user && !isAuthPage) {
			goto(`/employee/${slug}/auth`);
		}

		// Subscribe to auth changes
		const { data } = supabase.auth.onAuthStateChange(async (_event, session) => {
			user = session?.user ?? null;
			if (user && companyInfo) {
				await fetchEmployeeData(user.email!, companyInfo.id);
			} else {
				employeeData = null;
				// Redirect to auth on sign out
				if (!isAuthPage) {
					goto(`/employee/${slug}/auth`);
				}
			}
		});
		authSubscription = data.subscription;
	});

	onDestroy(() => {
		authSubscription?.unsubscribe();
	});

	async function loadCompanyInfo() {
		companyLoading = true;
		companyError = null;

		try {
			// Use public_company_portal_info view (exposes only safe fields)
			const { data, error } = await supabase
				.from('public_company_portal_info')
				.select('id, company_name, slug, logo_url')
				.eq('slug', slug)
				.single();

			if (error || !data) {
				console.error('Failed to load company info:', error?.message);
				companyError = 'Company portal not found';
				return;
			}

			companyInfo = {
				id: data.id,
				companyName: data.company_name,
				slug: data.slug,
				logoUrl: data.logo_url
			};
		} catch (err) {
			console.error('Failed to load company info:', err);
			companyError = 'Failed to load company information';
		} finally {
			companyLoading = false;
		}
	}

	async function fetchEmployeeData(email: string, companyId: string) {
		try {
			// Get employee record by email scoped to this company
			const { data, error } = await supabase
				.from('employees')
				.select('id, first_name, last_name')
				.eq('email', email)
				.eq('company_id', companyId)
				.not('portal_invited_at', 'is', null)
				.single();

			if (!error && data) {
				employeeData = {
					firstName: data.first_name,
					lastName: data.last_name,
					employeeId: data.id
				};
			}
		} catch (err) {
			console.error('Failed to fetch employee data:', err);
		}
	}

	async function handleSignOut() {
		try {
			const { error } = await supabase.auth.signOut();
			if (error) {
				console.error('Sign out error:', error);
			}
		} catch (err) {
			console.error('Sign out failed:', err);
		}
		// Always redirect to auth page, even if signOut had issues
		goto(`/employee/${slug}/auth`);
	}
</script>

<div class="portal-layout" class:auth-layout={isAuthPage}>
	{#if companyLoading}
		<!-- Loading company info -->
		<div class="loading-container">
			<div class="loading-spinner"></div>
		</div>
	{:else if companyError}
		<!-- Company not found -->
		<div class="error-container">
			<div class="error-card">
				<svg class="error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<circle cx="12" cy="12" r="10" />
					<line x1="12" y1="8" x2="12" y2="12" />
					<line x1="12" y1="16" x2="12.01" y2="16" />
				</svg>
				<h1 class="error-title">Portal Not Found</h1>
				<p class="error-message">{companyError}</p>
				<p class="error-hint">Please check the URL or contact your employer for the correct portal link.</p>
			</div>
		</div>
	{:else if isAuthPage}
		<!-- Auth pages get full-screen layout without nav -->
		<main class="auth-main">
			{@render children()}
		</main>
	{:else if isLoading}
		<!-- Loading auth state -->
		<div class="loading-container">
			<div class="loading-spinner"></div>
		</div>
	{:else if user}
		<PortalHeader {companyName} {employeeName} onSignOut={handleSignOut} />

		<div class="portal-body">
			<PortalSidebar {slug} />

			<main class="portal-main">
				{@render children()}
			</main>
		</div>

		<PortalNav {slug} />
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
		padding-bottom: calc(var(--spacing-6) + 80px);
	}

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

	.loading-container {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.loading-spinner {
		width: 40px;
		height: 40px;
		border: 3px solid var(--color-surface-200);
		border-top-color: var(--color-primary-500);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	.error-container {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-6);
	}

	.error-card {
		text-align: center;
		max-width: 400px;
	}

	.error-icon {
		width: 64px;
		height: 64px;
		color: var(--color-error-500);
		margin-bottom: var(--spacing-4);
	}

	.error-title {
		font-size: var(--font-size-headline-minimum);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-900);
		margin: 0 0 var(--spacing-2) 0;
	}

	.error-message {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0 0 var(--spacing-4) 0;
	}

	.error-hint {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
		margin: 0;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
</style>

<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { login, initializeAuth, authState } from '$lib/stores/auth.svelte';
	import { AuthLayout, AuthCard, GoogleLoginButton } from '$lib/components/auth';

	let isLoggingIn = $state(false);

	onMount(async () => {
		await initializeAuth();

		// If already authenticated, redirect to dashboard
		if (authState.isAuthenticated) {
			goto('/dashboard');
			return;
		}

		// Check for auto_login parameter (from Marketing redirect)
		// This enables seamless OAuth flow without PKCE cross-domain issues
		if (browser) {
			const urlParams = new URLSearchParams(window.location.search);
			const autoLogin = urlParams.get('auto_login');

			if (autoLogin === 'google') {
				// Clear auto_login parameter to prevent re-triggering on page refresh
				// Preserve other query params (e.g., ?next=) and respect base path
				const url = new URL(window.location.href);
				url.searchParams.delete('auto_login');
				history.replaceState({}, '', url.pathname + url.search);
				// Automatically initiate Google OAuth
				isLoggingIn = true;
				await login();
				return;
			}
		}
	});

	async function handleGoogleLogin() {
		isLoggingIn = true;
		await login();
		// Note: OAuth redirects, so isLoggingIn will reset on page reload
	}
</script>

<svelte:head>
	<title>Login - BeanFlow Payroll</title>
</svelte:head>

<AuthLayout>
	<!-- Logo & Branding -->
	<div class="text-center mb-8 max-sm:mb-6 animate-fade-in-down">
		<div
			class="w-18 h-18 max-sm:w-16 max-sm:h-16 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-2xl flex items-center justify-center mx-auto mb-4 text-white shadow-[0_10px_25px_rgba(37,99,235,0.3),0_4px_10px_rgba(37,99,235,0.2)]"
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				viewBox="0 0 24 24"
				fill="currentColor"
				class="w-10 h-10 max-sm:w-8 max-sm:h-8"
				aria-hidden="true"
			>
				<path
					d="M2.273 5.625A4.483 4.483 0 015.25 4.5h13.5c1.141 0 2.183.425 2.977 1.125A4.483 4.483 0 0122.5 6.75v10.5a4.483 4.483 0 01-1.273 3.375A4.483 4.483 0 0118.75 21H5.25a4.483 4.483 0 01-3.375-1.273A4.483 4.483 0 011.5 17.25V6.75a4.483 4.483 0 011.273-3.375z"
				/>
				<path d="M12 7.5a2.25 2.25 0 100 4.5 2.25 2.25 0 000-4.5z" fill-opacity="0.6" />
				<path
					d="M7.5 15a4.5 4.5 0 019 0v.75a.75.75 0 01-.75.75h-7.5a.75.75 0 01-.75-.75V15z"
					fill-opacity="0.4"
				/>
			</svg>
		</div>
		<h1 class="text-headline-minimum max-sm:text-title-large font-semibold text-surface-800 mb-2 leading-tight">
			BeanFlow Payroll
		</h1>
		<p class="text-body-content text-surface-600 leading-relaxed">
			Canadian Payroll Management Made Simple
		</p>
	</div>

	<!-- Login Card -->
	<AuthCard
		title="Welcome Back"
		subtitle="Sign in to manage your payroll"
		error={authState.error}
		loading={isLoggingIn || authState.isLoading}
	>
		<GoogleLoginButton
			onClick={handleGoogleLogin}
			loading={isLoggingIn}
			disabled={authState.isLoading}
		/>

		<p class="text-auxiliary-text text-surface-500 text-center mt-4 leading-relaxed">
			By signing in, you agree to our
			<a
				href="/terms"
				class="text-primary-600 font-medium no-underline hover:text-primary-700 hover:underline focus-visible:outline-2 focus-visible:outline-primary-500 focus-visible:outline-offset-1 rounded-sm transition-colors"
			>
				Terms of Service
			</a>
			and
			<a
				href="/privacy"
				class="text-primary-600 font-medium no-underline hover:text-primary-700 hover:underline focus-visible:outline-2 focus-visible:outline-primary-500 focus-visible:outline-offset-1 rounded-sm transition-colors"
			>
				Privacy Policy
			</a>
		</p>
	</AuthCard>

	<!-- Features Preview -->
	<div
		class="flex justify-center gap-6 max-sm:gap-4 mt-8 max-sm:mt-6 max-sm:flex-wrap animate-fade-in-up"
		style="animation-delay: 0.2s;"
	>
		<div class="flex flex-col items-center gap-2 text-surface-600 text-center max-sm:flex-1 max-sm:min-w-20">
			<div
				class="w-10 h-10 max-sm:w-9 max-sm:h-9 flex items-center justify-center text-primary-500 bg-primary-500/10 rounded-lg p-2"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 24 24"
					fill="currentColor"
					class="w-6 h-6 max-sm:w-5 max-sm:h-5"
					aria-hidden="true"
				>
					<path
						d="M12 2.25a.75.75 0 01.75.75v2.25a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM7.5 12a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM18.894 6.166a.75.75 0 00-1.06-1.06l-1.591 1.59a.75.75 0 101.06 1.061l1.591-1.59zM21.75 12a.75.75 0 01-.75.75h-2.25a.75.75 0 010-1.5H21a.75.75 0 01.75.75zM17.834 18.894a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 10-1.061 1.06l1.59 1.591zM12 18a.75.75 0 01.75.75V21a.75.75 0 01-1.5 0v-2.25A.75.75 0 0112 18zM7.758 17.303a.75.75 0 00-1.061-1.06l-1.591 1.59a.75.75 0 001.06 1.061l1.591-1.59zM6 12a.75.75 0 01-.75.75H3a.75.75 0 010-1.5h2.25A.75.75 0 016 12zM6.697 7.757a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 00-1.061 1.06l1.59 1.591z"
					/>
				</svg>
			</div>
			<span class="text-auxiliary-text font-medium text-surface-600 leading-snug">
				Automated Calculations
			</span>
		</div>
		<div class="flex flex-col items-center gap-2 text-surface-600 text-center max-sm:flex-1 max-sm:min-w-20">
			<div
				class="w-10 h-10 max-sm:w-9 max-sm:h-9 flex items-center justify-center text-primary-500 bg-primary-500/10 rounded-lg p-2"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 24 24"
					fill="currentColor"
					class="w-6 h-6 max-sm:w-5 max-sm:h-5"
					aria-hidden="true"
				>
					<path
						fill-rule="evenodd"
						d="M8.603 3.799A4.49 4.49 0 0112 2.25c1.357 0 2.573.6 3.397 1.549a4.49 4.49 0 013.498 1.307 4.491 4.491 0 011.307 3.497A4.49 4.49 0 0121.75 12a4.49 4.49 0 01-1.549 3.397 4.491 4.491 0 01-1.307 3.497 4.491 4.491 0 01-3.497 1.307A4.49 4.49 0 0112 21.75a4.49 4.49 0 01-3.397-1.549 4.49 4.49 0 01-3.498-1.306 4.491 4.491 0 01-1.307-3.498A4.49 4.49 0 012.25 12c0-1.357.6-2.573 1.549-3.397a4.49 4.49 0 011.307-3.497 4.49 4.49 0 013.497-1.307zm5.033 9.26a.75.75 0 10-1.06-1.06l-2.25 2.25a.75.75 0 001.06 1.06l2.25-2.25zm-5.816-3.116a.75.75 0 10-1.06 1.06l5.146 5.147a.75.75 0 001.06-1.06l-5.146-5.147z"
						clip-rule="evenodd"
					/>
				</svg>
			</div>
			<span class="text-auxiliary-text font-medium text-surface-600 leading-snug">
				CRA Compliant
			</span>
		</div>
		<div class="flex flex-col items-center gap-2 text-surface-600 text-center max-sm:flex-1 max-sm:min-w-20">
			<div
				class="w-10 h-10 max-sm:w-9 max-sm:h-9 flex items-center justify-center text-primary-500 bg-primary-500/10 rounded-lg p-2"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 24 24"
					fill="currentColor"
					class="w-6 h-6 max-sm:w-5 max-sm:h-5"
					aria-hidden="true"
				>
					<path
						fill-rule="evenodd"
						d="M5.625 1.5c-1.036 0-1.875.84-1.875 1.875v17.25c0 1.035.84 1.875 1.875 1.875h12.75c1.035 0 1.875-.84 1.875-1.875V12.75A3.75 3.75 0 0016.5 9h-1.875a1.875 1.875 0 01-1.875-1.875V5.25A3.75 3.75 0 009 1.5H5.625zM7.5 15a.75.75 0 01.75-.75h7.5a.75.75 0 010 1.5h-7.5A.75.75 0 017.5 15zm.75 2.25a.75.75 0 000 1.5H12a.75.75 0 000-1.5H8.25z"
						clip-rule="evenodd"
					/>
					<path
						d="M12.971 1.816A5.23 5.23 0 0114.25 5.25v1.875c0 .207.168.375.375.375H16.5a5.23 5.23 0 013.434 1.279 9.768 9.768 0 00-6.963-6.963z"
					/>
				</svg>
			</div>
			<span class="text-auxiliary-text font-medium text-surface-600 leading-snug">
				Digital Paystubs
			</span>
		</div>
	</div>
</AuthLayout>

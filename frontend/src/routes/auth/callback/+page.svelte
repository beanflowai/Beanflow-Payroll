<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { supabase } from '$lib/api/supabase';
	import { browser } from '$app/environment';

	let status = $state<'loading' | 'success' | 'error'>('loading');
	let errorMessage = $state<string | null>(null);

	onMount(async () => {
		try {
			// Supabase automatically handles the OAuth callback tokens in the URL
			const {
				data: { session },
				error
			} = await supabase.auth.getSession();

			if (error) {
				status = 'error';
				errorMessage = error.message;
				setTimeout(() => goto('/login'), 3000);
				return;
			}

			if (session) {
				// Clear retry flag on successful authentication
				if (browser) sessionStorage.removeItem('oauth_retry');
				status = 'success';
				goto('/dashboard');
			} else {
				// Cross-domain PKCE issue: OAuth initiated from Marketing cannot get session here
				// Check if we've already retried (prevent infinite loop)
				const hasRetried = browser && sessionStorage.getItem('oauth_retry');

				if (hasRetried) {
					// Already retried but still failed, show error
					sessionStorage.removeItem('oauth_retry');
					status = 'error';
					errorMessage = 'Authentication failed. Please try again.';
					setTimeout(() => goto('/login'), 3000);
					return;
				}

				// Mark as retried before initiating OAuth
				if (browser) sessionStorage.setItem('oauth_retry', 'true');

				// Auto-retry OAuth from Payroll domain (silent authentication)
				console.log('No session found, auto-retrying OAuth from Payroll domain...');

				const { error: retryError } = await supabase.auth.signInWithOAuth({
					provider: 'google',
					options: {
						redirectTo: `${window.location.origin}/auth/callback`
						// Note: Not setting prompt parameter allows Google to pass through silently
						// since user just selected their account moments ago
					}
				});

				if (retryError) {
					sessionStorage.removeItem('oauth_retry');
					status = 'error';
					errorMessage = retryError.message;
					setTimeout(() => goto('/login'), 3000);
				}
				// If successful, browser will redirect to Google OAuth
			}
		} catch (err) {
			if (browser) sessionStorage.removeItem('oauth_retry');
			status = 'error';
			errorMessage = err instanceof Error ? err.message : 'Authentication failed';
			setTimeout(() => goto('/login'), 3000);
		}
	});
</script>

<div class="callback-container">
	{#if status === 'loading'}
		<div class="loading">
			<div class="spinner"></div>
			<p>Completing login...</p>
		</div>
	{:else if status === 'error'}
		<div class="error">
			<p>Login failed: {errorMessage}</p>
			<p>Redirecting to login page...</p>
		</div>
	{/if}
</div>

<style>
	.callback-container {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 100vh;
		background-color: var(--color-surface-50);
	}

	.loading,
	.error {
		text-align: center;
		padding: var(--spacing-6);
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-2);
	}

	.spinner {
		width: 40px;
		height: 40px;
		margin: 0 auto var(--spacing-4);
		border: 3px solid var(--color-surface-200);
		border-top-color: var(--color-primary-500);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	.error {
		color: var(--color-error-600);
	}

	p {
		margin: var(--spacing-2) 0;
		color: var(--color-surface-600);
	}
</style>

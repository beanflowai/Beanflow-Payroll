<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { supabase } from '$lib/api/supabase';

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
				status = 'success';
				goto('/dashboard');
			} else {
				status = 'error';
				errorMessage = 'No session found';
				setTimeout(() => goto('/login'), 3000);
			}
		} catch (err) {
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

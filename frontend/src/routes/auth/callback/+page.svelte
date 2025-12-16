<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { supabase } from '$lib/api/supabase';

	let status = $state<'loading' | 'success' | 'error'>('loading');
	let errorMessage = $state<string | null>(null);

	onMount(async () => {
		try {
			// Supabase automatically handles the OAuth callback tokens in the URL
			const { data: { session }, error } = await supabase.auth.getSession();

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
		background-color: var(--color-bg-secondary, #f5f5f5);
	}

	.loading, .error {
		text-align: center;
		padding: 2rem;
		background: white;
		border-radius: 8px;
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
	}

	.spinner {
		width: 40px;
		height: 40px;
		margin: 0 auto 1rem;
		border: 3px solid #e0e0e0;
		border-top-color: #4285f4;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.error {
		color: #d32f2f;
	}

	p {
		margin: 0.5rem 0;
		color: #666;
	}
</style>

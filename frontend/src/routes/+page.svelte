<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { initializeAuth, authState } from '$lib/stores/auth.svelte';

	onMount(async () => {
		await initializeAuth();

		if (authState.isAuthenticated) {
			// Authenticated user → Dashboard
			goto('/dashboard');
		} else {
			// Unauthenticated user → Login
			goto('/login');
		}
	});
</script>

<svelte:head>
	<title>BeanFlow Payroll</title>
</svelte:head>

<div class="loading-page">
	<div class="loading-content">
		<div class="logo">
			<i class="fas fa-money-check-alt"></i>
		</div>
		<div class="spinner"></div>
		<p class="loading-text">Loading BeanFlow Payroll...</p>
	</div>
</div>

<style>
	.loading-page {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		background: linear-gradient(135deg, var(--color-primary-50), var(--color-secondary-50));
	}

	.loading-content {
		text-align: center;
	}

	.logo {
		width: 64px;
		height: 64px;
		background: var(--gradient-primary);
		border-radius: var(--radius-2xl);
		display: flex;
		align-items: center;
		justify-content: center;
		margin: 0 auto var(--spacing-6);
		color: white;
		font-size: 28px;
		box-shadow: var(--shadow-md3-2);
	}

	.spinner {
		width: 40px;
		height: 40px;
		border: 3px solid var(--color-surface-200);
		border-top-color: var(--color-primary-500);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
		margin: 0 auto var(--spacing-4);
	}

	.loading-text {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0;
	}
</style>

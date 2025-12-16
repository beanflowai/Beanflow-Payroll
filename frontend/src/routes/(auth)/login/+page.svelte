<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { login, initializeAuth, authState } from '$lib/stores/auth.svelte';

	let isLoggingIn = $state(false);

	onMount(async () => {
		await initializeAuth();

		// If already authenticated, redirect to dashboard
		if (authState.isAuthenticated) {
			goto('/dashboard');
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

<div class="login-page">
	<div class="login-container">
		<!-- Logo & Branding -->
		<div class="login-header">
			<div class="logo">
				<i class="fas fa-money-check-alt"></i>
			</div>
			<h1 class="app-title">BeanFlow Payroll</h1>
			<p class="app-subtitle">Canadian Payroll Management Made Simple</p>
		</div>

		<!-- Login Card -->
		<div class="login-card">
			<h2 class="login-title">Welcome Back</h2>
			<p class="login-description">Sign in to manage your payroll</p>

			{#if authState.error}
				<div class="error-message">
					<i class="fas fa-exclamation-circle"></i>
					<span>{authState.error}</span>
				</div>
			{/if}

			<button
				class="google-login-btn"
				onclick={handleGoogleLogin}
				disabled={isLoggingIn || authState.isLoading}
			>
				{#if isLoggingIn}
					<div class="spinner"></div>
					<span>Signing in...</span>
				{:else}
					<svg class="google-icon" viewBox="0 0 24 24">
						<path
							d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
							fill="#4285F4"
						/>
						<path
							d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
							fill="#34A853"
						/>
						<path
							d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
							fill="#FBBC05"
						/>
						<path
							d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
							fill="#EA4335"
						/>
					</svg>
					<span>Continue with Google</span>
				{/if}
			</button>

			<p class="terms-text">
				By signing in, you agree to our
				<a href="/terms" class="link">Terms of Service</a>
				and
				<a href="/privacy" class="link">Privacy Policy</a>
			</p>
		</div>

		<!-- Features Preview -->
		<div class="features-section">
			<div class="feature">
				<i class="fas fa-calculator"></i>
				<span>Automated Calculations</span>
			</div>
			<div class="feature">
				<i class="fas fa-leaf"></i>
				<span>CRA Compliant</span>
			</div>
			<div class="feature">
				<i class="fas fa-file-invoice-dollar"></i>
				<span>Digital Paystubs</span>
			</div>
		</div>
	</div>
</div>

<style>
	.login-page {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		background: linear-gradient(135deg, var(--color-primary-50), var(--color-secondary-50));
		padding: var(--spacing-4);
	}

	.login-container {
		width: 100%;
		max-width: 400px;
	}

	.login-header {
		text-align: center;
		margin-bottom: var(--spacing-8);
	}

	.logo {
		width: 72px;
		height: 72px;
		background: var(--gradient-primary);
		border-radius: var(--radius-2xl);
		display: flex;
		align-items: center;
		justify-content: center;
		margin: 0 auto var(--spacing-4);
		color: white;
		font-size: 32px;
		box-shadow: var(--shadow-md3-2);
	}

	.app-title {
		font-size: var(--font-size-headline-minimum);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-2);
	}

	.app-subtitle {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0;
	}

	.login-card {
		background: white;
		border-radius: var(--radius-2xl);
		padding: var(--spacing-8);
		box-shadow: var(--shadow-md3-2);
		text-align: center;
	}

	.login-title {
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-2);
	}

	.login-description {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0 0 var(--spacing-6);
	}

	.error-message {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3);
		background: var(--color-error-50);
		border-radius: var(--radius-lg);
		color: var(--color-error-600);
		font-size: var(--font-size-body-content);
		margin-bottom: var(--spacing-4);
	}

	.google-login-btn {
		width: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		background: white;
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content-large);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.google-login-btn:hover:not(:disabled) {
		background: var(--color-surface-50);
		border-color: var(--color-surface-300);
		box-shadow: var(--shadow-md3-1);
	}

	.google-login-btn:disabled {
		opacity: 0.7;
		cursor: not-allowed;
	}

	.google-icon {
		width: 20px;
		height: 20px;
	}

	.spinner {
		width: 20px;
		height: 20px;
		border: 2px solid var(--color-surface-200);
		border-top-color: var(--color-primary-500);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.terms-text {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
		margin: var(--spacing-4) 0 0;
	}

	.link {
		color: var(--color-primary-600);
		text-decoration: none;
	}

	.link:hover {
		text-decoration: underline;
	}

	.features-section {
		display: flex;
		justify-content: center;
		gap: var(--spacing-6);
		margin-top: var(--spacing-8);
	}

	.feature {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-2);
		color: var(--color-surface-600);
		font-size: var(--font-size-auxiliary-text);
	}

	.feature i {
		font-size: 24px;
		color: var(--color-primary-500);
	}

	@media (max-width: 480px) {
		.features-section {
			flex-wrap: wrap;
		}

		.feature {
			flex: 1;
			min-width: 100px;
		}
	}
</style>

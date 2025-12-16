<script lang="ts">
	/**
	 * Employee Portal - Magic Link Verification Page
	 * Handles token verification from magic link email
	 */
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';

	let status = $state<'verifying' | 'success' | 'error' | 'expired'>('verifying');
	let errorMessage = $state('');

	onMount(async () => {
		const token = $page.url.searchParams.get('token');

		if (!token) {
			status = 'error';
			errorMessage = 'No verification token provided';
			return;
		}

		// Simulate token verification
		await new Promise((resolve) => setTimeout(resolve, 1500));

		// For demo purposes, randomly succeed or fail
		// In production, this would call the API
		const demoSuccess = true; // Set to false to test error state

		if (demoSuccess) {
			status = 'success';
			// Redirect to dashboard after brief success message
			setTimeout(() => {
				goto('/employee');
			}, 1500);
		} else {
			status = 'expired';
			errorMessage = 'This link has expired or has already been used';
		}
	});

	function handleRequestNewLink() {
		goto('/employee/auth');
	}
</script>

<div class="verify-container">
	<div class="verify-card">
		<!-- Logo -->
		<div class="logo-container">
			<svg class="logo" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
				<rect width="48" height="48" rx="12" fill="var(--color-primary-500)" />
				<path
					d="M12 24C12 17.3726 17.3726 12 24 12C30.6274 12 36 17.3726 36 24C36 30.6274 30.6274 36 24 36"
					stroke="white"
					stroke-width="3"
					stroke-linecap="round"
				/>
				<circle cx="24" cy="24" r="4" fill="white" />
			</svg>
		</div>

		{#if status === 'verifying'}
			<div class="status-content">
				<div class="spinner-large"></div>
				<h2 class="status-title">Verifying your link...</h2>
				<p class="status-text">Please wait while we sign you in</p>
			</div>
		{:else if status === 'success'}
			<div class="status-content">
				<div class="icon-container success">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M5 13l4 4L19 7"
						/>
					</svg>
				</div>
				<h2 class="status-title">Success!</h2>
				<p class="status-text">You're now signed in. Redirecting to your portal...</p>
			</div>
		{:else if status === 'expired'}
			<div class="status-content">
				<div class="icon-container warning">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
						<circle cx="12" cy="12" r="10" stroke-width="2" />
						<line x1="12" y1="8" x2="12" y2="12" stroke-width="2" stroke-linecap="round" />
						<circle cx="12" cy="16" r="1" fill="currentColor" />
					</svg>
				</div>
				<h2 class="status-title">Link Expired</h2>
				<p class="status-text">{errorMessage}</p>
				<button class="action-btn" onclick={handleRequestNewLink}> Request New Link </button>
			</div>
		{:else}
			<div class="status-content">
				<div class="icon-container error">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
						<circle cx="12" cy="12" r="10" stroke-width="2" />
						<line x1="15" y1="9" x2="9" y2="15" stroke-width="2" stroke-linecap="round" />
						<line x1="9" y1="9" x2="15" y2="15" stroke-width="2" stroke-linecap="round" />
					</svg>
				</div>
				<h2 class="status-title">Verification Failed</h2>
				<p class="status-text">{errorMessage}</p>
				<button class="action-btn" onclick={handleRequestNewLink}> Try Again </button>
			</div>
		{/if}
	</div>
</div>

<style>
	.verify-container {
		width: 100%;
		max-width: 420px;
	}

	.verify-card {
		background: white;
		border-radius: var(--radius-2xl);
		box-shadow: var(--shadow-md3-3);
		padding: var(--spacing-8);
		text-align: center;
	}

	.logo-container {
		margin-bottom: var(--spacing-6);
	}

	.logo {
		width: 64px;
		height: 64px;
		margin: 0 auto;
	}

	.status-content {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-4);
	}

	.spinner-large {
		width: 48px;
		height: 48px;
		border: 3px solid var(--color-surface-200);
		border-top-color: var(--color-primary-500);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.icon-container {
		width: 64px;
		height: 64px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.icon-container svg {
		width: 32px;
		height: 32px;
	}

	.icon-container.success {
		background: var(--color-success-100);
		color: var(--color-success-600);
	}

	.icon-container.warning {
		background: var(--color-warning-100);
		color: var(--color-warning-600);
	}

	.icon-container.error {
		background: var(--color-error-100);
		color: var(--color-error-600);
	}

	.status-title {
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-900);
		margin: 0;
	}

	.status-text {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0;
		line-height: 1.5;
	}

	.action-btn {
		margin-top: var(--spacing-4);
		padding: var(--spacing-3) var(--spacing-6);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: white;
		background: var(--color-primary-500);
		border: none;
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.action-btn:hover {
		background: var(--color-primary-600);
	}

	/* Mobile adjustments */
	@media (max-width: 480px) {
		.verify-card {
			padding: var(--spacing-6);
			border-radius: var(--radius-xl);
		}
	}
</style>

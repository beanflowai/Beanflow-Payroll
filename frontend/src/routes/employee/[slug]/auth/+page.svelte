<script lang="ts">
	/**
	 * Employee Portal - Login Page (with Company Slug)
	 * Email + OTP authentication using Supabase Auth
	 */
	import { getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { supabase } from '$lib/api/supabase';
	import { PORTAL_COMPANY_CONTEXT_KEY, type PortalCompanyContext } from '$lib/types/employee-portal';

	const portalContext = getContext<PortalCompanyContext>(PORTAL_COMPANY_CONTEXT_KEY);
	const slug = $derived($page.params.slug);

	let email = $state('');
	let isSubmitting = $state(false);
	let error = $state('');

	// Company info for display
	const companyName = $derived(portalContext?.company?.companyName ?? 'Employee Portal');

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = '';

		if (!email.trim()) {
			error = 'Please enter your email address';
			return;
		}

		if (!isValidEmail(email)) {
			error = 'Please enter a valid email address';
			return;
		}

		isSubmitting = true;

		try {
			// Send OTP via Supabase Auth
			const { error: authError } = await supabase.auth.signInWithOtp({
				email: email.trim(),
				options: {
					shouldCreateUser: false
				}
			});

			if (authError) {
				if (authError.message.includes('not allowed')) {
					error = 'This email is not registered. Please contact your employer for portal access.';
				} else {
					error = authError.message;
				}
				isSubmitting = false;
				return;
			}

			// Redirect to OTP verification page with slug
			goto(`/employee/${slug}/auth/verify?email=${encodeURIComponent(email.trim())}`);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to send verification code';
			isSubmitting = false;
		}
	}

	function isValidEmail(email: string): boolean {
		return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
	}
</script>

<div class="auth-container">
	<div class="auth-card">
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

		<h1 class="auth-title">{companyName}</h1>
		<p class="auth-subtitle">Employee Portal</p>

		<!-- Login Form -->
		<form class="auth-form" onsubmit={handleSubmit}>
			<p class="auth-instruction">Enter your work email to sign in:</p>

			<div class="form-group">
				<label for="email" class="form-label">Email</label>
				<input
					id="email"
					type="email"
					class="form-input"
					placeholder="sarah@example.com"
					bind:value={email}
					disabled={isSubmitting}
				/>
			</div>

			{#if error}
				<p class="error-message">{error}</p>
			{/if}

			<button type="submit" class="submit-btn" disabled={isSubmitting}>
				{#if isSubmitting}
					<span class="spinner"></span>
					Sending...
				{:else}
					Send Verification Code
				{/if}
			</button>

			<p class="auth-note">
				<svg class="info-icon" viewBox="0 0 20 20" fill="currentColor">
					<path
						fill-rule="evenodd"
						d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
						clip-rule="evenodd"
					/>
				</svg>
				We'll send you a 6-digit code to verify your email. No password needed.
			</p>
		</form>
	</div>
</div>

<style>
	.auth-container {
		width: 100%;
		max-width: 420px;
	}

	.auth-card {
		background: white;
		border-radius: var(--radius-2xl);
		box-shadow: var(--shadow-md3-3);
		padding: var(--spacing-8);
		text-align: center;
	}

	.logo-container {
		margin-bottom: var(--spacing-4);
	}

	.logo {
		width: 64px;
		height: 64px;
		margin: 0 auto;
	}

	.auth-title {
		font-size: var(--font-size-headline-minimum);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-900);
		margin: 0 0 var(--spacing-1) 0;
	}

	.auth-subtitle {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-500);
		margin: 0 0 var(--spacing-6) 0;
	}

	.auth-form {
		text-align: left;
	}

	.auth-instruction {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
		margin: 0 0 var(--spacing-4) 0;
	}

	.form-group {
		margin-bottom: var(--spacing-4);
	}

	.form-label {
		display: block;
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
		margin-bottom: var(--spacing-2);
	}

	.form-input {
		width: 100%;
		padding: var(--spacing-3) var(--spacing-4);
		font-size: var(--font-size-body-content);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		transition: all var(--transition-fast);
		box-sizing: border-box;
	}

	.form-input:focus {
		outline: none;
		border-color: var(--color-primary-500);
		box-shadow: 0 0 0 3px var(--color-primary-100);
	}

	.form-input:disabled {
		background: var(--color-surface-100);
		cursor: not-allowed;
	}

	.error-message {
		color: var(--color-error-500);
		font-size: var(--font-size-auxiliary-text);
		margin: 0 0 var(--spacing-4) 0;
	}

	.submit-btn {
		width: 100%;
		padding: var(--spacing-3) var(--spacing-6);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: white;
		background: var(--color-primary-500);
		border: none;
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-2);
	}

	.submit-btn:hover:not(:disabled) {
		background: var(--color-primary-600);
	}

	.submit-btn:disabled {
		background: var(--color-surface-400);
		cursor: not-allowed;
	}

	.spinner {
		width: 16px;
		height: 16px;
		border: 2px solid rgba(255, 255, 255, 0.3);
		border-top-color: white;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.auth-note {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-2);
		margin-top: var(--spacing-4);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
		line-height: 1.5;
	}

	.info-icon {
		width: 16px;
		height: 16px;
		flex-shrink: 0;
		margin-top: 2px;
	}

	@media (max-width: 480px) {
		.auth-card {
			padding: var(--spacing-6);
			border-radius: var(--radius-xl);
		}

		.auth-title {
			font-size: var(--font-size-title-large);
		}
	}
</style>

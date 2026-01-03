<script lang="ts">
	/**
	 * Employee Portal - OTP Verification Page (with Company Slug)
	 * Verify 6-digit code sent to email
	 *
	 * BUG FIX: Now scopes portal_status update to company_id to prevent
	 * updating records in other companies when email exists in multiple companies.
	 */
	import { onMount, onDestroy, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { supabase } from '$lib/api/supabase';
	import { PORTAL_COMPANY_CONTEXT_KEY, type PortalCompanyContext } from '$lib/types/employee-portal';

	const portalContext = getContext<PortalCompanyContext>(PORTAL_COMPANY_CONTEXT_KEY);
	const slug = $derived($page.params.slug);

	let email = $state('');
	let otpDigits = $state<string[]>(['', '', '', '', '', '']);
	let isVerifying = $state(false);
	let error = $state('');
	let resendCooldown = $state(60);
	let canResend = $state(false);

	let inputRefs = $state<HTMLInputElement[]>([]);
	let cooldownInterval: ReturnType<typeof setInterval> | null = null;

	onMount(() => {
		const emailParam = $page.url.searchParams.get('email');
		if (!emailParam) {
			goto(`/employee/${slug}/auth`);
			return;
		}
		email = emailParam;
		startResendCooldown();
		setTimeout(() => inputRefs[0]?.focus(), 100);
	});

	function startResendCooldown() {
		if (cooldownInterval) {
			clearInterval(cooldownInterval);
		}

		resendCooldown = 60;
		canResend = false;
		cooldownInterval = setInterval(() => {
			resendCooldown--;
			if (resendCooldown <= 0) {
				if (cooldownInterval) {
					clearInterval(cooldownInterval);
					cooldownInterval = null;
				}
				canResend = true;
			}
		}, 1000);
	}

	onDestroy(() => {
		if (cooldownInterval) {
			clearInterval(cooldownInterval);
			cooldownInterval = null;
		}
	});

	function handleInput(index: number, event: Event) {
		const input = event.target as HTMLInputElement;
		const value = input.value;

		if (!/^\d*$/.test(value)) {
			input.value = otpDigits[index];
			return;
		}

		if (value.length > 1) {
			const digits = value.slice(0, 6).split('');
			digits.forEach((digit, i) => {
				if (i < 6) otpDigits[i] = digit;
			});
			otpDigits = [...otpDigits];
			const lastIndex = Math.min(digits.length - 1, 5);
			inputRefs[lastIndex]?.focus();
			if (digits.length >= 6) {
				handleVerify();
			}
			return;
		}

		otpDigits[index] = value;
		otpDigits = [...otpDigits];

		if (value && index < 5) {
			inputRefs[index + 1]?.focus();
		}

		if (otpDigits.every((d) => d) && otpDigits.join('').length === 6) {
			handleVerify();
		}
	}

	function handleKeyDown(index: number, event: KeyboardEvent) {
		if (event.key === 'Backspace') {
			if (!otpDigits[index] && index > 0) {
				inputRefs[index - 1]?.focus();
			}
			otpDigits[index] = '';
			otpDigits = [...otpDigits];
		} else if (event.key === 'ArrowLeft' && index > 0) {
			inputRefs[index - 1]?.focus();
		} else if (event.key === 'ArrowRight' && index < 5) {
			inputRefs[index + 1]?.focus();
		}
	}

	async function handleVerify() {
		const otp = otpDigits.join('');
		if (otp.length !== 6 || isVerifying) return;

		isVerifying = true;
		error = '';

		// Listen for auth state change - use setTimeout to avoid Supabase deadlock
		// See: https://github.com/supabase/gotrue-js/issues/762
		const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
			if (event === 'SIGNED_IN' && session) {
				subscription.unsubscribe();
				// setTimeout breaks the synchronous chain to avoid deadlock
				setTimeout(() => {
					updatePortalStatus(session.user.email);
					goto(`/employee/${slug}`);
				}, 0);
			}
		});

		const { error: authError } = await supabase.auth.verifyOtp({
			email,
			token: otp,
			type: 'email'
		});

		if (authError) {
			subscription.unsubscribe();
			error = authError.message.includes('expired')
				? 'This code has expired. Please request a new one.'
				: authError.message.includes('invalid')
					? 'Invalid code. Please check and try again.'
					: authError.message;
			otpDigits = ['', '', '', '', '', ''];
			inputRefs[0]?.focus();
			isVerifying = false;
		}
	}

	function updatePortalStatus(userEmail?: string) {
		const companyId = portalContext?.company?.id;
		if (!userEmail || !companyId) return;

		// Fire and forget - don't block login
		void supabase
			.from('employees')
			.update({
				portal_status: 'active',
				portal_last_login_at: new Date().toISOString()
			})
			.eq('email', userEmail)
			.eq('company_id', companyId);
	}

	async function handleResend() {
		if (!canResend) return;

		try {
			const { error: authError } = await supabase.auth.signInWithOtp({
				email,
				options: {
					shouldCreateUser: false
				}
			});

			if (authError) {
				error = authError.message;
				return;
			}

			startResendCooldown();
			error = '';
			otpDigits = ['', '', '', '', '', ''];
			inputRefs[0]?.focus();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to resend code';
		}
	}

	function handleBackToEmail() {
		goto(`/employee/${slug}/auth`);
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

		<h1 class="verify-title">Enter Verification Code</h1>

		<p class="verify-subtitle">
			We've sent a 6-digit code to:
			<br />
			<strong>{email}</strong>
		</p>

		<!-- OTP Input -->
		<div class="otp-container">
			<span class="otp-label">Verification Code</span>
			<div class="otp-inputs">
				{#each otpDigits as digit, index}
					<input
						bind:this={inputRefs[index]}
						type="text"
						inputmode="numeric"
						maxlength="6"
						class="otp-input"
						class:has-value={digit}
						value={digit}
						disabled={isVerifying}
						oninput={(e) => handleInput(index, e)}
						onkeydown={(e) => handleKeyDown(index, e)}
						onfocus={(e) => (e.target as HTMLInputElement).select()}
					/>
				{/each}
			</div>
		</div>

		{#if error}
			<p class="error-message">{error}</p>
		{/if}

		<button class="verify-btn" onclick={handleVerify} disabled={isVerifying || otpDigits.some((d) => !d)}>
			{#if isVerifying}
				<span class="spinner"></span>
				Verifying...
			{:else}
				Verify
			{/if}
		</button>

		<p class="expires-note">Code expires in 10 minutes</p>

		<!-- Resend Section -->
		<div class="resend-section">
			{#if canResend}
				<button class="resend-btn" onclick={handleResend}>Resend Code</button>
			{:else}
				<span class="resend-cooldown">Resend available in {resendCooldown}s</span>
			{/if}
		</div>

		<!-- Back link -->
		<button class="back-link" onclick={handleBackToEmail}>
			<svg class="back-icon" viewBox="0 0 20 20" fill="currentColor">
				<path
					fill-rule="evenodd"
					d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z"
					clip-rule="evenodd"
				/>
			</svg>
			Use a different email
		</button>
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
		margin-bottom: var(--spacing-4);
	}

	.logo {
		width: 64px;
		height: 64px;
		margin: 0 auto;
	}

	.verify-title {
		font-size: var(--font-size-headline-minimum);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-900);
		margin: 0 0 var(--spacing-3) 0;
	}

	.verify-subtitle {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0 0 var(--spacing-6) 0;
		line-height: 1.5;
	}

	.verify-subtitle strong {
		color: var(--color-surface-900);
	}

	.otp-container {
		margin-bottom: var(--spacing-4);
	}

	.otp-label {
		display: block;
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
		margin-bottom: var(--spacing-3);
	}

	.otp-inputs {
		display: flex;
		justify-content: center;
		gap: var(--spacing-2);
	}

	.otp-input {
		width: 48px;
		height: 56px;
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-semibold);
		text-align: center;
		border: 2px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		transition: all var(--transition-fast);
		background: white;
	}

	.otp-input:focus {
		outline: none;
		border-color: var(--color-primary-500);
		box-shadow: 0 0 0 3px var(--color-primary-100);
	}

	.otp-input.has-value {
		border-color: var(--color-primary-400);
		background: var(--color-primary-50);
	}

	.otp-input:disabled {
		background: var(--color-surface-100);
		cursor: not-allowed;
	}

	.error-message {
		color: var(--color-error-500);
		font-size: var(--font-size-auxiliary-text);
		margin: 0 0 var(--spacing-4) 0;
	}

	.verify-btn {
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

	.verify-btn:hover:not(:disabled) {
		background: var(--color-primary-600);
	}

	.verify-btn:disabled {
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

	.expires-note {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
		margin: var(--spacing-3) 0 var(--spacing-4) 0;
	}

	.resend-section {
		padding: var(--spacing-4) 0;
		border-top: 1px solid var(--color-surface-200);
	}

	.resend-btn {
		background: none;
		border: none;
		color: var(--color-primary-500);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		text-decoration: underline;
	}

	.resend-btn:hover {
		color: var(--color-primary-600);
	}

	.resend-cooldown {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.back-link {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		background: none;
		border: none;
		color: var(--color-surface-600);
		font-size: var(--font-size-auxiliary-text);
		cursor: pointer;
		margin-top: var(--spacing-4);
	}

	.back-link:hover {
		color: var(--color-primary-500);
	}

	.back-icon {
		width: 16px;
		height: 16px;
	}

	@media (max-width: 480px) {
		.verify-card {
			padding: var(--spacing-6);
			border-radius: var(--radius-xl);
		}

		.verify-title {
			font-size: var(--font-size-title-large);
		}

		.otp-input {
			width: 42px;
			height: 50px;
			font-size: var(--font-size-body-content);
		}
	}
</style>

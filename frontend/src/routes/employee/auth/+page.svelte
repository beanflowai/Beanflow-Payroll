<script lang="ts">
	/**
	 * Employee Portal - Login Page
	 * Magic link authentication - enter email to receive login link
	 */
	let email = $state('');
	let isSubmitting = $state(false);
	let showEmailSent = $state(false);
	let error = $state('');

	// Mock company info
	const companyName = 'Acme Corporation';

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

		// Simulate API call
		await new Promise((resolve) => setTimeout(resolve, 1000));

		isSubmitting = false;
		showEmailSent = true;
	}

	function isValidEmail(email: string): boolean {
		return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
	}

	function handleResend() {
		showEmailSent = false;
		// Reset for demo purposes
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

		<h1 class="auth-title">Employee Portal</h1>
		<p class="company-name">{companyName}</p>

		{#if !showEmailSent}
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
						Send Login Link
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
					We'll send you a secure link to access your portal. No password needed.
				</p>
			</form>
		{:else}
			<!-- Email Sent Confirmation -->
			<div class="email-sent">
				<div class="check-icon-container">
					<svg class="check-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M5 13l4 4L19 7"
						/>
					</svg>
				</div>

				<h2 class="email-sent-title">Check Your Email</h2>

				<p class="email-sent-text">
					We've sent a login link to:
					<br />
					<strong>{email}</strong>
				</p>

				<p class="email-sent-info">
					Click the link in the email to access your portal.
					<br />
					The link will expire in 15 minutes.
				</p>

				<div class="divider"></div>

				<div class="help-section">
					<p class="help-title">Didn't receive the email?</p>
					<ul class="help-list">
						<li>Check your spam folder</li>
						<li>
							<button class="resend-btn" onclick={handleResend}>Resend Link</button>
							<span class="resend-note">(available after 60 seconds)</span>
						</li>
					</ul>
				</div>
			</div>
		{/if}
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

	.company-name {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
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

	/* Email Sent State */
	.email-sent {
		text-align: center;
	}

	.check-icon-container {
		width: 64px;
		height: 64px;
		margin: 0 auto var(--spacing-4);
		background: var(--color-success-100);
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.check-icon {
		width: 32px;
		height: 32px;
		color: var(--color-success-600);
	}

	.email-sent-title {
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-900);
		margin: 0 0 var(--spacing-4) 0;
	}

	.email-sent-text {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
		margin: 0 0 var(--spacing-3) 0;
		line-height: 1.6;
	}

	.email-sent-text strong {
		color: var(--color-surface-900);
	}

	.email-sent-info {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
		margin: 0 0 var(--spacing-6) 0;
		line-height: 1.6;
	}

	.divider {
		height: 1px;
		background: var(--color-surface-200);
		margin: var(--spacing-6) 0;
	}

	.help-section {
		text-align: left;
	}

	.help-title {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
		margin: 0 0 var(--spacing-2) 0;
	}

	.help-list {
		margin: 0;
		padding-left: var(--spacing-5);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	.help-list li {
		margin-bottom: var(--spacing-2);
	}

	.resend-btn {
		background: none;
		border: none;
		color: var(--color-primary-500);
		font-size: var(--font-size-auxiliary-text);
		cursor: pointer;
		padding: 0;
		text-decoration: underline;
	}

	.resend-btn:hover {
		color: var(--color-primary-600);
	}

	.resend-note {
		font-size: var(--font-size-caption-text);
		color: var(--color-surface-500);
	}

	/* Mobile adjustments */
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

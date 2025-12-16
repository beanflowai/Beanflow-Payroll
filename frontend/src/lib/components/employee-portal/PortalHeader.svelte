<script lang="ts">
	/**
	 * PortalHeader - Employee Portal Header Component
	 * Displays logo, company name, employee name, and sign out button
	 */

	interface Props {
		companyName?: string;
		employeeName?: string;
		onSignOut?: () => void;
	}

	let { companyName = 'Acme Corporation', employeeName = 'Sarah Johnson', onSignOut }: Props =
		$props();

	function handleSignOut() {
		onSignOut?.();
	}
</script>

<header class="portal-header">
	<div class="header-left">
		<div class="logo-container">
			<svg class="logo" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
				<rect width="32" height="32" rx="8" fill="var(--color-primary-500)" />
				<path
					d="M8 16C8 11.5817 11.5817 8 16 8C20.4183 8 24 11.5817 24 16C24 20.4183 20.4183 24 16 24"
					stroke="white"
					stroke-width="2.5"
					stroke-linecap="round"
				/>
				<circle cx="16" cy="16" r="3" fill="white" />
			</svg>
		</div>
		<div class="header-text">
			<span class="portal-title">Employee Portal</span>
			<span class="company-name">{companyName}</span>
		</div>
	</div>

	<div class="header-right">
		<span class="employee-name">{employeeName}</span>
		<button class="sign-out-btn" onclick={handleSignOut}>Sign Out</button>
	</div>
</header>

<style>
	.portal-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--spacing-4) var(--spacing-6);
		background: white;
		border-bottom: 1px solid var(--color-surface-200);
		height: 64px;
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
	}

	.logo-container {
		width: 40px;
		height: 40px;
		flex-shrink: 0;
	}

	.logo {
		width: 100%;
		height: 100%;
	}

	.header-text {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.portal-title {
		font-size: var(--font-size-title-small);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-900);
		line-height: 1.2;
	}

	.company-name {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
		line-height: 1.2;
	}

	.header-right {
		display: flex;
		align-items: center;
		gap: var(--spacing-4);
	}

	.employee-name {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
	}

	.sign-out-btn {
		padding: var(--spacing-2) var(--spacing-4);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		background: transparent;
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.sign-out-btn:hover {
		background: var(--color-surface-100);
		border-color: var(--color-surface-400);
		color: var(--color-surface-800);
	}

	/* Mobile responsive */
	@media (max-width: 640px) {
		.portal-header {
			padding: var(--spacing-3) var(--spacing-4);
		}

		.company-name {
			display: none;
		}

		.employee-name {
			display: none;
		}
	}
</style>
